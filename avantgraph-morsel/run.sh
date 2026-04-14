#!/usr/bin/env bash
set -euo pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

# Load environment
. avantgraph/vars.sh
. scripts/import-vars.sh

NUM_THREADS=${1:-$(nproc)}

AVANTGRAPH="${AG_BIN}/avantgraph"
RESULTS_FILE="results/results.csv"
mkdir -p results

TIMEOUT_SEC=30

echo "query,threads,sf,duration_s,result,status" > "${RESULTS_FILE}"

for i in $(seq 1 6); do
    QUERY_FILE="cypher/q${i}.cypher"

    if [[ ! -f "${QUERY_FILE}" ]]; then
        echo "WARNING: missing ${QUERY_FILE}" >&2
        continue
    fi

    echo "Running query ${i}"

    RAW=$(mktemp)

    START=$(date +%s%N)

    # Run with timeout and capture everything safely
    timeout --kill-after=5 "${TIMEOUT_SEC}" \
        "${AVANTGRAPH}" \
        --query-type=cypher \
        --enable-morsel-pipelines \
        "${AG_GRAPH_DIR}" \
        "${QUERY_FILE}" \
        > "${RAW}" 2>&1

    RC=$?

    END=$(date +%s%N)

    DURATION=$(awk "BEGIN { printf \"%.6f\", (${END} - ${START}) / 1e9 }")

    # Status handling
    if [[ $RC -eq 124 ]]; then
        STATUS="TIMEOUT"
    elif [[ $RC -ne 0 ]]; then
        STATUS="FAIL"
    else
        STATUS="OK"
    fi

    # Extract result safely
    RESULT=$(grep -oP '(?<=%count=int:)\d+' "${RAW}" | head -1 || true)
    RESULT=${RESULT:-N/A}

    echo "${i},${NUM_THREADS},${SF},${DURATION},${RESULT},${STATUS}" \
        >> "${RESULTS_FILE}"

    rm -f "${RAW}"
done

echo "Done. Results written to ${RESULTS_FILE}"
