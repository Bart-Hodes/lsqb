#!/usr/bin/env python3
"""Plot AvantGraph vs AvantGraph-Morsel results across scale factors.

Validates results against expected output and drops+warns on mismatches.
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

RESULTS_FILE = "results/results.csv"
EXPECTED_FILE = "expected-output/expected-output.csv"

COLS = ["system", "variant", "sf", "query", "time", "result"]
AG_SYSTEMS = ["AvantGraph", "AvantGraph-Morsel"]

# -- Load data ----------------------------------------------------------------

df = pd.read_csv(RESULTS_FILE, header=None, sep="\t", names=COLS)
df = df[df["system"].isin(AG_SYSTEMS)].copy()

expected = pd.read_csv(EXPECTED_FILE, header=None, sep="\t", names=COLS)
# Build lookup: (sf, query) -> expected result
def normalize_sf(sf):
    """Normalize scale factor to a canonical string (e.g. 10.0 -> '10', 0.1 -> '0.1')."""
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
    if str(actual) == "N/A" or int(actual) != expected_val:
        print(
            f"WARNING: dropping {row['system']} SF={row['sf']} Q{row['query']}: "
            f"got {actual}, expected {expected_val}",
            file=sys.stderr,
        )
        bad_mask[idx] = True

n_dropped = bad_mask.sum()
if n_dropped > 0:
    print(f"Dropped {n_dropped} rows with incorrect results.", file=sys.stderr)
df = df[~bad_mask].copy()

if df.empty:
    print("No valid AvantGraph data to plot.", file=sys.stderr)
    sys.exit(1)

# -- Aggregate: median + min/max per (system, sf, query) ----------------------

agg = df.groupby(["system", "sf", "query"], as_index=False)["time"].agg(
    median="median", min="min", max="max", std="std", count="count"
)

sfs = sorted(agg["sf"].unique(), key=float)
queries = sorted(agg["query"].unique())

# -- Plot: one subplot per query, bars with error bars showing full range ------

n_queries = len(queries)
ncols = 3
nrows = (n_queries + ncols - 1) // ncols

fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3.5 * nrows), squeeze=False)

colors = {"AvantGraph": "#2563eb", "AvantGraph-Morsel": "#f97316"}
x = np.arange(len(sfs))
width = 0.35

for i, q in enumerate(queries):
    ax = axes[i // ncols][i % ncols]
    for j, sys_name in enumerate(AG_SYSTEMS):
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
                medians.append(0)
                lo_err.append(0)
                hi_err.append(0)
        offset = -width / 2 + j * width
        ax.bar(x + offset, medians, width, label=sys_name, color=colors[sys_name],
               yerr=[lo_err, hi_err], capsize=3, error_kw={"lw": 0.8})

    ax.set_title(f"Q{q}", fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels([str(s) for s in sfs], fontsize=8)
    ax.set_xlabel("Scale Factor")
    ax.set_ylabel("Time (s)")
    ax.set_yscale("log")
    ax.yaxis.set_major_formatter(ticker.ScalarFormatter())
    ax.grid(axis="y", alpha=0.3)

# Remove unused subplots
for i in range(n_queries, nrows * ncols):
    fig.delaxes(axes[i // ncols][i % ncols])

# Single shared legend
handles, labels = axes[0][0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=len(AG_SYSTEMS), fontsize=10,
           bbox_to_anchor=(0.5, 1.02))

fig.suptitle("AvantGraph vs AvantGraph-Morsel — LSQB Benchmark (median + min/max range)",
             fontsize=13, fontweight="bold", y=1.06)
fig.tight_layout()
fig.savefig("/tmp/avantgraph.png", dpi=300, bbox_inches="tight")
fig.savefig("/tmp/avantgraph.pdf", dpi=300, bbox_inches="tight")
print(f"Saved plots to /tmp/avantgraph.png and /tmp/avantgraph.pdf")
plt.close()
