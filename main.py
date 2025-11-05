"""
Main entry point for the Multi-Agent System.

This script demonstrates how to use the system with different configurations.
"""

from agents.founder import Founder
from agents.investor import Investor
from system.orchestrator import SystemOrchestrator
from config.default_config import DEFAULT_CONFIG
from utils.llm_client import LLMClient
from utils.dialog_logger import save_dialogs, reset_dialogs


def create_agents_from_config(config: dict):
    """
    Create agents from configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Tuple of (founders list, investors list)
    """
    founders = []
    for founder_config in config['founders']:
        founder = Founder(
            name=founder_config['name'],
            config={
                'specialization': founder_config['specialization'],
                'model': founder_config.get('model')
            }
        )
        founders.append(founder)
    
    investors = []
    for investor_config in config['investors']:
        investor = Investor(
            name=investor_config['name'],
            config={
                'criteria': investor_config['criteria'],
                'philosophy': investor_config['philosophy'],
                'model': investor_config.get('model')
            }
        )
        investors.append(investor)
    
    return founders, investors


def main():
    """Main function to run the multi-agent system."""
    
    # Reset dialog logs for new run
    reset_dialogs()
    
    # Load configuration
    config = DEFAULT_CONFIG.copy()
    
    # Create agents
    founders, investors = create_agents_from_config(config)
    
    # Set up LLM client
    llm_client = LLMClient(
        api_key=config['system']['api_key'],
        base_url=config['system']['base_url']
    )
    
    # Global temperature from config
    temperature = config['system'].get('temperature', 0.7)
    
    # Wrap client.generate to inject global temperature while allowing per-agent model
    def llm_callback(prompt, model=None):
        return llm_client.generate(prompt, model=model, temperature=temperature)
    # llm_callback = None  # Use placeholder responses for demo
    
    # Create orchestrator
    orchestrator = SystemOrchestrator(
        founders=founders,
        investors=investors,
        config=config['system'],
        llm_callback=llm_callback
    )
    
    # Run the system with a requirement
    requirement = config['instruction']
    
    results = orchestrator.run(requirement)
    
    # Save results
    with open('results_test_ds.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Save dialogs
    save_dialogs('dialogs_test_ds.json')
    
    print("\nResults saved to results.json")
    print("Dialogs saved to dialogs.json")
    
    return results


if __name__ == "__main__":
    main()

