#!/usr/bin/env bash

set -eu
set -o pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

. avantgraph/vars.sh

MERGED_JSON="${AG_GRAPH_DIR}/merged.json"
if [ ! -f "${MERGED_JSON}" ]; then
    echo "ERROR: merged.json not found: ${MERGED_JSON}"
    echo "Run mergeCsvToJson.sh first."
    exit 1
fi

NODES_JSON="${AG_GRAPH_DIR}/nodes.json"
EDGES_FWD_JSON="${AG_GRAPH_DIR}/edges_fwd.json"
EDGES_BWD_JSON="${AG_GRAPH_DIR}/edges_bwd.json"

SORT_TMP="${AG_GRAPH_DIR}/sort_tmp"
mkdir -p "${SORT_TMP}"

SORT_OPTS=(-T "${SORT_TMP}" -t $'\t' -k1,1n --parallel="$(nproc)" --buffer-size=80%)

SRC_TMP="${AG_GRAPH_DIR}/_edges_by_src.tmp"
TRG_TMP="${AG_GRAPH_DIR}/_edges_by_trg.tmp"

echo "Splitting nodes/edges (single pass)..."
awk -F'"' '
    /"type":"node"/ {
        print > nodes
        next
    }
    /"type":"relationship"/ {
        # The JSON template has "start": {"id": "<N>", ... "end": {"id": "<N>"
        # Walk the fields to find start.id and end.id values.
        src = ""; trg = ""
        for (i = 1; i <= NF; i++) {
            if ($(i) == "start") {
                # pattern: ..."start": {"id": "<VALUE>", ...
                # field after "start" is }: {, then "id", then ": ", then the value
                for (j = i+1; j <= NF; j++) {
                    if ($(j) == "id") { src = $(j+2); break }
                }
            }
            if ($(i) == "end") {
                for (j = i+1; j <= NF; j++) {
                    if ($(j) == "id") { trg = $(j+2); break }
                }
            }
        }
        print src "\t" $0 > src_tmp
        print trg "\t" $0 > trg_tmp
    }
' nodes="${NODES_JSON}" src_tmp="${SRC_TMP}" trg_tmp="${TRG_TMP}" "${MERGED_JSON}"

echo "Sorting edges by src..."
sort "${SORT_OPTS[@]}" "${SRC_TMP}" | cut -f2- > "${EDGES_FWD_JSON}"
rm -f "${SRC_TMP}"

echo "Sorting edges by trg..."
sort "${SORT_OPTS[@]}" "${TRG_TMP}" | cut -f2- > "${EDGES_BWD_JSON}"
rm -f "${TRG_TMP}"

rm -rf "${SORT_TMP}"

echo "Done: ${NODES_JSON}, ${EDGES_FWD_JSON}, ${EDGES_BWD_JSON}"
