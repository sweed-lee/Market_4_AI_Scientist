"""
Global dialog logger to capture all LLM prompt-response pairs.
"""

from typing import List, Dict, Any

# Global dialog storage
_dialogs: List[Dict[str, Any]] = []


def add_dialog(prompt: str, response: str, agent_name: str, agent_type: str, 
               round_num: int = None, dialog_type: str = None):
    """
    Add a prompt-response pair to the dialog log.
    
    Args:
        prompt: The input prompt
        response: The generated response
        agent_name: Name of the agent
        agent_type: Type of agent ('Founder' or 'Investor')
        round_num: Optional round number (major round)
        dialog_type: Optional dialog type (e.g., 'initial', 'iteration', 'round1_scoring', 'round2_evaluation')
    """
    dialog_entry = {
        'agent_name': agent_name,
        'agent_type': agent_type,
        'prompt': prompt,
        'response': response
    }
    if round_num is not None:
        dialog_entry['round_num'] = round_num
    if dialog_type:
        dialog_entry['dialog_type'] = dialog_type
    _dialogs.append(dialog_entry)


def get_all_dialogs() -> List[Dict[str, Any]]:
    """Get all logged dialogs."""
    return _dialogs


def reset_dialogs():
    """Clear all dialog logs."""
    global _dialogs
    _dialogs = []


def save_dialogs(filename: str = 'dialogs.json'):
    """
    Save all dialogs to a JSON file.
    
    Args:
        filename: Output filename
    """
    import json
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(_dialogs, f, indent=2, ensure_ascii=False)

