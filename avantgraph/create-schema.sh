set -e

GRAPH_DIR="$1"

ag-schema create-graph "${GRAPH_DIR}" --graph=

ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=City
ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=Comment --vertex-label=Message
ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=Company
ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=Continent
ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=Country
ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=Forum
ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=Person
ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=Post --vertex-label=Message
ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=Tag
ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=TagClass
ag-schema create-vertex-table "${GRAPH_DIR}" --graph= --vertex-label=University

ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=CONTAINER_OF ${STANDARD_EDGE_PROPS} --src-labels=Forum --trg-labels=Post --trg-labels=Message
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=HAS_CREATOR ${STANDARD_EDGE_PROPS} --src-labels=Comment --src-labels=Message --trg-labels=Person
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=HAS_CREATOR ${STANDARD_EDGE_PROPS} --src-labels=Post --src-labels=Message --trg-labels=Person
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=HAS_INTEREST ${STANDARD_EDGE_PROPS} --src-labels=Person --trg-labels=Tag
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=HAS_MEMBER ${STANDARD_EDGE_PROPS} --src-labels=Forum --trg-labels=Person
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=HAS_MODERATOR ${STANDARD_EDGE_PROPS} --src-labels=Forum --trg-labels=Person
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=HAS_TAG ${STANDARD_EDGE_PROPS} --src-labels=Comment --src-labels=Message --trg-labels=Tag
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=HAS_TAG ${STANDARD_EDGE_PROPS} --src-labels=Forum --trg-labels=Tag
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=HAS_TAG ${STANDARD_EDGE_PROPS} --src-labels=Post --src-labels=Message --trg-labels=Tag
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=HAS_TYPE ${STANDARD_EDGE_PROPS} --src-labels=Tag --trg-labels=TagClass
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=IS_LOCATED_IN ${STANDARD_EDGE_PROPS} --src-labels=Comment --src-labels=Message --trg-labels=Country
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=IS_LOCATED_IN ${STANDARD_EDGE_PROPS} --src-labels=Company --trg-labels=Country
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=IS_LOCATED_IN ${STANDARD_EDGE_PROPS} --src-labels=Person --trg-labels=City
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=IS_LOCATED_IN ${STANDARD_EDGE_PROPS} --src-labels=Post --src-labels=Message --trg-labels=Country
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=IS_LOCATED_IN ${STANDARD_EDGE_PROPS} --src-labels=University --trg-labels=City
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=IS_PART_OF ${STANDARD_EDGE_PROPS} --src-labels=City --trg-labels=Country
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=IS_PART_OF ${STANDARD_EDGE_PROPS} --src-labels=Country --trg-labels=Continent
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=IS_SUBCLASS_OF ${STANDARD_EDGE_PROPS} --src-labels=TagClass --trg-labels=TagClass
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=KNOWS ${STANDARD_EDGE_PROPS} --src-labels=Person --trg-labels=Person
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=LIKES ${STANDARD_EDGE_PROPS} --src-labels=Person --trg-labels=Comment --trg-labels=Message
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=LIKES ${STANDARD_EDGE_PROPS} --src-labels=Person --trg-labels=Post --trg-labels=Message
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=REPLY_OF ${STANDARD_EDGE_PROPS} --src-labels=Comment --src-labels=Message --trg-labels=Comment --trg-labels=Message
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=REPLY_OF ${STANDARD_EDGE_PROPS} --src-labels=Comment --src-labels=Message --trg-labels=Post --trg-labels=Message
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=STUDY_AT ${STANDARD_EDGE_PROPS} --src-labels=Person --trg-labels=University
ag-schema create-edge-table "${GRAPH_DIR}" --graph= --edge-label=WORK_AT ${STANDARD_EDGE_PROPS} --src-labels=Person --trg-labels=Company
