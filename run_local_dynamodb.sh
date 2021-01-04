#!/bin/bash
set -euxo pipefail

docker run -d -p 8000:8000 amazon/dynamodb-local
