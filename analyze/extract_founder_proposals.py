"""
Extract each founder's title and proposal information for each round.

Saves to results/ directory, one JSON file per founder.
"""

import json
from pathlib import Path
from collections import defaultdict

def load_results(filepath):
    """Load results from JSON file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_founder_proposals(results, output_dir='results'):
    """
    Extract title and proposal for each founder in each round.
    
    Args:
        results: Loaded JSON results
        output_dir: Output directory for JSON files
    """
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Collect data: {founder_name: [round_data, ...]}
    founder_data = defaultdict(list)
    
    # Process each major round
    for round_data in results['all_rounds']:
        major_round = round_data['round']
        
        # Get titles and proposals
        titles = round_data.get('titles', {})
        proposals = round_data.get('proposals', {})
        budgets = round_data.get('budgets', {})
        
        # Collect data for each founder
        all_founders = set(titles.keys()) | set(proposals.keys())
        
        for founder_name in all_founders:
            round_info = {
                'major_round': major_round,
                'title': titles.get(founder_name, ''),
                'proposal': proposals.get(founder_name, ''),
                'budget': budgets.get(founder_name, 0)
            }
            
            founder_data[founder_name].append(round_info)
    
    # Sort rounds for each founder
    for founder_name in founder_data:
        founder_data[founder_name].sort(key=lambda x: x['major_round'])
    
    # Save to JSON files
    for founder_name, rounds in founder_data.items():
        output_file = output_path / f"{founder_name}.json"
        
        output_json = {
            'founder_name': founder_name,
            'total_rounds': len(rounds),
            'rounds': rounds
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_json, f, indent=2, ensure_ascii=False)
        
        print(f"Saved: {output_file} ({len(rounds)} rounds)")

def main():
    """Main function."""
    import sys
    
    # Default filepath
    filepath = 'results_10_founders.json'
    
    # Check if filepath is provided as argument
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    
    if not Path(filepath).exists():
        print(f"Error: {filepath} not found!")
        print(f"Usage: python {sys.argv[0]} [results_file.json]")
        return
    
    print(f"Loading results from {filepath}...")
    results = load_results(filepath)
    
    print("\nExtracting founder proposals...")
    print("=" * 60)
    
    extract_founder_proposals(results)
    
    print("\n" + "=" * 60)
    print("Extraction completed!")

if __name__ == '__main__':
    main()

