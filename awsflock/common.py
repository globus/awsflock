import platform
import uuid

import botocore
import click

DEFAULT_DYNAMO_TABLE = "awsflock"


def gen_lease_id():
    return str(uuid.uuid4())


def help_opt(func):
    return click.help_option("-h", "--help")(func)


def table_opt(func):
    return click.option(
        "--tablename",
        default=DEFAULT_DYNAMO_TABLE,
        show_default=True,
        help="A custom name for the lock table to use",
    )(func)


def owner_opt(func):
    def callback(ctx, param, value):
        # if no owner is given, default to hostname of the current machine
        # failover to NULL in the worst case
        if not value:
            value = platform.node() or "NULL"
        return value

    return click.option(
        "--owner",
        help=(
            "The name of the lock owner. Defaults to using the hostname from the "
            "calling environment. Informational only, no impact on lock logic"
        ),
    )(func)


def reclaim_lock(client, tablename, lock_item, existing_lock_lease_id):
    # overwrite a lock while asserting that the lease ID cannot change (meaning that
    # only one client can possibly succeed in reclaiming)
    # if it does exist, return False
    # otherwise, return True
    try:
        client.put_item(
            TableName=tablename,
            Item=lock_item,
            ConditionExpression=(
                "attribute_exists(#lock_id) AND #lease_id = :existing_lease_id"
            ),
            ExpressionAttributeNames={"#lock_id": "lock_id", "#lease_id": "lease_id"},
            ExpressionAttributeValues={
                ":existing_lease_id": {"S": existing_lock_lease_id}
            },
        )
    except botocore.exceptions.ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise
    return True


def get_lock(client, table, lock_id):
    raw_lock = client.get_item(
        TableName=table, Key={"lock_id": {"S": lock_id}}, ConsistentRead=True
    )
    if "Item" not in raw_lock:
        return None
    return raw_lock["Item"]