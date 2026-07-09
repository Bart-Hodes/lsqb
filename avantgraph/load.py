#!/usr/bin/env python3
"""
DuckDB-based loader for the LSQB social-network graph into AvantGraph.

Mirrors the approach of graphalg-utils/graphalytics/run.py: use DuckDB to read
the CSV files, assign globally-unique sequential node ids, emit newline-delimited
JSON (nodes + forward/backward sorted edges), then load into AvantGraph via
ag-load-graph. Only topology is loaded (no properties), matching create-schema.sh.
"""
from pathlib import Path
import argparse
import subprocess
import duckdb

# Node namespace -> AvantGraph vertex labels. The namespace matches the CSV
# basename (e.g. Person.csv, Comment.csv) and the :ID(namespace) header.
NODES = [
    ("Continent",  ["Continent"]),
    ("Country",    ["Country"]),
    ("City",       ["City"]),
    ("University", ["University"]),
    ("Company",    ["Company"]),
    ("TagClass",   ["TagClass"]),
    ("Tag",        ["Tag"]),
    ("Forum",      ["Forum"]),
    ("Person",     ["Person"]),
    ("Comment",    ["Message", "Comment"]),
    ("Post",       ["Message", "Post"]),
]
NS_LABELS = {ns: labels for ns, labels in NODES}

# (edge label, csv basename, start namespace, end namespace)
EDGES = [
    ("IS_PART_OF",     "Country_isPartOf_Continent",       "Country",    "Continent"),
    ("IS_PART_OF",     "City_isPartOf_Country",            "City",       "Country"),
    ("IS_SUBCLASS_OF", "TagClass_isSubclassOf_TagClass",   "TagClass",   "TagClass"),
    ("IS_LOCATED_IN",  "University_isLocatedIn_City",       "University", "City"),
    ("IS_LOCATED_IN",  "Company_isLocatedIn_Country",       "Company",    "Country"),
    ("HAS_TYPE",       "Tag_hasType_TagClass",              "Tag",        "TagClass"),
    ("HAS_CREATOR",    "Comment_hasCreator_Person",         "Comment",    "Person"),
    ("IS_LOCATED_IN",  "Comment_isLocatedIn_Country",       "Comment",    "Country"),
    ("REPLY_OF",       "Comment_replyOf_Comment",           "Comment",    "Comment"),
    ("REPLY_OF",       "Comment_replyOf_Post",              "Comment",    "Post"),
    ("CONTAINER_OF",   "Forum_containerOf_Post",            "Forum",      "Post"),
    ("HAS_MEMBER",     "Forum_hasMember_Person",            "Forum",      "Person"),
    ("HAS_MODERATOR",  "Forum_hasModerator_Person",         "Forum",      "Person"),
    ("HAS_TAG",        "Forum_hasTag_Tag",                  "Forum",      "Tag"),
    ("HAS_INTEREST",   "Person_hasInterest_Tag",            "Person",     "Tag"),
    ("IS_LOCATED_IN",  "Person_isLocatedIn_City",           "Person",     "City"),
    ("KNOWS",          "Person_knows_Person",               "Person",     "Person"),
    ("LIKES",          "Person_likes_Comment",              "Person",     "Comment"),
    ("LIKES",          "Person_likes_Post",                 "Person",     "Post"),
    ("HAS_CREATOR",    "Post_hasCreator_Person",            "Post",       "Person"),
    ("HAS_TAG",        "Comment_hasTag_Tag",                "Comment",    "Tag"),
    ("HAS_TAG",        "Post_hasTag_Tag",                   "Post",       "Tag"),
    ("IS_LOCATED_IN",  "Post_isLocatedIn_Country",          "Post",       "Country"),
    ("STUDY_AT",       "Person_studyAt_University",         "Person",     "University"),
    ("WORK_AT",        "Person_workAt_Company",             "Person",     "Company"),
]


def sql_list(values):
    inner = ", ".join("'" + v.replace("'", "''") + "'" for v in values)
    return f"[{inner}]"


def build_tables(conn, csv_dir):
    conn.execute("DROP TABLE IF EXISTS node_raw")
    conn.execute("DROP TABLE IF EXISTS edge_raw")
    conn.execute("CREATE TABLE node_raw(ns VARCHAR, orig_id BIGINT, labels VARCHAR[])")
    conn.execute(
        "CREATE TABLE edge_raw("
        "edge_label VARCHAR, start_ns VARCHAR, end_ns VARCHAR, "
        "start_labels VARCHAR[], end_labels VARCHAR[], src_orig BIGINT, trg_orig BIGINT)"
    )

    for ns, labels in NODES:
        path = csv_dir / f"{ns}.csv"
        print(f"Reading nodes: {path.name}")
        conn.execute(f"""
            INSERT INTO node_raw
            SELECT '{ns}' AS ns, orig_id, {sql_list(labels)} AS labels
            FROM read_csv('{path}', delim='|', skip=1, header=false,
                          columns={{'orig_id': 'BIGINT'}})
        """)

    for label, basename, sns, ens in EDGES:
        path = csv_dir / f"{basename}.csv"
        print(f"Reading edges: {path.name}")
        conn.execute(f"""
            INSERT INTO edge_raw
            SELECT '{label}' AS edge_label, '{sns}' AS start_ns, '{ens}' AS end_ns,
                   {sql_list(NS_LABELS[sns])} AS start_labels,
                   {sql_list(NS_LABELS[ens])} AS end_labels,
                   src_orig, trg_orig
            FROM read_csv('{path}', delim='|', skip=1, header=false,
                          columns={{'src_orig': 'BIGINT', 'trg_orig': 'BIGINT'}})
        """)

    # Assign globally-unique sequential node ids, then continue numbering for
    # edges (matching the single running counter used by the old import_csv.py).
    conn.execute("DROP TABLE IF EXISTS nodes")
    conn.execute("""
        CREATE TABLE nodes AS
        SELECT (row_number() OVER (ORDER BY ns, orig_id)) - 1 AS gid, ns, orig_id, labels
        FROM node_raw
    """)
    conn.execute("CREATE UNIQUE INDEX node_key ON nodes(ns, orig_id)")

    (n_nodes,) = conn.execute("SELECT count(*) FROM nodes").fetchone()

    conn.execute("DROP TABLE IF EXISTS edges")
    conn.execute(f"""
        CREATE TABLE edges AS
        SELECT {n_nodes} + (row_number() OVER (ORDER BY e.start_ns, e.src_orig)) - 1 AS eid,
               s.gid AS src_gid, t.gid AS trg_gid,
               e.edge_label, e.start_labels, e.end_labels
        FROM edge_raw e
        JOIN nodes s ON s.ns = e.start_ns AND s.orig_id = e.src_orig
        JOIN nodes t ON t.ns = e.end_ns   AND t.orig_id = e.trg_orig
    """)

    (n_edges_in,) = conn.execute("SELECT count(*) FROM edge_raw").fetchone()
    (n_edges,) = conn.execute("SELECT count(*) FROM edges").fetchone()
    if n_edges != n_edges_in:
        print(f"WARNING: dropped {n_edges_in - n_edges} edges with missing endpoints")
    print(f"Nodes: {n_nodes}, edges: {n_edges}")


def write_json(conn, out_dir):
    nodes_json = out_dir / "nodes.json"
    fwd_json = out_dir / "edges_fwd.json"
    bwd_json = out_dir / "edges_bwd.json"

    print("Writing nodes.json..")
    conn.execute(f"""
        COPY (
            SELECT 'node' AS type,
                   CAST(gid AS VARCHAR) AS id,
                   labels AS labels,
                   '{{}}'::JSON AS properties
            FROM nodes
            ORDER BY gid
        ) TO '{nodes_json}' (FORMAT JSON)
    """)

    print("Writing edges_fwd.json (sorted by src)..")
    conn.execute(f"""
        COPY (
            SELECT 'relationship' AS type,
                   CAST(eid AS VARCHAR) AS id,
                   edge_label AS label,
                   {{'id': CAST(src_gid AS VARCHAR), 'labels': start_labels}} AS "start",
                   {{'id': CAST(trg_gid AS VARCHAR), 'labels': end_labels}} AS "end",
                   '{{}}'::JSON AS properties
            FROM edges
            ORDER BY src_gid
        ) TO '{fwd_json}' (FORMAT JSON)
    """)

    print("Writing edges_bwd.json (sorted by trg)..")
    conn.execute(f"""
        COPY (
            SELECT 'relationship' AS type,
                   CAST(eid AS VARCHAR) AS id,
                   edge_label AS label,
                   {{'id': CAST(src_gid AS VARCHAR), 'labels': start_labels}} AS "start",
                   {{'id': CAST(trg_gid AS VARCHAR), 'labels': end_labels}} AS "end",
                   '{{}}'::JSON AS properties
            FROM edges
            ORDER BY trg_gid
        ) TO '{bwd_json}' (FORMAT JSON)
    """)

    return nodes_json, fwd_json, bwd_json


def load_into_avantgraph(ag_bin, graph_dir, nodes_json, fwd_json, bwd_json, keep_json):
    ag_load = str(ag_bin / "ag-load-graph")

    print("Loading vertices into AvantGraph..")
    subprocess.run(
        [ag_load, "--graph-format=json", str(nodes_json), str(graph_dir)],
        check=True)

    print("Loading forward edges into AvantGraph..")
    subprocess.run(
        [ag_load, "--graph-format=json", "--load-direction=forwards",
         str(fwd_json), str(graph_dir)],
        check=True)

    print("Loading backward edges into AvantGraph..")
    subprocess.run(
        [ag_load, "--graph-format=json", "--load-direction=backwards",
         str(bwd_json), str(graph_dir)],
        check=True)

    if not keep_json:
        nodes_json.unlink()
        fwd_json.unlink()
        bwd_json.unlink()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_dir", type=Path, help="Directory with LSQB CSV files")
    parser.add_argument("graph_dir", type=Path, help="AvantGraph graph directory (schema already created)")
    parser.add_argument("--ag-bin", type=Path, required=True, help="AvantGraph bin directory")
    parser.add_argument("--keep-json", action="store_true", help="Do not delete intermediate JSON files")
    args = parser.parse_args()

    args.graph_dir.mkdir(parents=True, exist_ok=True)

    dbfile = args.graph_dir / "load.duckdb"
    if dbfile.exists():
        dbfile.unlink()
    with duckdb.connect(str(dbfile)) as conn:
        conn.execute(f"PRAGMA threads={__import__('os').cpu_count() or 1}")
        build_tables(conn, args.csv_dir)
        nodes_json, fwd_json, bwd_json = write_json(conn, args.graph_dir)
    dbfile.unlink()

    load_into_avantgraph(args.ag_bin, args.graph_dir, nodes_json, fwd_json, bwd_json, args.keep_json)
    print("Done loading.")


if __name__ == "__main__":
    main()
