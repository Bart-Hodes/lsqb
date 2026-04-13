#!/usr/bin/env bash

set -eu
set -o pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

. avantgraph/vars.sh

# Skip loading if graph already exists and looks healthy
if [ -f "${AG_GRAPH_DIR}/main" ]; then
    echo "Graph already exists at ${AG_GRAPH_DIR}"
    echo "Verifying schema..."
    TABLES=$("${AG_BIN}/ag-schema" list-vertex-tables "${AG_GRAPH_DIR}" --graph= 2>&1)
    N_TABLES=$(echo "${TABLES}" | grep -c "^VT ")
    if [ "${N_TABLES}" -ge 11 ]; then
        echo "  ${N_TABLES} vertex tables found — OK"
        echo "${TABLES}"
        echo "Skipping reload."
        exit 0
    else
        echo "  Only ${N_TABLES} vertex tables found (expected 11) — reloading."
    fi
fi

avantgraph/pre-load.sh
avantgraph/load.sh
avantgraph/post-load.sh
