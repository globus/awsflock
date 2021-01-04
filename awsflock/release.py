#!/usr/bin/env python3
import botocore
import click

from awsflock.common import help_opt, pass_dynamo_client, table_opt


@click.command("release")
@help_opt
@table_opt
@click.argument("LOCK_ID")
@click.argument("LEASE_ID")
@pass_dynamo_client
def release_lock(client, tablename, lock_id, lease_id):
    """
    Release a DynamoDB Lock. Exit codes are used to signal success or failure.

    \b
    Exit 0 if the lock is released.
    Exit 3 if the lock is no longer held and therefore cannot be released.
    Any other exit code indicates an error.

    \b
    Permissions required:
      dynamodb:DeleteItem
    """
    # delete a lock while asserting that the lease ID cannot change (meaning that
    # if it is reclaimed by another client, we cannot "release" it)
    try:
        client.delete_item(
            TableName=tablename,
            Key={"lock_id": {"S": lock_id}},
            ConditionExpression=(
                "attribute_exists(#lock_id) AND #lease_id = :existing_lease_id"
            ),
            ExpressionAttributeNames={"#lock_id": "lock_id", "#lease_id": "lease_id"},
            ExpressionAttributeValues={":existing_lease_id": {"S": lease_id}},
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            click.get_current_context().exit(3)
        raise
    click.get_current_context().exit(0)
