"""
Configuration with 25 founders and 4 investor groups.

Model distribution:
  - 25 founders: 7 use USD-guiji/deepseek-v3, 6 use qwen-plus,
    6 use gpt-4o, 6 use gemini-3-flash-preview
  - 4 investor groups: each uses one of the above models

Each founder has its own task/instruction:
  - Web game design (all 25)
All tasks are explicitly scoped to be feasible for a single LLM agent
within a limited amount of time.

The interaction graph is sparse:
  - Each founder is connected to exactly 2 other founders.
  - Each investor_group is connected to all founders (and vice versa).
"""

FOUNDER_MODELS = [
    "USD-guiji/deepseek-v3",   # 7 founders (1-7)
    "USD-guiji/deepseek-v3",
    "USD-guiji/deepseek-v3",
    "USD-guiji/deepseek-v3",
    "USD-guiji/deepseek-v3",
    "USD-guiji/deepseek-v3",
    "USD-guiji/deepseek-v3",
    "qwen-plus",               # 6 founders (8-13)
    "qwen-plus",
    "qwen-plus",
    "qwen-plus",
    "qwen-plus",
    "qwen-plus",
    "gpt-4o",                  # 6 founders (14-19)
    "gpt-4o",
    "gpt-4o",
    "gpt-4o",
    "gpt-4o",
    "gpt-4o",
    "gemini-3-flash-preview",  # 6 founders (20-25)
    "gemini-3-flash-preview",
    "gemini-3-flash-preview",
    "gemini-3-flash-preview",
    "gemini-3-flash-preview",
    "gemini-3-flash-preview",
]

INVESTOR_GROUP_MODELS = [
    "USD-guiji/deepseek-v3",
    "qwen-plus",
    "gpt-4o",
    "gemini-3-flash-preview",
]

COMMON_INSTRUCTION = (
    "Design a small browser-based web game for casual players. "
    "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
)

CONFIG_25_FOUNDERS_MULTIMODEL = {
    "system": {
        "num_rounds": 10,
        "max_investor_points": 100,
        "temperature": 0.7,
        # Budget tolerance percentage for founder budgets (e.g., 0.1 = 10%)
        "budget_tolerance_percent": 0.2,
        # Maximum number of investment rounds per evaluation
        "max_investment_rounds": 3,
        # Max retries for investor allocation when validation fails (e.g., total != budget)
        "max_allocation_retries": 3,
        # === Checkpointing (optional) ===
        # Save two checkpoints per major round:
        # - founder_submitted: after founders submit, before investor evaluation
        # - investor_evaluated: after investor evaluation, before next major round
        "enable_checkpoints": True,
        "checkpoint_dir": "checkpoints",
        # "base_url": "https://api.deepseek.com",
        "base_url": "http://35.220.164.252:3888/v1/",
        "api_key": "",# boyu
        # "api_key": "", #ds
    },
    "founders": [
        {
            "name": f"Founder_{i}",
            "specialization": "Web Game",
            "model": FOUNDER_MODELS[i - 1],
            "instruction": COMMON_INSTRUCTION,
        }
        for i in range(1, 26)
    ],
    "investor_groups": [
        {
            "name": "InvestorGroup_1",
            "total_capital": 12000,  # Total capital for this investor group (1M tokens)
            # Group-local top-k selection (new system)
            "k_selection": 10,
            "investors": [
                {
                    "name": "Investor_1_G1",
                    "criteria": "Innovation and novelty",
                    "philosophy": "Focus on breakthrough ideas and creative solutions",
                    "model": INVESTOR_GROUP_MODELS[0],
                },
                {
                    "name": "Investor_2_G1",
                    "criteria": "Practical application and market fit",
                    "philosophy": "Emphasize real-world applicability and market viability",
                    "model": INVESTOR_GROUP_MODELS[0],
                },
                {
                    "name": "Investor_3_G1",
                    "criteria": "Cost-effectiveness and feasibility",
                    "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget",
                    "model": INVESTOR_GROUP_MODELS[0],
                },
            ],
        },
        {
            "name": "InvestorGroup_2",
            "total_capital": 12000,  # Total capital for this investor group (1M tokens)
            # Group-local top-k selection (new system)
            "k_selection": 10,
            "investors": [
                {
                    "name": "Investor_1_G2",
                    "criteria": "Innovation and novelty",
                    "philosophy": "Focus on breakthrough ideas and creative solutions",
                    "model": INVESTOR_GROUP_MODELS[1],
                },
                {
                    "name": "Investor_2_G2",
                    "criteria": "Practical application and market fit",
                    "philosophy": "Emphasize real-world applicability and market viability",
                    "model": INVESTOR_GROUP_MODELS[1],
                },
                {
                    "name": "Investor_3_G2",
                    "criteria": "Cost-effectiveness and feasibility",
                    "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget",
                    "model": INVESTOR_GROUP_MODELS[1],
                },
            ],
        },
        {
            "name": "InvestorGroup_3",
            "total_capital": 12000,  # Total capital for this investor group (1M tokens)
            # Group-local top-k selection (new system)
            "k_selection": 10,
            "investors": [
                {
                    "name": "Investor_1_G3",
                    "criteria": "Innovation and novelty",
                    "philosophy": "Focus on breakthrough ideas and creative solutions",
                    "model": INVESTOR_GROUP_MODELS[2],
                },
                {
                    "name": "Investor_2_G3",
                    "criteria": "Practical application and market fit",
                    "philosophy": "Emphasize real-world applicability and market viability",
                    "model": INVESTOR_GROUP_MODELS[2],
                },
                {
                    "name": "Investor_3_G3",
                    "criteria": "Cost-effectiveness and feasibility",
                    "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget",
                    "model": INVESTOR_GROUP_MODELS[2],
                },
            ],
        },
        {
            "name": "InvestorGroup_4",
            "total_capital": 12000,  # Total capital for this investor group (1M tokens)
            # Group-local top-k selection (new system)
            "k_selection": 10,
            "investors": [
                {
                    "name": "Investor_1_G4",
                    "criteria": "Innovation and novelty",
                    "philosophy": "Focus on breakthrough ideas and creative solutions",
                    "model": INVESTOR_GROUP_MODELS[3],
                },
                {
                    "name": "Investor_2_G4",
                    "criteria": "Practical application and market fit",
                    "philosophy": "Emphasize real-world applicability and market viability",
                    "model": INVESTOR_GROUP_MODELS[3],
                },
                {
                    "name": "Investor_3_G4",
                    "criteria": "Cost-effectiveness and feasibility",
                    "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget",
                    "model": INVESTOR_GROUP_MODELS[3],
                },
            ],
        },
    ],

    # Sparse interaction graph: each founder connects to 2 other founders,
    # each investor_group connects to 4 founders (and vice versa).
    "interaction_graphs": {
        "sparse": {
            # Founder-founder edges (each founder has 2 neighbors)
            "Founder_1": ["Founder_2", "Founder_3", "InvestorGroup_1","InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_2": ["Founder_1", "Founder_4", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_3": ["Founder_1", "Founder_5", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_4": ["Founder_2", "Founder_6", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_5": ["Founder_3", "Founder_7", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_6": ["Founder_4", "Founder_8", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_7": ["Founder_5", "Founder_9", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_8": ["Founder_6", "Founder_10", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_9": ["Founder_7", "Founder_10", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_10": ["Founder_8", "Founder_9", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_11": ["Founder_12", "Founder_13", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_12": ["Founder_11", "Founder_14", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_13": ["Founder_11", "Founder_15", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_14": ["Founder_12", "Founder_16", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_15": ["Founder_13", "Founder_17", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_16": ["Founder_14", "Founder_18", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_17": ["Founder_15", "Founder_19", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_18": ["Founder_16", "Founder_20", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_19": ["Founder_17", "Founder_20", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_20": ["Founder_18", "Founder_19", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_21": ["Founder_22", "Founder_20", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_22": ["Founder_21", "Founder_24", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_23": ["Founder_21", "Founder_25", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_24": ["Founder_22", "Founder_25", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],
            "Founder_25": ["Founder_1", "Founder_24", "InvestorGroup_1", "InvestorGroup_2", "InvestorGroup_3", "InvestorGroup_4",],

            # Investor-group to founders (each with all 25 founders)
            "InvestorGroup_1": ["Founder_1", "Founder_2", "Founder_3", "Founder_4", "Founder_5", "Founder_6", "Founder_7", "Founder_8", "Founder_9", "Founder_10", "Founder_11", "Founder_12", "Founder_13", "Founder_14", "Founder_15", "Founder_16", "Founder_17", "Founder_18", "Founder_19", "Founder_20", "Founder_21", "Founder_22", "Founder_23", "Founder_24", "Founder_25"],
            "InvestorGroup_2": ["Founder_1", "Founder_2", "Founder_3", "Founder_4", "Founder_5", "Founder_6", "Founder_7", "Founder_8", "Founder_9", "Founder_10", "Founder_11", "Founder_12", "Founder_13", "Founder_14", "Founder_15", "Founder_16", "Founder_17", "Founder_18", "Founder_19", "Founder_20", "Founder_21", "Founder_22", "Founder_23", "Founder_24", "Founder_25"],
            "InvestorGroup_3": ["Founder_1", "Founder_2", "Founder_3", "Founder_4", "Founder_5", "Founder_6", "Founder_7", "Founder_8", "Founder_9", "Founder_10", "Founder_11", "Founder_12", "Founder_13", "Founder_14", "Founder_15", "Founder_16", "Founder_17", "Founder_18", "Founder_19", "Founder_20", "Founder_21", "Founder_22", "Founder_23", "Founder_24", "Founder_25"],
            "InvestorGroup_4": ["Founder_1", "Founder_2", "Founder_3", "Founder_4", "Founder_5", "Founder_6", "Founder_7", "Founder_8", "Founder_9", "Founder_10", "Founder_11", "Founder_12", "Founder_13", "Founder_14", "Founder_15", "Founder_16", "Founder_17", "Founder_18", "Founder_19", "Founder_20", "Founder_21", "Founder_22", "Founder_23", "Founder_24", "Founder_25"],
        }
    },
    "graph_mode": "sparse",
}
