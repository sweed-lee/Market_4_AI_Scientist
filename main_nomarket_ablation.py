"""
Entry point for no-market ablation experiment.

Uses existing config format, but runs with:
- Founder proposal/refinement only
- Investor textual advice only
- No scoring/allocation/investment rounds
"""

from agents.founder_nomarket import FounderNoMarket
from agents.investor_nomarket import InvestorNoMarket, InvestorGroupNoMarket
from system.orchestrator_nomarket import SystemOrchestratorNoMarket
from config.config_20_founders_6groups_strategy import (
    CONFIG_20_FOUNDERS_6GROUPS_STRATEGY as CONFIG_NOMARKET,
)
from utils.llm_client import LLMClient
from utils.dialog_logger import save_dialogs, reset_dialogs


def create_agents_from_config(config: dict):
    founders = []
    for founder_config in config["founders"]:
        founders.append(
            FounderNoMarket(
                name=founder_config["name"],
                config={
                    "specialization": founder_config.get("specialization", ""),
                    "model": founder_config.get("model"),
                    "instruction": founder_config.get("instruction"),
                },
            )
        )

    investor_groups = []
    for group_cfg in config.get("investor_groups", []):
        investors = []
        for investor_config in group_cfg.get("investors", []):
            investors.append(
                InvestorNoMarket(
                    name=investor_config["name"],
                    config={
                        "criteria": investor_config.get("criteria", ""),
                        "philosophy": investor_config.get("philosophy", ""),
                        "model": investor_config.get("model"),
                    },
                )
            )
        investor_groups.append(InvestorGroupNoMarket(name=group_cfg["name"], investors=investors))

    return founders, investor_groups


def main():
    reset_dialogs()
    config = CONFIG_NOMARKET.copy()

    founders, investor_groups = create_agents_from_config(config)

    llm_client = LLMClient(
        api_key=config["system"]["api_key"],
        base_url=config["system"]["base_url"],
    )
    temperature = config["system"].get("temperature", 0.7)

    def llm_callback(prompt, model=None):
        return llm_client.generate(prompt, model=model, temperature=temperature)

    orchestrator = SystemOrchestratorNoMarket(
        founders=founders,
        investor_groups=investor_groups,
        config=config,
        llm_callback=llm_callback,
    )
    results = orchestrator.run()

    import json

    with open("results_nomarket_ablation_3.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    save_dialogs("dialogs_nomarket_ablation_3.json")

    print("\nResults saved to results_nomarket_ablation.json")
    print("Dialogs saved to dialogs_nomarket_ablation.json")
    return results


if __name__ == "__main__":
    main()

