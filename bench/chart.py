"""Generate docs/benchmark.svg (+ per-category chart) from bench/results/*.test.json.

Run:  var/bench/chart-venv/bin/python bench/chart.py   (needs matplotlib)

Theme note: transparent background, mid-tone text/grid so the SVG stays
readable on both light and dark README themes.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
# Fixed id salt and no timestamp, so re-running on unchanged results rewrites identical SVGs.
matplotlib.rcParams["svg.hashsalt"] = "bloorecall-bench"
import matplotlib.pyplot as plt  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULTS = PROJECT_ROOT / "bench" / "results"
DOCS = PROJECT_ROOT / "docs"

ORDER = [
    "grep",
    "filename",
    "bm25",
    "dense",
    "hybrid",
    "hybrid-rrf",
    "hybrid-noheadings",
    "hybrid-norerank",
    "hybrid-norecency",
]
LABELS = {
    "grep": "grep\n(baseline)",
    "filename": "filename\n(baseline)",
    "bm25": "bm25\nonly",
    "dense": "dense\nonly",
    "hybrid": "hybrid v1.0\n(linear)",
    "hybrid-rrf": "hybrid v1.1\n(shipped)",
    "hybrid-noheadings": "hybrid\nno headings",
    "hybrid-norerank": "hybrid\nno re-rank",
    "hybrid-norecency": "hybrid\nno recency",
}

TEXT = "#9aa4b2"
GRID = "#4a5261"
# Keyed by system so adding one never repaints the rest; the shipped system gets the accent.
COLORS = {
    "grep": "#7f8ea3",
    "filename": "#8d9bb0",
    "bm25": "#6f8f7a",
    "dense": "#8f9a6f",
    "hybrid": "#b08d5f",
    "hybrid-rrf": "#d9a441",
    "hybrid-noheadings": "#a37f8e",
    "hybrid-norerank": "#7f7fa3",
    "hybrid-norecency": "#6f9a9a",
}
EDGE = "#c7cdd6"


def load_results() -> dict[str, dict]:
    results = {}
    for path in sorted(RESULTS.glob("*.test.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        results[data["system"]] = data
    return results


def style_axes(ax) -> None:
    ax.set_facecolor("none")
    for spine in ax.spines.values():
        spine.set_color(GRID)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.5, alpha=0.6)
    ax.set_axisbelow(True)


def headline_chart(results: dict[str, dict]) -> None:
    systems = [s for s in ORDER if s in results]
    metric = "recall@5"
    values = [results[s]["metrics"]["overall"][metric] for s in systems]
    lowers = [results[s]["metrics"]["overall"][metric] - results[s]["metrics"]["overall"]["ci95"][metric][0] for s in systems]
    uppers = [results[s]["metrics"]["overall"]["ci95"][metric][1] - results[s]["metrics"]["overall"][metric] for s in systems]

    fig, ax = plt.subplots(figsize=(9.6, 4.6), dpi=160)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    bars = ax.bar(
        range(len(systems)),
        values,
        yerr=[lowers, uppers],
        capsize=4,
        color=[COLORS[s] for s in systems],
        edgecolor=EDGE,
        linewidth=0.6,
        error_kw={"ecolor": TEXT, "elinewidth": 1.0},
    )
    ax.set_xticks(range(len(systems)), [LABELS[s] for s in systems])
    ax.set_ylabel(f"{metric} (test, 95% bootstrap CI)", color=TEXT)
    ax.set_ylim(0, 1.12)
    ax.set_title("BlooRecall retrieval benchmark — Recall@5 by system", color=TEXT, fontsize=12)
    style_axes(ax)
    # Labels sit above each whisker's cap so they never collide with the error bar.
    for bar, value, upper in zip(bars, values, uppers):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + upper + 0.015,
            f"{value:.2f}",
            ha="center",
            color=TEXT,
            fontsize=9,
        )
    fig.tight_layout()
    DOCS.mkdir(exist_ok=True)
    fig.savefig(DOCS / "benchmark.svg", transparent=True, metadata={"Date": None})
    plt.close(fig)


def category_chart(results: dict[str, dict]) -> None:
    systems = [s for s in ORDER if s in results]
    categories = sorted(
        {cat for s in systems for cat in results[s]["metrics"]["by_category"]}
    )
    metric = "mrr@10"
    fig, ax = plt.subplots(figsize=(10.4, 5.0), dpi=160)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    width = 0.8 / len(systems)
    for index, system in enumerate(systems):
        values = [
            results[system]["metrics"]["by_category"].get(cat, {}).get(metric, 0.0)
            for cat in categories
        ]
        positions = [i + index * width for i in range(len(categories))]
        ax.bar(positions, values, width=width, label=system, color=COLORS[system], edgecolor=EDGE, linewidth=0.4)
    ax.set_xticks([i + 0.4 for i in range(len(categories))], categories, fontsize=8)
    ax.set_ylabel(f"{metric} by category (test)", color=TEXT)
    ax.set_ylim(0, 1.04)
    ax.set_title("MRR@10 per query category", color=TEXT, fontsize=12)
    style_axes(ax)
    legend = ax.legend(fontsize=8, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.09), ncol=5)
    for text in legend.get_texts():
        text.set_color(TEXT)
    fig.tight_layout()
    fig.savefig(DOCS / "benchmark-by-category.svg", transparent=True, metadata={"Date": None})
    plt.close(fig)


if __name__ == "__main__":
    results = load_results()
    if not results:
        sys.exit(f"no *.test.json results in {RESULTS}")
    headline_chart(results)
    category_chart(results)
    print(f"wrote {DOCS/'benchmark.svg'} and {DOCS/'benchmark-by-category.svg'}")
