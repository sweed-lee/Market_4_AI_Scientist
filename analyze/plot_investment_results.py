"""
Plot investment results from results_10_founders.json

Generates multiple types of plots:
1. Each investor_group's successful investments (total_accepted) vs major_round
2. Each founder's budget vs major_round
3. For each major_round, accumulated_investment vs investment_round for each founder
4. Success rate (accumulated_investment >= 0.8 * total_budget) vs major_round
5. For each major_round, per-founder Budget vs final Accumulated Investment (side-by-side bars)
6. For selected investor_groups, total accepted investment per major_round (successful only)
7. For selected investors, total accepted investment per major_round (successful only)
8. For each major_round, score distribution for a selected investor and aggregated score distribution for a selected group
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from pathlib import Path

# === User-configurable selectors ===
# Leave empty/None to skip those plots.
# Note: For the per-founder bar charts (plot6+7 and plot8), we use ONE group + ONE investor.
TARGET_INVESTOR_GROUP = "InvestorGroup_1"
TARGET_INVESTOR = "Investor_1_G1"

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

def load_results(filepath):
    """Load results from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def _sort_founders_natural(founder_names):
    """Sort founder names by numeric order (Founder_1, Founder_2, ..., Founder_25)."""
    def key_fn(name):
        try:
            return int(name.split("_")[-1])
        except (ValueError, IndexError):
            return 0
    return sorted(founder_names, key=key_fn)

def plot_investor_group_investments(results, save_path):
    """Plot 1: Each investor_group's successful investments vs major_round."""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Collect data: {major_round: {group_name: total_accepted}}
    data = defaultdict(lambda: defaultdict(float))
    investor_groups = set()
    
    for round_data in results['all_rounds']:
        major_round = round_data['round']
        if 'investment_history' not in round_data:
            continue
        
        inv_history = round_data['investment_history']
        # Get all investment rounds
        for key in sorted(inv_history.keys()):
            if not key.startswith('investment_round_'):
                continue
            round_info = inv_history[key]
            if 'investor_groups' not in round_info:
                continue
            
            for group_name, group_data in round_info['investor_groups'].items():
                investor_groups.add(group_name)
                # Sum up total_accepted across all investment rounds in this major round
                data[major_round][group_name] += group_data.get('total_accepted', 0)
    
    # Plot
    investor_groups = sorted(investor_groups)
    major_rounds = sorted(data.keys())
    x = np.arange(len(major_rounds))
    width = 0.8 / len(investor_groups)
    
    for i, group_name in enumerate(investor_groups):
        values = [data[mr][group_name] for mr in major_rounds]
        ax.bar(x + i * width, values, width, label=group_name, alpha=0.8)
    
    ax.set_xlabel('Major Round', fontsize=18, fontweight='bold')
    ax.set_ylabel('Total Accepted Investment (tokens)', fontsize=18, fontweight='bold')
    ax.set_title('Investor Group Successful Investments by Major Round', fontsize=22, fontweight='bold')
    ax.set_xticks(x + width * (len(investor_groups) - 1) / 2)
    ax.set_xticklabels([f'Round {mr}' for mr in major_rounds])
    ax.tick_params(axis='x', labelsize=16)
    ax.tick_params(axis='y', labelsize=16)
    ax.legend(loc='best', ncol=2, fontsize=16)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{save_path}/plot1_investor_group_investments.png', dpi=300, bbox_inches='tight')
    print("Saved: plot1_investor_group_investments.png")
    plt.close()

def plot_founder_budgets(results, save_path):
    """Plot 2: Each founder's budget vs major_round."""
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Collect data: {major_round: {founder_name: budget}}
    data = {}
    founders = set()
    
    for round_data in results['all_rounds']:
        major_round = round_data['round']
        if 'budgets' not in round_data:
            continue
        
        data[major_round] = {}
        for founder_name, budget in round_data['budgets'].items():
            founders.add(founder_name)
            data[major_round][founder_name] = budget
    
    # Plot
    founders = sorted(founders)
    major_rounds = sorted(data.keys())
    x = np.arange(len(major_rounds))
    width = 0.8 / len(founders)
    
    for i, founder_name in enumerate(founders):
        values = [data[mr].get(founder_name, 0) for mr in major_rounds]
        ax.plot(x, values, marker='o', label=founder_name, linewidth=2, markersize=6)
    
    ax.set_xlabel('Major Round', fontsize=18, fontweight='bold')
    ax.set_ylabel('Budget (tokens)', fontsize=18, fontweight='bold')
    ax.set_title('Founder Budgets by Major Round', fontsize=22, fontweight='bold')
    ax.set_xticks(x)
    ax.tick_params(axis='x', labelsize=16)
    ax.tick_params(axis='y', labelsize=16)
    ax.set_xticklabels([f'Round {mr}' for mr in major_rounds])
    ax.legend(loc='best', ncol=2, fontsize=16)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{save_path}/plot2_founder_budgets.png', dpi=300, bbox_inches='tight')
    print("Saved: plot2_founder_budgets.png")
    plt.close()

def plot_major_round_investments(results, save_path):
    """Plot 3: For each major_round, accumulated_investment vs investment_round for each founder."""
    for round_data in results['all_rounds']:
        major_round = round_data['round']
        if 'investment_history' not in round_data:
            continue
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Collect data: {founder_name: {investment_round: accumulated_investment}}
        data = defaultdict(dict)
        founders = set()
        
        inv_history = round_data['investment_history']
        # Get all investment rounds in order
        investment_rounds = []
        for key in sorted(inv_history.keys()):
            if not key.startswith('investment_round_'):
                continue
            round_num = int(key.split('_')[-1])
            investment_rounds.append(round_num)
            round_info = inv_history[key]
            
            if 'founders' not in round_info:
                continue
            
            for founder_name, founder_data in round_info['founders'].items():
                founders.add(founder_name)
                accumulated = founder_data.get('accumulated_investment', 0)
                data[founder_name][round_num] = accumulated
        
        # Plot
        founders = sorted(founders)
        investment_rounds = sorted(investment_rounds)
        
        for founder_name in founders:
            values = [data[founder_name].get(ir, 0) for ir in investment_rounds]
            ax.plot(investment_rounds, values, marker='o', label=founder_name, linewidth=2, markersize=6)
        
        ax.set_xlabel('Investment Round', fontsize=18, fontweight='bold')
        ax.set_ylabel('Accumulated Investment (tokens)', fontsize=18, fontweight='bold')
        ax.tick_params(axis='x', labelsize=16)
        ax.tick_params(axis='y', labelsize=16)
        ax.set_title(f'Accumulated Investment by Investment Round (Major Round {major_round})', 
                     fontsize=22, fontweight='bold')
        ax.legend(loc='best', ncol=2, fontsize=16)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(f'{save_path}/plot3_major_round_{major_round}_investments.png', dpi=300, bbox_inches='tight')
        print(f"Saved: plot3_major_round_{major_round}_investments.png")
        plt.close()

def plot_success_rate(results, save_path):
    """Plot 4: Success rate (accumulated_investment >= 0.8 * total_budget) vs major_round."""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Collect data: {major_round: success_count, total_count}
    success_data = {}
    
    for round_data in results['all_rounds']:
        major_round = round_data['round']
        if 'investment_history' not in round_data:
            continue
        
        # Get the last investment round
        inv_history = round_data['investment_history']
        last_round_key = None
        last_round_num = -1
        
        for key in inv_history.keys():
            if not key.startswith('investment_round_'):
                continue
            round_num = int(key.split('_')[-1])
            if round_num > last_round_num:
                last_round_num = round_num
                last_round_key = key
        
        if last_round_key is None:
            continue
        
        last_round_info = inv_history[last_round_key]
        if 'founders' not in last_round_info:
            continue
        
        # Get budgets from round_data
        budgets = round_data.get('budgets', {})
        
        success_count = 0
        total_count = 0
        
        for founder_name, founder_data in last_round_info['founders'].items():
            total_budget = budgets.get(founder_name, 0)
            if total_budget == 0:
                continue
            
            accumulated = founder_data.get('accumulated_investment', 0)
            threshold = 0.8 * total_budget
            
            total_count += 1
            if accumulated >= threshold:
                success_count += 1
        
        if total_count > 0:
            success_data[major_round] = success_count / total_count * 100
    
    # Plot
    major_rounds = sorted(success_data.keys())
    success_rates = [success_data[mr] for mr in major_rounds]
    
    ax.bar(major_rounds, success_rates, alpha=0.7, color='steelblue', edgecolor='black', linewidth=1.5)
    ax.set_xlabel('Major Round', fontsize=18, fontweight='bold')
    ax.set_ylabel('Success Rate (%)', fontsize=18, fontweight='bold')
    ax.set_title('Project Success Rate by Major Round\n(Success = accumulated_investment >= 0.8 * total_budget)', 
                 fontsize=22, fontweight='bold')
    ax.set_xticks(major_rounds)
    ax.set_xticklabels([f'Round {mr}' for mr in major_rounds])
    ax.tick_params(axis='x', labelsize=16)
    ax.tick_params(axis='y', labelsize=16)
    ax.set_ylim([0, 105])
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, (mr, rate) in enumerate(zip(major_rounds, success_rates)):
        ax.text(mr, rate + 2, f'{rate:.1f}%', ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f'{save_path}/plot4_success_rate.png', dpi=300, bbox_inches='tight')
    print("Saved: plot4_success_rate.png")
    plt.close()

def _get_last_investment_round_entry(round_data: dict):
    """Return (round_key, round_info) for last investment_round_* entry in this major round."""
    inv_history = round_data.get("investment_history") or {}
    last_key = None
    last_num = -1
    for k in inv_history.keys():
        if not k.startswith("investment_round_"):
            continue
        try:
            n = int(k.split("_")[-1])
        except Exception:
            continue
        if n > last_num:
            last_num = n
            last_key = k
    if last_key is None:
        return None, None
    return last_key, inv_history.get(last_key)

def plot_budget_vs_funding_per_major_round(results, save_path):
    """
    Plot: For each major round, each founder's Budget vs final Accumulated Investment.
    Saves one figure per major round.
    """
    for round_data in results.get("all_rounds", []):
        major_round = round_data.get("round")
        budgets = round_data.get("budgets") or {}
        if not budgets:
            continue

        _, last_entry = _get_last_investment_round_entry(round_data)
        if not last_entry or "founders" not in last_entry:
            continue

        founders = _sort_founders_natural(budgets.keys())
        funding = {fn: last_entry["founders"].get(fn, {}).get("accumulated_investment", 0) for fn in founders}

        x = np.arange(len(founders))
        width = 0.42
        fig, ax = plt.subplots(figsize=(max(14, len(founders) * 0.5), 8))
        ax.bar(x - width/2, [budgets.get(f, 0) for f in founders], width, label="Budget", alpha=0.8)
        ax.bar(x + width/2, [funding.get(f, 0) for f in founders], width, label="Accumulated Investment", alpha=0.8)

        ax.set_title(f"Budget vs Fundraising (Major Round {major_round})", fontsize=18, fontweight="bold")
        ax.set_xlabel("Founder", fontsize=14, fontweight="bold")
        ax.set_ylabel("Tokens", fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(founders, rotation=60, ha="right")
        ax.legend(loc="best")
        ax.grid(True, axis="y", alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{save_path}/plot5_major_round_{major_round}_budget_vs_funding.png", dpi=300, bbox_inches="tight")
        plt.close()

def plot_selected_investor_group_totals(results, save_path, group_names):
    """
    Plot: For selected investor groups, total accepted investment per major round
    (sum of total_accepted across investment rounds in the major round).
    """
    if not group_names:
        return
    fig, ax = plt.subplots(figsize=(14, 7))

    major_rounds = []
    data = {g: [] for g in group_names}

    for round_data in sorted(results.get("all_rounds", []), key=lambda r: r.get("round", 0)):
        mr = round_data.get("round")
        inv_history = round_data.get("investment_history") or {}
        major_rounds.append(mr)
        # pre-sum totals for this major round
        sums = {g: 0 for g in group_names}
        for key in sorted(inv_history.keys()):
            if not key.startswith("investment_round_"):
                continue
            info = inv_history.get(key, {})
            for g in group_names:
                sums[g] += int(info.get("investor_groups", {}).get(g, {}).get("total_accepted", 0))
        for g in group_names:
            data[g].append(sums[g])

    x = np.arange(len(major_rounds))
    width = 0.8 / max(1, len(group_names))
    for i, g in enumerate(group_names):
        ax.bar(x + i * width, data[g], width, label=g, alpha=0.85)

    ax.set_title("Selected Investor Groups: Total Accepted Investment by Major Round", fontsize=18, fontweight="bold")
    ax.set_xlabel("Major Round", fontsize=14, fontweight="bold")
    ax.set_ylabel("Total Accepted (tokens)", fontsize=14, fontweight="bold")
    ax.set_xticks(x + width * (len(group_names) - 1) / 2)
    ax.set_xticklabels([f"Round {mr}" for mr in major_rounds])
    ax.legend(loc="best")
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{save_path}/plot6_selected_investor_groups_total_accepted.png", dpi=300, bbox_inches="tight")
    plt.close()

def plot_selected_investor_totals(results, save_path, investor_names):
    """
    Plot: For selected investors, total accepted investment per major round.
    Uses investment_history[*]['investors'][group]['investors'][investor]['accepted_total'] if present.
    """
    if not investor_names:
        return
    fig, ax = plt.subplots(figsize=(14, 7))

    major_rounds = []
    data = {inv: [] for inv in investor_names}

    for round_data in sorted(results.get("all_rounds", []), key=lambda r: r.get("round", 0)):
        mr = round_data.get("round")
        inv_history = round_data.get("investment_history") or {}
        major_rounds.append(mr)
        sums = {inv: 0 for inv in investor_names}
        for key in sorted(inv_history.keys()):
            if not key.startswith("investment_round_"):
                continue
            info = inv_history.get(key, {})
            investors_block = info.get("investors", {}) or {}
            for group_name, ginfo in investors_block.items():
                invs = (ginfo.get("investors") or {})
                for inv in investor_names:
                    sums[inv] += int((invs.get(inv) or {}).get("accepted_total", 0))
        for inv in investor_names:
            data[inv].append(sums[inv])

    x = np.arange(len(major_rounds))
    width = 0.8 / max(1, len(investor_names))
    for i, inv in enumerate(investor_names):
        ax.bar(x + i * width, data[inv], width, label=inv, alpha=0.85)

    ax.set_title("Selected Investors: Total Accepted Investment by Major Round", fontsize=18, fontweight="bold")
    ax.set_xlabel("Major Round", fontsize=14, fontweight="bold")
    ax.set_ylabel("Total Accepted (tokens)", fontsize=14, fontweight="bold")
    ax.set_xticks(x + width * (len(investor_names) - 1) / 2)
    ax.set_xticklabels([f"Round {mr}" for mr in major_rounds])
    ax.legend(loc="best")
    ax.grid(True, axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{save_path}/plot7_selected_investors_total_accepted.png", dpi=300, bbox_inches="tight")
    plt.close()

def plot_major_round_group_and_investor_investments_bars(
    results,
    save_path,
    group_name: str,
):
    """
    Plot6+7 (group-only): For each major round, create ONE figure:
      - Selected investor_group's total accepted investment per founder (one bar per founder; sorted desc)

    NOTE: This used to include an investor-level subplot. It has been simplified to
    group-only plotting per user request.
    """
    if not group_name:
        return

    for round_data in results.get("all_rounds", []):
        major_round = round_data.get("round")
        budgets = round_data.get("budgets") or {}
        founders = sorted(budgets.keys())
        if not founders:
            continue

        # --- Group accepted per founder (use all_scores if present) ---
        all_scores = round_data.get("all_scores") or {}
        group_scores = (all_scores.get(group_name) or {})
        group_accepted = {f: float(group_scores.get(f, 0.0)) for f in founders}

        # Sort by value descending
        group_sorted = sorted(group_accepted.items(), key=lambda x: x[1], reverse=True)

        fig, ax = plt.subplots(1, 1, figsize=(max(14, len(founders) * 0.5), 6))
        g_names = [k for k, _ in group_sorted]
        g_vals = [v for _, v in group_sorted]
        x = np.arange(len(g_names))
        ax.bar(x, g_vals, alpha=0.85, color="steelblue", edgecolor="black", linewidth=0.5)
        ax.set_title(
            f"{group_name} accepted investment per founder (Major {major_round})",
            fontsize=14,
            fontweight="bold",
        )
        ax.set_ylabel("Accepted (tokens)", fontsize=12, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(g_names, rotation=60, ha="right", fontsize=9)
        ax.grid(True, axis="y", alpha=0.3)

        safe_group = str(group_name).replace("/", "_")
        plt.tight_layout()
        plt.savefig(
            f"{save_path}/plot6_7_major_round_{major_round}_{safe_group}_group_accepted_per_founder.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()


def _group_color_from_name(group_name: str):
    """
    Deterministic color per investor group.
    - InvestorGroup_1 -> tab10(0), InvestorGroup_2 -> tab10(1), ...
    Falls back to tab10(0) if parsing fails.
    """
    try:
        idx = int(str(group_name).split("_")[-1]) - 1
    except Exception:
        idx = 0
    cmap = plt.cm.get_cmap("tab10", 10)
    return cmap(idx % 10)


def plot_major_round_group_accepted_per_founder_ordered(results, save_path, group_name: str):
    """
    New plot (based on plot6+7 group-only):
    For each major round, create ONE figure per investor group:

    - Founders are ordered by their numeric suffix (Founder_1, Founder_2, ...).
    - Each investor group uses a distinct, deterministic color.
    """
    for round_data in results.get("all_rounds", []):
        major_round = round_data.get("round")
        budgets = round_data.get("budgets") or {}
        founders = _sort_founders_natural(list(budgets.keys()))
        if not founders:
            continue

        all_scores = round_data.get("all_scores") or {}
        if group_name not in all_scores:
            continue

        g_scores = all_scores.get(group_name) or {}
        vals = [float(g_scores.get(f, 0.0)) for f in founders]
        x = np.arange(len(founders))

        fig, ax = plt.subplots(1, 1, figsize=(max(14, len(founders) * 0.55), 7))
        ax.bar(
            x,
            vals,
            width=0.85,
            label=group_name,
            alpha=0.9,
            color=_group_color_from_name(group_name),
            edgecolor="black",
            linewidth=0.4,
        )

        ax.set_title(
            f"{group_name} accepted investment per founder (Major {major_round})",
            fontsize=16,
            fontweight="bold",
        )
        ax.set_ylabel("Accepted (tokens)", fontsize=14, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels(founders, rotation=60, ha="right", fontsize=10)
        ax.grid(True, axis="y", alpha=0.3)
        ax.legend(loc="best", frameon=True)

        plt.tight_layout()
        safe_group = str(group_name).replace("/", "_")
        plt.savefig(
            f"{save_path}/plot6_7_major_round_{major_round}_{safe_group}_group_accepted_per_founder_ordered.png",
            dpi=300,
            bbox_inches="tight",
        )
        plt.close()


def plot_major_round_score_bars(results, save_path, group_name: str, investor_name: str):
    """
    Plot8 (updated): For each major round, create ONE figure with two subplots (stacked):
      - Top: selected investor's step-1 scores per founder (one bar per founder; sorted desc)
      - Bottom: selected investor_group's aggregated scores per founder (one bar per founder; sorted desc)
    """
    if not group_name or not investor_name:
        return

    for round_data in results.get("all_rounds", []):
        major_round = round_data.get("round")
        fb_group = (round_data.get("investor_feedback") or {}).get(group_name) or {}
        if not fb_group:
            continue

        investor_scores = {}
        aggregated_scores = {}
        for founder_name, entry in fb_group.items():
            r1 = entry.get("round1_proposal_scores") or {}
            if investor_name in r1:
                investor_scores[founder_name] = float(r1[investor_name])
            aggregated_scores[founder_name] = float(entry.get("round1_aggregated_score", 0.0))

        if not investor_scores and not aggregated_scores:
            continue

        inv_sorted = sorted(investor_scores.items(), key=lambda x: x[1], reverse=True)
        grp_sorted = sorted(aggregated_scores.items(), key=lambda x: x[1], reverse=True)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(max(14, len(grp_sorted) * 0.5), 10), sharex=False)

        # Top: investor scores
        n1 = [k for k, _ in inv_sorted]
        v1 = [v for _, v in inv_sorted]
        x1 = np.arange(len(n1))
        ax1.bar(x1, v1, alpha=0.85, color="seagreen", edgecolor="black", linewidth=0.5)
        ax1.set_title(f"{investor_name} step-1 scores per founder (Major {major_round})", fontsize=14, fontweight="bold")
        ax1.set_ylabel("Score", fontsize=12, fontweight="bold")
        ax1.set_ylim(0, 105)
        ax1.set_xticks(x1)
        ax1.set_xticklabels(n1, rotation=60, ha="right", fontsize=9)
        ax1.grid(True, axis="y", alpha=0.3)

        # Bottom: group aggregated scores
        n2 = [k for k, _ in grp_sorted]
        v2 = [v for _, v in grp_sorted]
        x2 = np.arange(len(n2))
        ax2.bar(x2, v2, alpha=0.85, color="mediumpurple", edgecolor="black", linewidth=0.5)
        ax2.set_title(f"{group_name} aggregated scores per founder (Major {major_round})", fontsize=14, fontweight="bold")
        ax2.set_ylabel("Aggregated score", fontsize=12, fontweight="bold")
        ax2.set_xticks(x2)
        ax2.set_xticklabels(n2, rotation=60, ha="right", fontsize=9)
        ax2.grid(True, axis="y", alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{save_path}/plot8_major_round_{major_round}_score_bars.png", dpi=300, bbox_inches="tight")
        plt.close()

def main():
    """Main function to generate all plots."""
    name='results_20_founders_nomarketinfo_100'
    filepath = f'{name}.json'
    
    if not Path(filepath).exists():
        print(f"Error: {filepath} not found!")
        return
    
    print(f"Loading results from {filepath}...")
    results = load_results(filepath)
    save_path = f'{name}_plots_1'
    if not Path(save_path).exists():
        Path(save_path).mkdir(parents=True, exist_ok=True)
    
    print("\nGenerating plots...")
    print("=" * 60)
    
    # Plot 1: Investor group investments
    print("\n[1/4] Plotting investor group successful investments...")
    plot_investor_group_investments(results, save_path)
    
    # Plot 2: Founder budgets
    print("\n[2/4] Plotting founder budgets...")
    plot_founder_budgets(results, save_path)
    
    # Plot 3: Major round investments
    print("\n[3/4] Plotting accumulated investments by investment round for each major round...")
    plot_major_round_investments(results, save_path)
    
    # Plot 4: Success rate
    print("\n[4/4] Plotting success rate...")
    plot_success_rate(results, save_path)

    # Plot 5: Budget vs funding per major round
    print("\n[5] Plotting budget vs funding per major round...")
    plot_budget_vs_funding_per_major_round(results, save_path)

    # Plot 6+7 (group-only): per major round, per-founder accepted bars (for one group)
    if TARGET_INVESTOR_GROUP:
        print("\n[6+7] Plotting per-founder accepted bars (group only) per major round...")
        plot_major_round_group_and_investor_investments_bars(results, save_path, TARGET_INVESTOR_GROUP)

    # Plot 8 (updated): per major round, per-founder score bars (investor + group)
    if TARGET_INVESTOR_GROUP and TARGET_INVESTOR:
        print("\n[8] Plotting per-founder score bars (investor + group) per major round...")
        plot_major_round_score_bars(results, save_path, TARGET_INVESTOR_GROUP, TARGET_INVESTOR)
    
    print("\n" + "=" * 60)
    print("All plots generated successfully!")

if __name__ == '__main__':
    main()

