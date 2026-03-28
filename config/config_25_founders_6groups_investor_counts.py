"""
Configuration with 25 founders and 6 investor groups (varying investor counts).

- 25 founders (unchanged), all use model: USD-guiji/deepseek-v3.
- 6 investor groups, each with total_capital 9000.
- Investor counts by group (2 groups each):
  - 1 investor: Balanced-only session (single balanced evaluator)
  - 3 investors: same 3 specializations as the original config
  - 6 investors: same 3 specializations, but each specialization doubled (2x per type)
"""

COMMON_INSTRUCTION = (
    "Design a small browser-based web game for casual players. "
    "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. "
    "Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
)

MODEL = "USD-guiji/deepseek-v3"

# Original 3 investor roles (specializations)
INVESTOR_ROLES = [
    {
        "role": "innovation",
        "criteria": "Innovation and novelty",
        "philosophy": "Focus on breakthrough ideas and creative solutions",
    },
    {
        "role": "market_fit",
        "criteria": "Practical application and market fit",
        "philosophy": "Emphasize real-world applicability and market viability",
    },
    {
        "role": "feasibility",
        "criteria": "Cost-effectiveness and feasibility",
        "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget",
    },
]

BALANCED_INVESTOR = {
    "role": "balanced",
    "criteria": "Balanced evaluation (innovation, market fit, feasibility)",
    "philosophy": (
        "Weigh novelty, market viability, and implementation feasibility evenly; "
        "avoid extreme preferences; be consistent and evidence-driven."
    ),
}


def _founder_visible_founders(i: int) -> list:
    """Founder_i sees numerically adjacent founders (i-1, i+1), with wrap-around between 1 and 25."""
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


def _make_investor(name: str, role_cfg: dict) -> dict:
    return {
        "name": name,
        "criteria": role_cfg["criteria"],
        "philosophy": role_cfg["philosophy"],
        "model": MODEL,
    }


def _investors_for_group(group_idx: int, investor_count: int) -> list:
    """
    Build investors list for a group.

    - 1 investor: single balanced evaluator
    - 3 investors: original 3 roles
    - 6 investors: original 3 roles, duplicated (2 per role)
    """
    if investor_count == 1:
        return [_make_investor(f"Investor_Balanced_G{group_idx}", BALANCED_INVESTOR)]

    if investor_count == 3:
        return [
            _make_investor(f"Investor_{i + 1}_G{group_idx}", role_cfg)
            for i, role_cfg in enumerate(INVESTOR_ROLES)
        ]

    if investor_count == 6:
        investors = []
        for i, role_cfg in enumerate(INVESTOR_ROLES, start=1):
            investors.append(_make_investor(f"Investor_{i}_A_G{group_idx}", role_cfg))
            investors.append(_make_investor(f"Investor_{i}_B_G{group_idx}", role_cfg))
        return investors

    raise ValueError(f"Unsupported investor_count={investor_count}. Expected one of: 1, 3, 6.")


# 6 groups total: two groups each of size 1, 3, 6 investors
GROUP_INVESTOR_COUNTS = [1, 1, 3, 3, 6, 6]
ALL_INVESTOR_GROUPS = [f"InvestorGroup_{g}" for g in range(1, 7)]


CONFIG_25_FOUNDERS_6GROUPS_INVESTOR_COUNTS = {
    "system": {
        "num_rounds": 10,
        "max_investor_points": 100,
        "temperature": 0.7,
        "budget_tolerance_percent": 0.2,
        "max_investment_rounds": 3,
        "max_allocation_retries": 3,
        "step2_debate_rounds": 2,
        "enable_checkpoints": True,
        "checkpoint_dir": "checkpoints_investor_counts",
        "base_url": "http://35.220.164.252:3888/v1/",
        "api_key": "",
    },
    "founders": [
        {
            "name": f"Founder_{i}",
            "specialization": "Web Game",
            "model": MODEL,
            "instruction": COMMON_INSTRUCTION,
        }
        for i in range(1, 26)
    ],
    "investor_groups": [
        {
            "name": f"InvestorGroup_{g}",
            "total_capital": 9000,
            "k_selection": 10,
            "investors": _investors_for_group(g, GROUP_INVESTOR_COUNTS[g - 1]),
        }
        for g in range(1, 7)
    ],
    "interaction_graphs": {
        "sparse": {
            **{f"Founder_{i}": _founder_visible_founders(i) + ALL_INVESTOR_GROUPS for i in range(1, 26)},
            **{f"InvestorGroup_{g}": [f"Founder_{i}" for i in range(1, 26)] for g in range(1, 7)},
        }
    },
    "graph_mode": "sparse",
}
