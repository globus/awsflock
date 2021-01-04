#!/usr/bin/en python3
import time

import click

from awsflock.common import help_opt, pass_dynamo_client, table_opt


def _wait_for_table_active(client, tablename):
    status = "UNKNOWN"
    attempt = 0
    while status != "ACTIVE" and attempt < 20:
        attempt += 1
        click.echo(".", nl=False)
        try:
            r = client.describe_table(TableName=tablename)
        except client.exceptions.ResourceNotFoundException:
            continue
        status = r["Table"]["TableStatus"]
        time.sleep(1)
    if status != "ACTIVE":
        click.echo("TIMEOUT!")
        click.get_current_context().exit(1)
    click.echo("OK")


@click.command("create-table")
@help_opt
@table_opt
@pass_dynamo_client
def create_table(client, tablename):
    """
    Create a new table for managing dynamodb locks.

    \b
    Permissions required:
      dynamodb:CreateTable
      dynamodb:UpdateTimeToLive
      dynamodb:DescribeTable
    """
    # create the table; NOTES:
    # 1. We could make the billing mode configurable in the future if there are
    #    high-throughput use-cases. We use default billing options which should
    #    fit within the free usage tier (assuming no other dynamo usage)
    # 2. We could introduce optional sort_keys if we find a use-case with many, many
    #    locks in which being able to quickly find the right lock is important/useful.
    client.create_table(
        TableName=tablename,
        KeySchema=[{"AttributeName": "lock_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "lock_id", "AttributeType": "S"}],
        BillingMode="PROVISIONED",
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )
    click.echo(
        f"'{tablename}' create in progress. Waiting for active status..", nl=False
    )
    _wait_for_table_active(client, tablename)
    client.update_time_to_live(
        TableName=tablename,
        TimeToLiveSpecification={"Enabled": True, "AttributeName": "expiration_time"},
    )
    click.echo(
        f"Setting TTL config on '{tablename}'. Waiting for active status..", nl=False
    )
    _wait_for_table_active(client, tablename)
