#!/usr/bin/env python3
import time

import botocore
import click

from awsflock.common import gen_lease_id, get_lock, pass_dynamo_client, reclaim_lock
from awsflock.shared_opts import help_opt, lease_duration_opt, owner_opt, table_opt


def vecho(message, verbose):
    if verbose:
        click.echo(message, err=True, color="yellow")


def create_lock(client, tablename, lock_item):
    # create a lock while asserting that it must not already exist
    # if it does exist, return False
    # otherwise, return True
    try:
        client.put_item(
            TableName=tablename,
            Item=lock_item,
            ConditionExpression="NOT(attribute_exists(#pk))",
            ExpressionAttributeNames={"#pk": "lock_id"},
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


@click.command("acquire")
@click.argument("LOCK_ID")
@click.option("--verbose", is_flag=True, help="Enable verbose output to stderr")
@click.option(
    "--wait-time",
    default=60,
    show_default=True,
    type=int,
    help=(
        "A number of seconds to wait for the lock to be available. "
        "0 means wait indefinitely"
    ),
)
@click.option(
    "--no-wait", is_flag=True, help="Exit immediately if the lock cannot be acquired"
)
@help_opt
@table_opt
@lease_duration_opt
@owner_opt
@pass_dynamo_client
def acquire_lock(
    client, lock_id, tablename, verbose, lease_duration, wait_time, no_wait, owner
):
    """
    Acquire a DynamoDB Lock. Exit codes are used to signal success or failure.

    \b
    Exit 0 if the lock is acquired.
    Exit 3 if the lock is being held by another agent.
    Any other exit code indicates an error.

    Outputs the LEASE_ID associated with the current agent/usage.

    \b
    Permissions required:
      dynamodb:PutItem
      dynamodb:GetItem
    """
    vecho("params:", verbose)
    for x in (
        "lock_id",
        "tablename",
        "verbose",
        "lease_duration",
        "wait_time",
        "no_wait",
        "owner",
    ):
        vecho(f"  {x}={locals()[x]}", verbose)

    lease_id = gen_lease_id()
    new_lock_item = {
        "lock_id": {"S": lock_id},
        "lease_id": {"S": lease_id},
        "lease_duration": {"N": str(lease_duration.seconds)},
        "owner": {"S": owner},
        "expiration_time": {"N": str(int(time.time() + lease_duration.seconds))},
    }
    waited_seconds = 0
    wait_duration = 1
    while waited_seconds <= wait_time or wait_time == 0:
        vecho("trying to get lock...", verbose)
        existing_lock = get_lock(client, tablename, lock_id)
        if not existing_lock:
            vecho(
                "did not see an instance of this lock; will try to create it", verbose
            )
            acquired_success = create_lock(client, tablename, new_lock_item)
            if acquired_success:
                vecho("successfully acquired the lock (mode=create)", verbose)
                click.echo(lease_id)
                click.get_current_context().exit(0)
            # otherwise, someone else acquired the lock (fallthrough and continue after
            # sleep)
        else:
            vecho("saw an existing lock, will check for reclamation", verbose)
            # get the time at which the lock may have expired, and the lease_id
            existing_lock_expiration_time = int(existing_lock["expiration_time"]["N"])
            existing_lock_lease_id = existing_lock.get("lease_id")["S"]
            vecho(
                f"existing lock has a lease '{existing_lock_lease_id}' with "
                f"expiration time '{existing_lock_expiration_time}'",
                verbose,
            )

            # if the lock is expired by more than 5 seconds, try to reclaim
            if time.time() - existing_lock_expiration_time > 5:
                vecho("existing lock is expired, try to reclaim", verbose)
                reclaim_success = reclaim_lock(
                    client, tablename, new_lock_item, existing_lock_lease_id
                )
                # if we reclaimed a lock, succeed and exit, otherwise fallthrough and
                # continue after sleep
                if reclaim_success:
                    vecho("successfully acquired the lock (mode=reclaim)", verbose)
                    click.echo(lease_id)
                    click.get_current_context().exit(0)

        if no_wait:
            click.get_current_context().exit(3)

        # sleep each iteration, and increment timer
        # conditionally wait -- if we have a limited duration for waiting, stop
        # waiting at the very end
        if waited_seconds < wait_time or wait_time == 0:
            vecho(f"did not acquire the lock, wait {wait_duration} seconds", verbose)
            # durations use exponential backoff with a cap at 5m waiting periods
            time.sleep(wait_duration)
            waited_seconds += wait_duration
            wait_duration *= 2
            if wait_duration > 300:
                wait_duration = 300

    click.get_current_context().exit(3)
