#!/usr/bin/env bash

set -eu
set -o pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

. kuzu/vars.sh
. scripts/import-vars.sh

rm -rf ${KUZU_DATA_DIR}/lsqb-database
