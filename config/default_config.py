"""
Default configuration for the multi-agent system.

This configuration can be easily extended or modified.
"""

DEFAULT_CONFIG = {
    "system": {
        "num_rounds": 3,
        "max_investor_points": 100,
        "temperature": 0.7,
        "base_url": "https://api.deepseek.com/v1",
        "api_key": "xxx"
    },
    "instruction" : "Create a personalized home page for a deep learning scientist. This task should be manageable for a single LLM agent specializing in web development.",
    "founders": [
        {
            "name": "Founder_A",
            "specialization": "Balanced",
            "model": "deepseek-chat"
        },
        {
            "name": "Founder_B",
            "specialization": "Balanced",
            "model": "deepseek-chat"
        },
        {
            "name": "Founder_C",
            "specialization": "Balanced",
            "model": "deepseek-chat"
        },
    ],
    "investors": [
        {
            "name": "Investor_1",
            "criteria": "Innovation and novelty",
            "philosophy": "Focus on breakthrough ideas and creative solutions",
            "model": "deepseek-chat"
        },
        {
            "name": "Investor_2",
            "criteria": "Practical application and market fit",
            "philosophy": "Emphasize real-world applicability and market viability",
            "model": "deepseek-chat"
        },
        {
            "name": "Investor_3",
            "criteria": "Cost-effectiveness and feasibility",
            "philosophy": "Check for exaggerated and unrealistic statements and its implementation costs",
            "model": "deepseek-chat"
        },
    ],
}

# gpt-5
# USD-guiji/deepseek-v3
# Qwen/Qwen3-235B-A22B
# deepseek-chat