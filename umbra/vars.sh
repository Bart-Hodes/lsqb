pushd . > /dev/null
cd "$( cd "$( dirname "${BASH_SOURCE[0]:-${(%):-%x}}" )" >/dev/null 2>&1 && pwd )"

export UMBRA_DATABASE_DIR=`pwd`/scratch/db/
export COMMON_SQL_DIR=`pwd`/../sql
export UMBRA_SQL_DIR=`pwd`/sql/
export UMBRA_SQL_SCRATCH_DIR=`pwd`/scratch/sql
export UMBRA_CONTAINER_NAME=lsqb-umb
export UMBRA_VERSION=latest
export UMBRA_DOCKER_IMAGE=umbradb/umbra:${UMBRA_VERSION}

if [ -z "${UMBRA_BUFFERSIZE+x}" ]; then
    export UMBRA_DOCKER_BUFFERSIZE_ENV_VAR=
else
    export UMBRA_DOCKER_BUFFERSIZE_ENV_VAR="--env BUFFERSIZE=${UMBRA_BUFFERSIZE}"
fi

popd > /dev/null
