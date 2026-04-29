#!/usr/bin/env python3
"""Plot all benchmarked systems across scale factors.

Validates results against expected output and drops+warns on mismatches.
"""

import re
import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

RESULTS_FILE = "results/results.csv"
EXPECTED_FILE = "expected-output/expected-output.csv"

COLS = ["system", "variant", "sf", "query", "time", "result"]

SYSTEM_COLORS = {
    "AvantGraph":        "#2563eb",
    "AvantGraph-Morsel": "#f97316",
    "DuckDB":            "#22c55e",
    "DuckPGQ":           "#16a34a",
    "KuzuDB":            "#a855f7",
    "Neo4j":             "#ef4444",
    "Memgraph":          "#eab308",
    "Hyper":             "#06b6d4",
    "Umbra":             "#64748b",
    "MySQL":             "#dc2626",
}

def canonical_system(s: str) -> str:
    """Strip version suffix and normalize casing."""
    base = re.sub(r"-\d.*$", "", str(s))
    if base.lower() == "avantgraph-morsel":
        return "AvantGraph-Morsel"
    return base

# -- Load data ----------------------------------------------------------------

df = pd.read_csv(RESULTS_FILE, header=None, sep="\t", names=COLS, dtype=str)
# Drop any stray CSV-header rows or blank rows
df = df[df["query"].str.match(r"^\d+$", na=False)].copy()
df["query"] = df["query"].astype(int)
df["time"] = df["time"].astype(float)
df["system"] = df["system"].apply(canonical_system)

expected = pd.read_csv(EXPECTED_FILE, header=None, sep="\t", names=COLS)

def normalize_sf(sf):
    try:
        v = float(sf)
        return str(int(v)) if v == int(v) else str(v)
    except (ValueError, TypeError):
        return str(sf)

expected_lookup = {}
for _, row in expected.iterrows():
    key = (normalize_sf(row["sf"]), int(row["query"]))
    expected_lookup[key] = int(row["result"])

# -- Validate results against expected output ---------------------------------

bad_mask = pd.Series(False, index=df.index)
for idx, row in df.iterrows():
    key = (normalize_sf(row["sf"]), int(row["query"]))
    if key not in expected_lookup:
        continue
    expected_val = expected_lookup[key]
    actual = row["result"]
    if str(actual) in ("N/A", "TIMEOUT", "FAIL"):
        bad_mask[idx] = True
        continue
    try:
        if int(actual) != expected_val:
            print(
                f"WARNING: dropping {row['system']} SF={row['sf']} Q{row['query']}: "
                f"got {actual}, expected {expected_val}",
                file=sys.stderr,
            )
            bad_mask[idx] = True
    except (ValueError, TypeError):
        bad_mask[idx] = True

n_dropped = bad_mask.sum()
if n_dropped > 0:
    print(f"Dropped {n_dropped} rows with incorrect/missing results.", file=sys.stderr)
df = df[~bad_mask].copy()

if df.empty:
    print("No valid data to plot.", file=sys.stderr)
    sys.exit(1)

# -- Aggregate: median + min/max per (system, sf, query) ----------------------

agg = df.groupby(["system", "sf", "query"], as_index=False)["time"].agg(
    median="median", min="min", max="max", std="std", count="count"
)

sfs = sorted(agg["sf"].unique(), key=float)
queries = sorted(agg["query"].unique())
systems = sorted(agg["system"].unique())

# -- Plot: one subplot per query, grouped bars per system ---------------------

n_queries = len(queries)
ncols = 3
nrows = (n_queries + ncols - 1) // ncols

fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 3.8 * nrows), squeeze=False)

x = np.arange(len(sfs))
n_sys = len(systems)
width = 0.8 / max(n_sys, 1)

for i, q in enumerate(queries):
    ax = axes[i // ncols][i % ncols]
    for j, sys_name in enumerate(systems):
        subset = agg[(agg["system"] == sys_name) & (agg["query"] == q)]
        medians, lo_err, hi_err = [], [], []
        for sf in sfs:
            match = subset[subset["sf"] == sf]
            if len(match) > 0:
                row = match.iloc[0]
                medians.append(row["median"])
                lo_err.append(row["median"] - row["min"])
                hi_err.append(row["max"] - row["median"])
            else:
                medians.append(np.nan)
                lo_err.append(0)
                hi_err.append(0)
        offset = -0.4 + (j + 0.5) * width
        color = SYSTEM_COLORS.get(sys_name, None)
        ax.bar(x + offset, medians, width, label=sys_name, color=color,
               yerr=[lo_err, hi_err], capsize=2, error_kw={"lw": 0.7})

    ax.set_title(f"Q{q}", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([str(s) for s in sfs], fontsize=8)
    ax.set_xlabel("Scale Factor")
    ax.set_ylabel("Time (s)")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.grid(axis="y", alpha=0.3)

for i in range(n_queries, nrows * ncols):
    fig.delaxes(axes[i // ncols][i % ncols])

handles, labels = axes[0][0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=min(len(systems), 6),
           fontsize=10, bbox_to_anchor=(0.5, 1.02))

fig.suptitle("LSQB Benchmark — All Systems (median + min/max range)",
             fontsize=13, fontweight="bold", y=1.06)
fig.tight_layout()
fig.savefig("/tmp/avantgraph.png", dpi=300, bbox_inches="tight")
fig.savefig("/tmp/avantgraph.pdf", dpi=300, bbox_inches="tight")
print("Saved plots to /tmp/avantgraph.png and /tmp/avantgraph.pdf")
plt.close()
