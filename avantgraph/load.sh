#!/usr/bin/env bash

set -eu
set -o pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

. avantgraph/vars.sh
. scripts/import-vars.sh

CSV_DIR="${IMPORT_DATA_DIR_PROJECTED_FK}"
if [ ! -d "${CSV_DIR}" ]; then
    echo "ERROR: Dataset not found: ${CSV_DIR}"
    exit 1
fi

export PATH="${AG_BIN}:${PATH}"

# Create schema (topology only, no edge properties).
export STANDARD_EDGE_PROPS=""
bash avantgraph/create-schema.sh "${AG_GRAPH_DIR}"

# Read CSVs with DuckDB, emit sorted nodes/fwd/bwd JSON, load into AvantGraph.
python3 avantgraph/load.py \
    "${CSV_DIR}" \
    "${AG_GRAPH_DIR}" \
    --ag-bin "${AG_BIN}"
