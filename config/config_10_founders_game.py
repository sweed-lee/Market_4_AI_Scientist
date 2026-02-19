"""
Configuration with 25 founders and 4 investor groups.

Each founder has its own task/instruction:
  - 4 founders: personal homepage creation
  - 3 founders: web service/application design
  - 3 founders: web game design
All tasks are explicitly scoped to be feasible for a single LLM agent
within a limited amount of time.

The interaction graph is sparse:
  - Each founder is connected to exactly 2 other founders.
  - Each investor_group is connected to all founders (and vice versa).
"""

CONFIG_10_FOUNDERS = {
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
        "base_url": "https://api.deepseek.com",
        # "api_key": "",# boyu
        "api_key": "", #ds
    },
    "founders": [
        # Personal homepage (4)
        {
            "name": "Founder_1",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_2",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_3",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_4",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        # Web service / application (3)
        {
            "name": "Founder_5",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_6",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_7",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        # Web game (3)
        {
            "name": "Founder_8",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_9",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_10",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_11",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_12",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_13",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_14",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_15",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_16",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_17",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_18",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_19",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_20",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_21",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_22",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_23",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_24",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
        {
            "name": "Founder_25",
            "specialization": "Web Game",
            "model": "deepseek-chat",
            "instruction": (
                "Design a small browser-based web game for casual players. "
                "The rules and graphics should remain simple enough for a single LLM agent to implement within a limited time budget. Do not call external network resources. Ensure the function can be implemented without LLM accessing external networks."
            ),
        },
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
                    "model": "deepseek-chat",
                },
                {
                    "name": "Investor_2_G1",
                    "criteria": "Practical application and market fit",
                    "philosophy": "Emphasize real-world applicability and market viability",
                    "model": "deepseek-chat",
                },
                {
                    "name": "Investor_3_G1",
                    "criteria": "Cost-effectiveness and feasibility",
                    "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget",
                    "model": "deepseek-chat",
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
                    "model": "deepseek-chat",
                },
                {
                    "name": "Investor_2_G2",
                    "criteria": "Practical application and market fit",
                    "philosophy": "Emphasize real-world applicability and market viability",
                    "model": "deepseek-chat",
                },
                {
                    "name": "Investor_3_G2",
                    "criteria": "Cost-effectiveness and feasibility",
                    "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget",
                    "model": "deepseek-chat",
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
                    "model": "deepseek-chat",
                },
                {
                    "name": "Investor_2_G3",
                    "criteria": "Practical application and market fit",
                    "philosophy": "Emphasize real-world applicability and market viability",
                    "model": "deepseek-chat",
                },
                {
                    "name": "Investor_3_G3",
                    "criteria": "Cost-effectiveness and feasibility",
                    "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget",
                    "model": "deepseek-chat",
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
                    "model": "deepseek-chat",
                },
                {
                    "name": "Investor_2_G4",
                    "criteria": "Practical application and market fit",
                    "philosophy": "Emphasize real-world applicability and market viability",
                    "model": "deepseek-chat",
                },
                {
                    "name": "Investor_3_G4",
                    "criteria": "Cost-effectiveness and feasibility",
                    "philosophy": "Check for exaggerated and unrealistic statements and unreasonable implementation budget",
                    "model": "deepseek-chat",
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


