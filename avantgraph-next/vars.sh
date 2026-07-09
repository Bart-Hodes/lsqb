export AG_BIN=${AG_BIN:-$HOME/avantgraph-next/install/bin}
# Share the graph loaded by the avantgraph/ variant — on-disk format is
# compatible between the two builds, so no need to load it twice.
export AG_GRAPH_DIR=${AG_GRAPH_DIR:-`pwd`/avantgraph/scratch/lsqb-sf${SF}}
