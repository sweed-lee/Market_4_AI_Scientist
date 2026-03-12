"""
Configuration with 25 founders and 5 investor groups by task-aligned strategy.

- 5 investor groups, each with 3 investors and total_capital 9000.
- 25 founders, divided into 5 task-aligned clusters (5 founders per cluster).
- Each investor group and each founder cluster share one of the following 5 web-app task preferences:
  1. Games
  2. Lightweight Utility Apps
  3. Strongly Social Applications
  4. Lifestyle Applications
  5. AI Applications
- GROUP_STRATEGY controls investor-group preference.
- COMMON_INSTRUCTION and founder specialization/instruction reflect founder preference.
- All founders and investors use model: USD-guiji/deepseek-v3.
"""

MODEL = "USD-guiji/deepseek-v3"

TASKS = {
    "games": {
        "label": "Games",
        "common_instruction": (
            "Design a small browser-based web game for casual players. "
            "The web app should emphasize entertainment, playful interaction, fun, challenge, "
            "and short-session engagement. "
            "The rules and graphics should remain simple enough for a single LLM agent to implement "
            "within a limited time budget. Do not call external network resources. Ensure the function "
            "can be implemented without LLM accessing external networks."
        ),
        "founder_specialization": "Game Web App",
        "founder_suffix": (
            " Focus on entertainment value, intuitive gameplay, simple mechanics, "
            "and replayable short-session interaction."
        ),
        "investor_suffix_criteria": (
            " Group preference: Games—prioritize entertainment value, engaging mechanics, "
            "clarity of gameplay loop, and replayability."
        ),
        "investor_suffix_philosophy": (
            " Group preference: Games—favor proposals that can quickly deliver fun, polished, "
            "and understandable browser-based play experiences."
        ),
    },
    "utility": {
        "label": "Lightweight Utility Apps",
        "common_instruction": (
            "Design a small browser-based utility web app. "
            "The web app should accomplish a specific practical task quickly and clearly, "
            "with value centered on usefulness, convenience, and low-friction operation. "
            "The function and interface should remain simple enough for a single LLM agent to implement "
            "within a limited time budget. Do not call external network resources. Ensure the function "
            "can be implemented without LLM accessing external networks."
        ),
        "founder_specialization": "Utility Web App",
        "founder_suffix": (
            " Focus on practical usefulness, clarity, speed, convenience, and low-friction interaction."
        ),
        "investor_suffix_criteria": (
            " Group preference: Lightweight Utility Apps—prioritize usefulness, task clarity, "
            "efficiency, and ease of use."
        ),
        "investor_suffix_philosophy": (
            " Group preference: Lightweight Utility Apps—favor proposals that solve one concrete problem "
            "well with minimal complexity and smooth interaction."
        ),
    },
    "social": {
        "label": "Strongly Social Applications",
        "common_instruction": (
            "Design a small browser-based social web app. "
            "The web app's core experience should depend on real-time or ongoing interaction among real users, "
            "where social exchange and user-to-user dynamics are central to the product experience. "
            "Keep the feature scope simple enough for a single LLM agent to implement within a limited time budget. "
            "Do not call external network resources. Ensure the function can be implemented without LLM accessing "
            "external networks."
        ),
        "founder_specialization": "Social Web App",
        "founder_suffix": (
            " Focus on meaningful real-user interaction, participation incentives, organic engagement, "
            "and simple but effective social mechanics."
        ),
        "investor_suffix_criteria": (
            " Group preference: Strongly Social Applications—prioritize interaction quality, "
            "social dynamics, user engagement, and participatory design."
        ),
        "investor_suffix_philosophy": (
            " Group preference: Strongly Social Applications—favor proposals where the product value "
            "emerges from authentic user-to-user interaction rather than isolated single-user utility."
        ),
    },
    "lifestyle": {
        "label": "Lifestyle Applications",
        "common_instruction": (
            "Design a small browser-based lifestyle web app. "
            "The web app should support everyday personal needs and routines, including organization, "
            "self-management, planning, tracking, and other daily-life functions. "
            "Keep the feature scope simple enough for a single LLM agent to implement within a limited time budget. "
            "Do not call external network resources. Ensure the function can be implemented without LLM accessing "
            "external networks."
        ),
        "founder_specialization": "Lifestyle Web App",
        "founder_suffix": (
            " Focus on everyday usefulness, routine support, intuitive workflows, and personal organization."
        ),
        "investor_suffix_criteria": (
            " Group preference: Lifestyle Applications—prioritize day-to-day usefulness, user friendliness, "
            "habit support, and practical value in daily routines."
        ),
        "investor_suffix_philosophy": (
            " Group preference: Lifestyle Applications—favor proposals that fit naturally into everyday life "
            "and provide sustainable personal value through simple interactions."
        ),
    },
    "ai": {
        "label": "AI Applications",
        "common_instruction": (
            "Design a small browser-based AI web app. "
            "The web app's main value should lie in generative AI capabilities, especially for creating, "
            "transforming, summarizing, or assisting with content through AI-driven interaction. "
            "Keep the product simple enough for a single LLM agent to implement within a limited time budget. "
            "Do not call external network resources. Ensure the function can be implemented without LLM accessing "
            "external networks."
        ),
        "founder_specialization": "AI Web App",
        "founder_suffix": (
            " Focus on clear AI-assisted value, intuitive prompting flow, useful generation quality, "
            "and simple human-AI interaction."
        ),
        "investor_suffix_criteria": (
            " Group preference: AI Applications—prioritize meaningful generative-AI value, interaction quality, "
            "output usefulness, and product clarity."
        ),
        "investor_suffix_philosophy": (
            " Group preference: AI Applications—favor proposals that use generative AI as the core product engine "
            "rather than as a superficial add-on."
        ),
    },
}

# Five investor groups, one per task
GROUP_STRATEGY = {
    "InvestorGroup_1": "games",
    "InvestorGroup_2": "utility",
    "InvestorGroup_3": "social",
    "InvestorGroup_4": "lifestyle",
    "InvestorGroup_5": "ai",
}

# Founder blocks: each 5 founders share one task
FOUNDER_TASK_MAP = {
    **{f"Founder_{i}": "games" for i in range(1, 6)},
    **{f"Founder_{i}": "utility" for i in range(6, 11)},
    **{f"Founder_{i}": "social" for i in range(11, 16)},
    **{f"Founder_{i}": "lifestyle" for i in range(16, 21)},
    **{f"Founder_{i}": "ai" for i in range(21, 26)},
}

# Base criteria/philosophy per investor role
INVESTOR_BASE = [
    {"criteria": "Innovation and novelty", "philosophy": "Focus on breakthrough ideas and creative solutions"},
    {"criteria": "Practical application and market fit", "philosophy": "Emphasize real-world applicability and market viability"},
    {"criteria": "Cost-effectiveness and feasibility", "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget"},
]


def _investor_config(group_name: str, inv_idx: int) -> dict:
    base = INVESTOR_BASE[inv_idx]
    task_key = GROUP_STRATEGY[group_name]
    task_cfg = TASKS[task_key]
    return {
        "name": f"Investor_{inv_idx + 1}_{group_name}",
        "criteria": base["criteria"] + task_cfg["investor_suffix_criteria"],
        "philosophy": base["philosophy"] + task_cfg["investor_suffix_philosophy"],
        "model": MODEL,
    }


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


ALL_INVESTOR_GROUPS = [f"InvestorGroup_{g}" for g in range(1, 6)]

CONFIG_25_FOUNDERS_5GROUPS_TASK_ALIGNED = {
    "system": {
        "num_rounds": 10,
        "max_investor_points": 100,
        "temperature": 0.7,
        "budget_tolerance_percent": 0.2,
        "max_investment_rounds": 3,
        "max_allocation_retries": 3,
        "enable_checkpoints": True,
        "checkpoint_dir": "checkpoints_strategy_5groups",
        "base_url": "http://35.220.164.252:3888/v1/",
        "api_key": "",
    },
    "founders": [
        {
            "name": f"Founder_{i}",
            "specialization": TASKS[FOUNDER_TASK_MAP[f"Founder_{i}"]]["founder_specialization"],
            "model": MODEL,
            "instruction": (
                TASKS[FOUNDER_TASK_MAP[f"Founder_{i}"]]["common_instruction"]
                + TASKS[FOUNDER_TASK_MAP[f"Founder_{i}"]]["founder_suffix"]
            ),
        }
        for i in range(1, 26)
    ],
    "investor_groups": [
        {
            "name": group_name,
            "total_capital": 9000,
            "k_selection": 10,
            "investors": [_investor_config(group_name, i) for i in range(3)],
        }
        for group_name in ALL_INVESTOR_GROUPS
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
        }
    },
    "graph_mode": "sparse",
}