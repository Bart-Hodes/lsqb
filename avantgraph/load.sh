#!/usr/bin/env bash

set -eu
set -o pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

bash avantgraph/mergeCsvToJson.sh
bash avantgraph/sortJson.sh
bash avantgraph/loadJson.sh
