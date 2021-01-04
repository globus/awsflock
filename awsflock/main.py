#!/usr/bin/env python3
import click

from awsflock.common import help_opt
from awsflock.create_table import create_table
from awsflock.acquire import acquire_lock
from awsflock.release import release_lock
from awsflock.renew import renew_lock


@click.group("awsflock", no_args_is_help=True)
@help_opt
def main():
    """
    Commands for managing DynamoDB Locks. See `--help` on subcommands for usage details.

    The locking protocol is based around lock IDs (arbitrary strings) which can be
    acquired for limited durations (leases). A lease has a duration and ID. When you
    acquire a lock, you get a new lease ID, which can then be used to release the lock.

    Leases eventually expire. DynamoDB itself may clean up expired locks, but clients are
    also allowed to reclaim locks which are expired but haven't been cleaned up yet. Lock
    waiting does not abort early if a lock has a lease duration longer than the wait time,
    as the lock may be explicitly released.
    """


main.add_command(create_table)
main.add_command(acquire_lock)
main.add_command(release_lock)
main.add_command(renew_lock)


if __name__ == "__main__":
    main()