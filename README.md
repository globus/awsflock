# AWS flock

`flock`-like functionality for applications in AWS, using dynamodb as a
backend for synchronization.

A CLI tool as simple as the classic `flock` command.

## Use Cases

- Synchronizing multiple automated jobs across workers in AWS
- Writing scripts that only one human operator can be running at a time (e.g.
  production deployment tools with terraform, CFN, etc)
- Synchronizing jobs in non-AWS systems (e.g. GitHub Actions) using AWS
  credentials

## Usage

Full usage info can be found with

```bash
awsflock --help
```

Create the table in DynamoDB in order to start using `awsflock`:

```bash
awsflock table-create
```

Acquire a lock, with a 15 minute expiration, and get the lock `LEASE_ID`:

```bash
LEASE_ID="$(awsflock acquire LockFoo --lease-duration '15 minutes')"
```

Renew the lock, getting back the new `LEASE_ID` and reducing the expiration
window to 5 minutes, specified in seconds:

```bash
LEASE_ID="$(awsflock renew LockFoo "$LEASE_ID" --lease-duration '300s')"
```

Release the lock, so that others may use it:

```bash
awsflock release LockFoo "$LEASE_ID"
```

Attempt to acquire another lock, but don't block and wait for it to be
acquired:

```bash
LEASE_ID="$(awsflock acquire LockBar --no-wait)"
if [ $? -eq 0 ]; then
  # lock acquired ...
else
  # lock not acquired ...
fi
```

## Behavior / Model

Locks are held for a limited period of time.
After that time, if not renewed, the lock expires and another worker may reclaim
the lock.
While the lock is held, the worker holding it has a "lease" on the lock, proven
by a given `LEASE_ID`.
A `LEASE_ID` can be used to "renew" or "release" a given lock.

`awsflock` requires a table in DynamoDB to store active locks.
By default, the table name is `awsflock`, but custom names can be used.
You must create the table before locks can be used (it will never be created
automatically).
Locks are identified by name, and those names are unique keys into the
`awsflock` table.

Locks have a limited lifetime (default: 2 hours) if not explicitly released,
after which they may be "reclaimed" by anyone trying to acquire that lock.

> **NOTE:**
> Local clock time is compared against lock expirations to determine whether
> or not reclamation may be tried. The default reclamation window (5 seconds)
> is more than sufficient for most use-cases, but assumes that your clocks
> are synchronized by NTP or a similar protocol. Usage where clocks cannot be
> trusted may result in incorrect lock reclamations.

When you acquire a lock, you get back a `LEASE_ID`. The `LEASE_ID` can then be
used to renew the lock or release it. In this way, locks are held by a single
owner for a limited period of time, and the `LEASE_ID` constitutes proof of
ownership.

## CHANGELOG

### 0.2.0

* More advanced parsing of durations

### 0.1.1

* Minor fixup

### 0.1.0

* Initial release
