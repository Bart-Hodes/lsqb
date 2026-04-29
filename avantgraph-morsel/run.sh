#!/usr/bin/env bash
set -euo pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

. avantgraph/vars.sh
. scripts/import-vars.sh

NUM_THREADS=${1:-$(nproc)}

AVANTGRAPH="${AG_BIN}/avantgraph"
RESULTS_FILE="results/results.csv"
mkdir -p results

TIMEOUT_SEC=30
SYSTEM="AvantGraph-morsel"
VARIANT="${NUM_THREADS} threads"

for i in $(seq 1 6); do
    QUERY_FILE="cypher/q${i}.cypher"

    if [[ ! -f "${QUERY_FILE}" ]]; then
        echo "WARNING: missing ${QUERY_FILE}" >&2
        continue
    fi

    echo "Running query ${i}"

    RAW=$(mktemp)

    RC=0
    timeout --kill-after=5 "${TIMEOUT_SEC}" \
        "${AVANTGRAPH}" \
        --verbose \
        --query-type=cypher \
        --enable-morsel-pipelines \
        "${AG_GRAPH_DIR}" \
        "${QUERY_FILE}" \
        > "${RAW}" 2>&1 || RC=$?

    if [[ $RC -eq 124 ]]; then
        DURATION="${TIMEOUT_SEC}.0000"
        RESULT="TIMEOUT"
    elif [[ $RC -ne 0 ]]; then
        DURATION="0.0000"
        RESULT="FAIL"
    else
        WAIT=$(awk '/-----Wait Time-----/{getline; print $1; exit}' "${RAW}")
        DURATION=$(awk "BEGIN { printf \"%.4f\", ${WAIT:-0} }")
        RESULT=$(grep -oP '(?<=%count=int:)\d+' "${RAW}" | head -1 || true)
        RESULT=${RESULT:-N/A}
    fi

    printf '%s\t%s\t%s\t%s\t%s\t%s\n' \
        "${SYSTEM}" "${VARIANT}" "${SF}" "${i}" "${DURATION}" "${RESULT}" \
        >> "${RESULTS_FILE}"

    rm -f "${RAW}"
done

echo "Done. Results appended to ${RESULTS_FILE}"
