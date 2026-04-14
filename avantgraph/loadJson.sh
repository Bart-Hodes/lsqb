#!/usr/bin/env bash

set -eu
set -o pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

. avantgraph/vars.sh

export PATH="${AG_BIN}:${PATH}"

NODES_JSON="${AG_GRAPH_DIR}/nodes.json"
EDGES_FWD_JSON="${AG_GRAPH_DIR}/edges_fwd.json"
EDGES_BWD_JSON="${AG_GRAPH_DIR}/edges_bwd.json"

for f in "${NODES_JSON}" "${EDGES_FWD_JSON}" "${EDGES_BWD_JSON}"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: $f not found. Run sortJson.sh first."
        exit 1
    fi
done

echo "Loading vertices..."
"${AG_BIN}/ag-load-graph" --graph-format=json "${NODES_JSON}" "${AG_GRAPH_DIR}"

echo "Loading forward edges (sorted by src)..."
"${AG_BIN}/ag-load-graph" --graph-format=json --load-direction=forwards "${EDGES_FWD_JSON}" "${AG_GRAPH_DIR}"

echo "Loading backward edges (sorted by trg)..."
"${AG_BIN}/ag-load-graph" --graph-format=json --load-direction=backwards "${EDGES_BWD_JSON}" "${AG_GRAPH_DIR}"

echo "Done loading."
