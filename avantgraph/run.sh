#!/usr/bin/env bash

set -eu
set -o pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

. avantgraph/vars.sh
. scripts/import-vars.sh

NUM_THREADS=${1:-$(nproc)}

AVANTGRAPH="${AG_BIN}/avantgraph"
RESULTS_FILE="results/results.csv"
mkdir -p results

# q7-q9 use OPTIONAL MATCH / anti-joins which are not yet supported
for i in $(seq 1 6); do
    QUERY_FILE="cypher/q${i}.cypher"
    if [ ! -f "${QUERY_FILE}" ]; then
        echo "WARNING: Query file not found: ${QUERY_FILE}" >&2
        continue
    fi

    echo "Query ${i}"

    START=$(date +%s%N)
    OUTPUT=$("${AVANTGRAPH}" \
        --query-type=cypher \
        --read-only \
        "${AG_GRAPH_DIR}" \
        "${QUERY_FILE}" 2>/dev/null) || true
    END=$(date +%s%N)

    DURATION=$(awk "BEGIN { printf \"%.4f\", (${END} - ${START}) / 1000000000 }")

    # Extract the count from output like: "tuple:  %count=int:8773828"
    RESULT=$(echo "${OUTPUT}" | grep -oP '(?<=%count=int:)\d+' | head -1)
    if [ -z "${RESULT}" ]; then
        RESULT="N/A"
    fi

    printf "AvantGraph\t${NUM_THREADS} threads\t${SF}\t${i}\t${DURATION}\t${RESULT}\n" >> "${RESULTS_FILE}"
done
