"""
Analyze multiple results_{num}_{model}.json files to compute metrics per model.

Metrics:
1) For each model and round: mean and std of total scores across all founders (across all files)
2) For each model, founder (A/B/C) and round: mean and std of that founder's scores (across files)

Usage:
    python analyze_results.py [--glob "results_*.json"]

Outputs:
    - Prints a human-readable summary to stdout
    - Writes JSON summaries per model to summary_{model}.json
"""

import argparse
import glob
import json
import os
import re
from collections import defaultdict
from statistics import mean, pstdev
from typing import Dict, List, Tuple


RESULTS_GLOB_DEFAULT = "results_*.json"


def parse_filename(path: str) -> Tuple[str, str]:
    """Parse results filename to extract (num, model).

    Expected format: results_{num}_{model}.json
    Returns (num_str, model_str)
    """
    base = os.path.basename(path)
    # Support both: results_{num}_{model}.json and results{num}_{model}.json
    m = re.match(r"results_?([^_]+)_(.+)\.json$", base)
    if not m:
        return ("", "")
    return m.group(1), m.group(2)


def collect_scores(files: List[str]) -> Dict[str, Dict]:
    """Collect scores grouped by model.

    Returns structure:
    {
      model: {
        'round_to_investor_all': {round_idx: [all investor->founder scores (flattened)]},
        'round_to_per_investor': {round_idx: {investor_name: [their scores to all founders]}},
        'files': [...]
      }
    }
    """
    data: Dict[str, Dict] = {}

    for path in files:
        _, model = parse_filename(path)
        if not model:
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                obj = json.load(f)
        except Exception:
            continue

        all_rounds = obj.get('all_rounds', [])

        model_entry = data.setdefault(model, {
            'round_to_investor_all': defaultdict(list),
            'round_to_per_investor': defaultdict(lambda: defaultdict(list)),
            'files': []
        })
        model_entry['files'].append(path)

        for rd in all_rounds:
            rnd = rd.get('round')
            all_scores = rd.get('all_scores', {})  # {investor: {founder: score}}
            if rnd is None or not all_scores:
                continue
            for investor_name, f_map in all_scores.items():
                for _, score in f_map.items():
                    try:
                        score_val = float(score)
                    except Exception:
                        continue
                    model_entry['round_to_investor_all'][rnd].append(score_val)
                    model_entry['round_to_per_investor'][rnd][investor_name].append(score_val)

    return data


def compute_stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {'mean': 0.0, 'std': 0.0, 'n': 0}
    if len(values) == 1:
        return {'mean': float(values[0]), 'std': 0.0, 'n': 1}
    return {
        'mean': float(mean(values)),
        'std': float(pstdev(values)),  # population std for across-file aggregation
        'n': len(values),
    }


def build_summary(per_model: Dict[str, Dict]) -> Dict[str, Dict]:
    summary: Dict[str, Dict] = {}
    for model, content in per_model.items():
        round_to_all = content['round_to_investor_all']
        round_to_inv = content['round_to_per_investor']
        model_sum = {
            'files_count': len(content.get('files', [])),
            'investor_overall_by_round': {},
            'per_investor_by_round': {},
        }
        # per-round overall (all investors' allocations flattened)
        for rnd, vals in sorted(round_to_all.items()):
            model_sum['investor_overall_by_round'][str(rnd)] = compute_stats(vals)
        # per-round per-investor
        for rnd, i_map in round_to_inv.items():
            model_sum['per_investor_by_round'][str(rnd)] = {}
            for investor_name, vals in i_map.items():
                model_sum['per_investor_by_round'][str(rnd)][investor_name] = compute_stats(vals)
        summary[model] = model_sum
    return summary


def print_summary(summary: Dict[str, Dict]):
    for model, s in summary.items():
        print(f"\n=== Model: {model} (files: {s.get('files_count', 0)}) ===")
        print("- Investors overall by round (flattened allocations):")
        for rnd, stats in sorted(s['investor_overall_by_round'].items(), key=lambda x: int(x[0])):
            print(f"  Round {rnd}: mean={stats['mean']:.2f}, std={stats['std']:.2f}, n={stats['n']}")
        print("- Per-investor across rounds:")
        # Collect full investor set
        per_inv = s['per_investor_by_round']
        all_investors = set()
        for _, imap in per_inv.items():
            all_investors.update(imap.keys())
        for iname in sorted(all_investors):
            print(f"  {iname}:")
            # Print rounds in order 1..N
            for rnd in sorted(per_inv.keys(), key=lambda x: int(x)):
                stats = per_inv[rnd].get(iname)
                if not stats:
                    continue
                print(f"    Round {rnd}: mean={stats['mean']:.2f}, std={stats['std']:.2f}, n={stats['n']}")


def write_per_model(summary: Dict[str, Dict]):
    for model, s in summary.items():
        out = f"summary_{model}.json"
        try:
            with open(out, 'w', encoding='utf-8') as f:
                json.dump(s, f, indent=2, ensure_ascii=False)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--glob', default='results*_ds.json', help='Glob for results files')
    args = parser.parse_args()

    files = glob.glob(args.glob)
    if not files:
        print("No results files matched.")
        return

    per_model = collect_scores(files)
    summary = build_summary(per_model)
    print_summary(summary)
    write_per_model(summary)


if __name__ == '__main__':
    main()


