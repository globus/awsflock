import os
import shlex
import uuid

import pytest
from click.testing import CliRunner

from awsflock import cli
from awsflock.common import get_dynamo_client

_tablename = f"awsflock-{uuid.uuid4().hex}"
os.environ["AWSFLOCK_TABLE"] = _tablename

if not os.getenv("DYANMO_ENDPOINT_URL"):
    os.environ["DYNAMO_ENDPOINT_URL"] = "http://localhost:8000"

# tests run with the default region and dummy credentials set
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_ACCESS_KEY_ID"] = "fooAccessKey"
os.environ["AWS_SECRET_ACCESS_KEY"] = "fooSecretKey"


@pytest.fixture(scope="session")
def tablename():
    return _tablename


@pytest.fixture
def run_cmd():
    def func(line, assert_exit_code=0):
        args = shlex.split(line)
        assert args[0] == "awsflock"

        result = CliRunner().invoke(
            cli, args[1:], catch_exceptions=bool(assert_exit_code)
        )
        if result.exit_code != assert_exit_code:
            raise Exception(
                f"Failed to run '{line}'.\n"
                f"result.exit_code={result.exit_code} (expected {assert_exit_code})\n"
                f"Output:\n{result.output}"
            )
        return result

    return func


@pytest.fixture
def with_table(tablename, run_cmd):
    result = run_cmd("awsflock create-table")
    assert result.exit_code == 0

    yield

    client = get_dynamo_client()
    client.delete_table(TableName=tablename)
