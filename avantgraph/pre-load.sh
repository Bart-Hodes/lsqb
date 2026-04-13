#!/usr/bin/env bash

set -eu
set -o pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

. avantgraph/vars.sh
. scripts/import-vars.sh

rm -rf "${AG_GRAPH_DIR}"
mkdir -p "${AG_GRAPH_DIR}"
