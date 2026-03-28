"""
Entry point for running the system with 10 founders and 4 investor groups.

Uses CONFIG_10_FOUNDERS from config.config_10_founders.
"""

from agents.founder import Founder
from agents.investor import Investor, InvestorGroup
from system.orchestrator import SystemOrchestrator
from config.config_25_founders_6groups_investor_counts import CONFIG_25_FOUNDERS_6GROUPS_INVESTOR_COUNTS as CONFIG_10_FOUNDERS
from utils.llm_client import LLMClient
from utils.dialog_logger import save_dialogs, reset_dialogs


def create_agents_from_config(config: dict):
    """
    Create agents from configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Tuple of (founders list, investor_groups list)
    """
    founders = []
    for founder_config in config["founders"]:
        founder = Founder(
            name=founder_config["name"],
            config={
                "specialization": founder_config["specialization"],
                "model": founder_config.get("model"),
                "instruction": founder_config.get("instruction"),
            },
        )
        founders.append(founder)

    # Build investor groups from configuration. Each group contains several
    # individual investors, and the group will aggregate their scores.
    investor_groups = []
    for group_cfg in config.get("investor_groups", []):
        investors = []
        for investor_config in group_cfg.get("investors", []):
            investor = Investor(
                name=investor_config["name"],
                config={
                    "criteria": investor_config["criteria"],
                    "philosophy": investor_config["philosophy"],
                    "model": investor_config.get("model"),
                },
            )
            investors.append(investor)
        total_capital = group_cfg.get("total_capital", 100.0)  # Default 100.0 if not specified
        # Group-local k selection (new system). Keep backward compatibility with older configs.
        k_selection = group_cfg.get("k_selection", config.get("system", {}).get("k_selection", None))
        round1_max_workers = group_cfg.get("round1_max_workers", None)
        step2_debate_rounds = group_cfg.get(
            "step2_debate_rounds",
            config.get("system", {}).get("step2_debate_rounds", 0),
        )
        investor_group = InvestorGroup(
            name=group_cfg["name"], 
            investors=investors,
            total_capital=total_capital,
            k_selection=k_selection,
            round1_max_workers=round1_max_workers,
            step2_debate_rounds=step2_debate_rounds,
        )
        investor_groups.append(investor_group)

    return founders, investor_groups


def main():
    """Main function to run the multi-agent system with 10 founders."""

    # Reset dialog logs for new run
    reset_dialogs()

    # Load configuration
    config = CONFIG_10_FOUNDERS.copy()

    # Create agents
    founders, investor_groups = create_agents_from_config(config)

    # Set up LLM client
    llm_client = LLMClient(
        api_key=config["system"]["api_key"],
        base_url=config["system"]["base_url"],
    )

    # Global temperature from config
    temperature = config["system"].get("temperature", 0.7)

    # Wrap client.generate to inject global temperature while allowing per-agent model
    def llm_callback(prompt, model=None):
        return llm_client.generate(prompt, model=model, temperature=temperature)
    # llm_callback = None  # Use placeholder responses for demo

    # Create orchestrator
    orchestrator = SystemOrchestrator(
        founders=founders,
        investor_groups=investor_groups,
        config=config,
        llm_callback=llm_callback,
    )

    # Run the system (each founder uses its own requirement/instruction)
    results = orchestrator.run()

    # Save results
    with open("results_25_founders_6groups_investor_counts.json", "w", encoding="utf-8") as f:
        import json

        json.dump(results, f, indent=2, ensure_ascii=False)

    # Save dialogs
    save_dialogs("dialogs_25_founders_6groups_investor_counts.json")

    print("\nResults saved to results_25_founders_6groups_investor_counts.json")
    print("Dialogs saved to dialogs_25_founders_6groups_investor_counts.json")

    return results


if __name__ == "__main__":
    main()

