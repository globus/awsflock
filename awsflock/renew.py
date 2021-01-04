#!/usr/bin/env python3
import time

import click

from awsflock.common import (
    gen_lease_id,
    help_opt,
    owner_opt,
    pass_dynamo_client,
    reclaim_lock,
    table_opt,
)


@click.command("renew")
@help_opt
@click.argument("LOCK_ID")
@click.argument("LEASE_ID")
@table_opt
@click.option(
    "--lease-duration",
    type=int,
    default=7200,
    show_default=True,
    help="The duration of the lease in seconds, after which it expires if not released",
)
@owner_opt
@pass_dynamo_client
def renew_lock(client, lock_id, lease_id, tablename, lease_duration, owner):
    """
    Renew a DynamoDB Lock. Exit codes are used to signal success or failure.

    \b
    Exit 0 if the lock is renewed.
    Exit 3 if renewal fails because the lock no longer exists or another agent
    reclaimed it already.
    Any other exit code indicates an error.

    Outputs the LEASE_ID associated with the current agent/usage.

    \b
    Permissions required:
      dynamodb:PutItem
      dynamodb:GetItem
    """
    # renewal is just reclaiming a lock without any preflight checks
    # (acquisition reclamation checks expiration time before trying to reclaim)
    new_lease_id = gen_lease_id()
    new_lock_item = {
        "lock_id": {"S": lock_id},
        "lease_id": {"S": new_lease_id},
        "lease_duration": {"N": str(lease_duration)},
        "owner": {"S": owner},
        "expiration_time": {"N": str(int(time.time() + lease_duration))},
    }
    reclaim_success = reclaim_lock(client, tablename, new_lock_item, lease_id)

    # if we reclaimed a lock, succeed and exit, otherwise fallthrough
    if reclaim_success:
        click.echo(new_lease_id)
        click.get_current_context().exit(0)
    # reclaim failed
    click.get_current_context().exit(3)
