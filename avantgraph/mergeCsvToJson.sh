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

# Create schema
export PATH="${AG_BIN}:${PATH}"
export STANDARD_EDGE_PROPS=""
bash avantgraph/create-schema.sh "${AG_GRAPH_DIR}"

MERGED_JSON="${AG_GRAPH_DIR}/merged.json"

echo "Materializing JSON..."
bash avantgraph/import.sh "${CSV_DIR}" > "${MERGED_JSON}"
echo "Done: ${MERGED_JSON}"
