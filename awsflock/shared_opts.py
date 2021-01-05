import platform

import click

from awsflock.parsing import Duration

DEFAULT_DYNAMO_TABLE = "awsflock"


def lease_duration_opt(func):
    return click.option(
        "--lease-duration",
        type=Duration(),
        default="2 hours",
        show_default=True,
        help=(
            "The duration of the lease, after which it expires if not released. "
            "Given as an integer and a duration unit. Valid durations are "
            "seconds, minutes, hours, and days. "
            "Defaults to seconds if no unit is given"
        ),
    )(func)


def help_opt(func):
    return click.help_option("-h", "--help")(func)


def table_opt(func):
    return click.option(
        "--tablename",
        envvar="AWSFLOCK_TABLE",
        default=DEFAULT_DYNAMO_TABLE,
        show_default=True,
        help=(
            "A custom name for the lock table to use. "
            "Can be set with the AWSFLOCK_TABLE env var"
        ),
    )(func)


def owner_opt(func):
    def callback(ctx, param, value):
        # if no owner is given, default to hostname of the current machine
        # failover to NULL in the worst case
        if not value:
            return platform.node() or "NULL"
        return value

    return click.option(
        "--owner",
        help=(
            "The name of the lock owner. Defaults to using the hostname from the "
            "calling environment. Informational only, no impact on lock logic"
        ),
        callback=callback,
    )(func)
