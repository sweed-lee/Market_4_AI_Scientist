"""
Configuration with 25 founders and 6 investor groups by group strategy.

- 6 investor groups, each with 3 investors and total_capital 9000.
- Group strategy (each applied to 2 groups):
  - Conservative: prefer low-risk, steady-return projects x 2 groups
  - Balanced: balance risk and return x 2 groups
  - Aggressive: prefer high-risk, high-return projects x 2 groups
- Each investor's criteria and philosophy = original + group strategy.
- All founders and investors use model: USD-guiji/deepseek-v3.
- Founder count and tasks unchanged (25 founders, web game design).
"""

COMMON_INSTRUCTION = (
    "Design a small browser-based web game for casual players. "
    "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
)

MODEL = "USD-guiji/deepseek-v3"

# Base criteria/philosophy per investor role (same as original 3 roles)
INVESTOR_BASE = [
    {"criteria": "Innovation and novelty", "philosophy": "Focus on breakthrough ideas and creative solutions"},
    {"criteria": "Practical application and market fit", "philosophy": "Emphasize real-world applicability and market viability"},
    {"criteria": "Cost-effectiveness and feasibility", "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget"},
]

# Group strategy: (criteria_suffix, philosophy_suffix) for Conservative, Balanced, Aggressive
GROUP_STRATEGY = {
    "conservative": (
        " Group strategy: Conservative—prefer low-risk, steady-return projects.",
        " Group strategy: Conservative—prefer low-risk, stable-return projects; prioritize verifiable, executable proposals in evaluation.",
    ),
    "balanced": (
        " Group strategy: Balanced—balance risk and return.",
        " Group strategy: Balanced—balance risk and return; weigh both innovation and feasibility.",
    ),
    "aggressive": (
        " Group strategy: Aggressive—prefer high-risk, high-return projects.",
        " Group strategy: Aggressive—prefer high-risk, high-return projects; emphasize disruptive innovation and long-term potential.",
    ),
}


def _investor_config(group_idx: int, inv_idx: int, strategy_key: str) -> dict:
    base = INVESTOR_BASE[inv_idx]
    cs, ps = GROUP_STRATEGY[strategy_key]
    return {
        "name": f"Investor_{inv_idx + 1}_G{group_idx}",
        "criteria": base["criteria"] + cs,
        "philosophy": base["philosophy"] + ps,
        "model": MODEL,
    }


# 6 groups: Conservative x2, Balanced x2, Aggressive x2
GROUP_STRATEGY_ORDER = ["conservative", "conservative", "balanced", "balanced", "aggressive", "aggressive"]

ALL_INVESTOR_GROUPS = [f"InvestorGroup_{g}" for g in range(1, 7)]


def _founder_visible_founders(i: int) -> list:
    """Founder_i sees numerically adjacent founders (i-1, i+1) and Founder_1/Founder_25 see each other."""
    out = []
    if i > 1:
        out.append(f"Founder_{i - 1}")
    else:
        out.append("Founder_25")
    if i < 25:
        out.append(f"Founder_{i + 1}")
    else:
        out.append("Founder_1")
    return out


CONFIG_25_FOUNDERS_6GROUPS_STRATEGY = {
    "system": {
        "num_rounds": 10,
        "max_investor_points": 100,
        "temperature": 0.7,
        "budget_tolerance_percent": 0.2,
        "max_investment_rounds": 3,
        "max_allocation_retries": 3,
        "enable_checkpoints": True,
        "checkpoint_dir": "checkpoints_stategy",
        "base_url": "http://35.220.164.252:3888/v1/",
        "api_key": "",
    },
    "founders": [
        {"name": f"Founder_{i}", "specialization": "Web Game", "model": MODEL, "instruction": COMMON_INSTRUCTION}
        for i in range(1, 26)
    ],
    "investor_groups": [
        {
            "name": f"InvestorGroup_{g}",
            "total_capital": 9000,
            "k_selection": 10,
            "investors": [_investor_config(g, i, GROUP_STRATEGY_ORDER[g - 1]) for i in range(3)],
        }
        for g in range(1, 7)
    ],
    "interaction_graphs": {
        "sparse": {
            **{
                f"Founder_{i}": _founder_visible_founders(i) + ALL_INVESTOR_GROUPS
                for i in range(1, 26)
            },
            "InvestorGroup_1": [f"Founder_{i}" for i in range(1, 26)],
            "InvestorGroup_2": [f"Founder_{i}" for i in range(1, 26)],
            "InvestorGroup_3": [f"Founder_{i}" for i in range(1, 26)],
            "InvestorGroup_4": [f"Founder_{i}" for i in range(1, 26)],
            "InvestorGroup_5": [f"Founder_{i}" for i in range(1, 26)],
            "InvestorGroup_6": [f"Founder_{i}" for i in range(1, 26)],
        }
    },
    "graph_mode": "sparse",
}
