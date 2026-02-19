"""
Plot investment results from checkpoint files (investor_evaluated_*.json).

Loads checkpoint files like:
  checkpoints/investor_evaluated_major_round_8_20260129T184005Z.json

The checkpoint's orchestrator.history is equivalent to results['all_rounds'].
Generates the same plots as plot_investment_results.py (including natural founder
ordering Founder_1, Founder_2, ... in plot5):
1. Each investor_group's successful investments (total_accepted) vs major_round
2. Each founder's budget vs major_round
3. For each major_round, accumulated_investment vs investment_round for each founder
4. Success rate (accumulated_investment >= 0.8 * total_budget) vs major_round
5. For each major_round, per-founder Budget vs final Accumulated Investment
6+7. Per-founder accepted bars (group + investor) per major round
8. Per-founder score bars (investor + group) per major round
"""

import json
import argparse
from pathlib import Path

# Matplotlib global styling overrides (bigger fonts for readability)
import matplotlib.pyplot as plt

# Reuse plotting functions from plot_investment_results
# Run from project root: python analyze/plot_investment_results_from_checkpoint.py
from plot_investment_results import (
    plot_investor_group_investments,
    plot_founder_budgets,
    plot_major_round_investments,
    plot_success_rate,
    plot_budget_vs_funding_per_major_round,
    plot_major_round_group_and_investor_investments_bars,
    plot_major_round_group_accepted_per_founder_ordered,
    plot_major_round_score_bars,
    TARGET_INVESTOR_GROUP,
    TARGET_INVESTOR,
)

# Increase global font sizes for all plots generated from checkpoints.
# (Individual plotting functions may still override specific fontsize values.)
plt.rcParams.update(
    {
        "font.size": 14,
        "axes.titlesize": 20,
        "axes.labelsize": 18,
        "xtick.labelsize": 14,
        "ytick.labelsize": 14,
        "legend.fontsize": 14,
    }
)


def load_results_from_checkpoint(checkpoint_path: str) -> dict:
    """
    Load checkpoint file and extract results in the same format as
    results_10_founders.json (with all_rounds).

    The investor_evaluated checkpoint stores:
    - orchestrator.history: rounds 1 to (major_round - 1)
    - payload.round_data: the completed round_data for major_round
    We merge them to get the full history including the last evaluated round.
    """
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        checkpoint = json.load(f)

    history = list(checkpoint.get("orchestrator", {}).get("history", []))
    kind = checkpoint.get("kind", "")
    payload = checkpoint.get("payload", {}) or {}

    # For investor_evaluated, the current round is in payload.round_data
    if kind == "investor_evaluated" and payload.get("round_data"):
        round_data = payload["round_data"]
        if not history or history[-1].get("round") != round_data.get("round"):
            history.append(round_data)

    if not history:
        raise ValueError(
            f"Checkpoint has no round data (orchestrator.history or payload.round_data): {checkpoint_path}"
        )

    return {"all_rounds": history}


def main():
    parser = argparse.ArgumentParser(
        description="Plot investment results from checkpoint file"
    )
    parser.add_argument(
        "checkpoint",
        type=str,
        default="/home/dataset-local/market4science/checkpoints_stategy/investor_evaluated_major_round_10_20260203T142902Z.json",
        nargs="?",
        help="Path to investor_evaluated checkpoint JSON file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Output directory for plots (default: <checkpoint_stem>_plots)",
    )
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint)
    if not checkpoint_path.exists():
        print(f"Error: {checkpoint_path} not found!")
        return 1

    if args.output:
        save_path = Path(args.output)
    else:
        # e.g. investor_evaluated_major_round_8_20260129T184005Z -> investor_evaluated_major_round_8_20260129T184005Z_plots
        save_path = Path(checkpoint_path.stem + "_plots")

    save_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading checkpoint from {checkpoint_path}...")
    results = load_results_from_checkpoint(str(checkpoint_path))
    num_rounds = len(results["all_rounds"])
    print(f"Loaded {num_rounds} major rounds")

    print("\nGenerating plots...")
    print("=" * 60)

    # Plot 1: Investor group investments
    print("\n[1/4] Plotting investor group successful investments...")
    plot_investor_group_investments(results, str(save_path))

    # Plot 2: Founder budgets
    print("\n[2/4] Plotting founder budgets...")
    plot_founder_budgets(results, str(save_path))

    # Plot 3: Major round investments
    print("\n[3/4] Plotting accumulated investments by investment round for each major round...")
    plot_major_round_investments(results, str(save_path))

    # Plot 4: Success rate
    print("\n[4/4] Plotting success rate...")
    plot_success_rate(results, str(save_path))

    # Plot 5: Budget vs funding per major round
    print("\n[5] Plotting budget vs funding per major round...")
    plot_budget_vs_funding_per_major_round(results, str(save_path))

    # Plot 6+7 (group-only): per major round, per-founder accepted bars (for each group)
    all_scores = {}
    for rd in results.get("all_rounds", []):
        all_scores.update(rd.get("all_scores") or {})
    group_names = sorted(all_scores.keys())
    if group_names:
        print("\n[6+7] Plotting per-founder accepted bars (group only) per major round for each group...")
        for g in group_names:
            plot_major_round_group_and_investor_investments_bars(results, str(save_path), g)
        print("\n[6+7 - new] Plotting per-founder accepted bars (group only, ordered by founder index) per major round for each group...")
        for g in group_names:
            plot_major_round_group_accepted_per_founder_ordered(results, str(save_path), g)

    # Plot 8: per major round, per-founder score bars
    if TARGET_INVESTOR_GROUP and TARGET_INVESTOR:
        print("\n[8] Plotting per-founder score bars (investor + group) per major round...")
        plot_major_round_score_bars(
            results, str(save_path), TARGET_INVESTOR_GROUP, TARGET_INVESTOR
        )

    print("\n" + "=" * 60)
    print(f"All plots saved to {save_path}/")
    return 0


if __name__ == "__main__":
    exit(main())
