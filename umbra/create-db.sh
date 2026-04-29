#!/usr/bin/env bash

set -eu
set -o pipefail

cd "$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd ..

. umbra/vars.sh

echo -n "Cleaning up . . ."
# ensure database dir exists and is empty
mkdir -p ${UMBRA_DATABASE_DIR}/
docker run \
    --user=$(id -u):$(id -g) \
    --entrypoint=sh \
    --volume=${UMBRA_DATABASE_DIR}:/var/db/:z \
    ${UMBRA_DOCKER_IMAGE} \
    -c "rm -rf /var/db/*"
echo " Cleanup done."
