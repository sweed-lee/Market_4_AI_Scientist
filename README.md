# Multi-Agent System: Founder-Investor Framework

A multi-agent competitive system based on Large Language Models (LLMs) that simulates the complete process of founders proposing strategies and investors evaluating and allocating investments.

## Overview

This system implements a multi-round competitive framework:
- **Founders**: Propose initial strategies based on task requirements and iteratively optimize based on investor feedback
- **Investors**: Evaluate all strategies, allocate investment scores, and provide detailed feedback
- **Multi-round Iteration**: Through multiple rounds of competition, strategies are continuously refined, and the optimal solution is selected

## Project Structure

```
market4science/
├── agents/                    # Agent modules
│   ├── __init__.py
│   ├── base_agent.py         # Base agent class (parent class for all agents)
│   ├── founder.py            # Founder agent implementation
│   └── investor.py           # Investor agent implementation
│
├── system/                    # System orchestration module
│   ├── __init__.py
│   └── orchestrator.py       # Multi-round competition orchestrator (core logic)
│
├── config/                    # Configuration module
│   ├── __init__.py
│   ├── default_config.py     # Default configuration file (system parameters, agent configs)
│   └── prompts.py            # All prompt templates (customizable)
│
├── utils/                     # Utility modules
│   ├── __init__.py
│   ├── llm_client.py         # LLM API client wrapper (supports OpenAI-compatible interfaces)
│   └── dialog_logger.py     # Dialog logging utility
│
├── main.py                   # Main program entry point
├── analyze_results.py        # Results analysis tool
└── README.md                 # This document
```

## Module Functionality

### 1. agents/ - Agent Modules

#### `base_agent.py` - Base Agent Class
- **Function**: Defines common interfaces and base functionality for all agents
- **Core Methods**:
  - `process_request()`: Abstract method to process requests
  - `add_to_history()`: Record history
  - `reset()`: Reset state
- **Usage**: Serves as the parent class for Founder and Investor, providing a unified interface

#### `founder.py` - Founder Agent
- **Function**: Propose strategies and iteratively optimize them
- **Core Methods**:
  - `generate_strategy(requirement)`: Generate initial strategy
  - `iterate_strategy(all_scores, feedback, requirement)`: Iterate strategy based on feedback
- **Features**:
  - Supports custom specialization
  - Automatically extracts strategy proposals (PROPOSAL section)
  - Maintains multi-round score history

#### `investor.py` - Investor Agent
- **Function**: Evaluate strategies and allocate scores
- **Core Methods**:
  - `evaluate_strategies(strategies, max_points, requirement)`: Evaluate all strategies
- **Features**:
  - Each investor has unique evaluation criteria and investment philosophy
  - Provides summary, detailed evaluation, and points
  - Parses structured LLM responses (SUMMARIES, DETAILS, ALLOCATIONS)

### 2. system/ - System Orchestration Module

#### `orchestrator.py` - Multi-round Competition Orchestrator
- **Function**: Coordinates the entire multi-round competition process
- **Core Methods**:
  - `run(requirement)`: Execute the complete multi-round competition
  - `_initial_round(requirement)`: First round initial strategies
  - `_iteration_round(round_num)`: Subsequent round iterations
- **Process**:
  1. Round 1: All founders propose initial strategies → All investors evaluate
  2. Subsequent rounds: Founders iterate based on feedback → Investors re-evaluate
  3. Calculate final scores and determine winner
- **Output**: Complete competition results JSON (includes data from all rounds)

### 3. config/ - Configuration Module

#### `default_config.py` - Default Configuration File
- **Function**: Defines all configurations required for system operation
- **Configuration Items**:
  ```python
  {
      "system": {
          "num_rounds": 3,              # Number of competition rounds
          "max_investor_points": 100,    # Total points each investor allocates
          "temperature": 0.7,            # LLM temperature parameter
          "base_url": "...",             # LLM API address
          "api_key": "..."               # API key
      },
      "instruction": "...",              # Task requirement description
      "founders": [...],                 # Founder configuration list
      "investors": [...]                 # Investor configuration list
  }
  ```
- **Modification Location**: Edit this file directly to modify configurations

#### `prompts.py` - Prompt Templates
- **Function**: Defines all LLM prompt templates
- **Template List**:
  - `FOUNDER_INITIAL_PROMPT`: Founder initial strategy generation prompt
  - `FOUNDER_ITERATION_PROMPT`: Founder iteration optimization prompt
  - `INVESTOR_EVALUATION_PROMPT`: Investor evaluation prompt
- **Features**:
  - All prompts include `requirement` field to ensure clear task objectives
  - Uses structured format ([THINKING], [PROPOSAL], etc.)
  - Can be modified at any time to adjust agent behavior

### 4. utils/ - Utility Modules

#### `llm_client.py` - LLM Client
- **Function**: Wraps LLM API calls
- **Features**:
  - Supports OpenAI-compatible interfaces
  - Supports custom base_url (for local LLMs, proxies, etc.)
  - Supports per-call model override
- **Usage Example**:
  ```python
  client = LLMClient(api_key='xxx', base_url='https://api.deepseek.com/v1')
  response = client.generate(prompt, model='deepseek-chat', temperature=0.7)
  ```

#### `dialog_logger.py` - Dialog Logging
- **Function**: Records all LLM interactions (prompt-response pairs)
- **Features**:
  - Global log storage
  - Can be categorized by agent name and type
  - Supports export to JSON

## Configuration Files

### Main Configuration File Locations

1. **`config/default_config.py`** - System Configuration
   - Modify system parameters (rounds, points, etc.)
   - Configure Founders and Investors
   - Set LLM API information

2. **`config/prompts.py`** - Prompt Configuration
   - Modify Founder prompts
   - Modify Investor prompts
   - Adjust agent behavior and output format

### Configuration Examples

#### Modify Task Requirement
Edit the `instruction` field in `config/default_config.py`:
```python
"instruction": "Create a personalized home page for a deep learning scientist."
```

#### Add More Founders
Add to the `founders` list in `config/default_config.py`:
```python
{
    "name": "Founder_D",
    "specialization": "AI and Machine Learning",
    "model": "deepseek-chat"
}
```

#### Modify Investor Evaluation Criteria
Modify in `config/default_config.py` `investors`:
```python
{
    "name": "Investor_1",
    "criteria": "Innovation and novelty",
    "philosophy": "Focus on breakthrough ideas and creative solutions",
    "model": "deepseek-chat"
}
```

#### Use Different LLM
Modify the `system` configuration in `config/default_config.py`:
```python
"system": {
    "base_url": "https://api.openai.com/v1",  # or local LLM address
    "api_key": "your-api-key",
    "temperature": 0.7
}
```

## How to Run

### 1. Install Dependencies


### 2. Configure API Key and Address

Edit `config/default_config.py`:
```python
"system": {
    "api_key": "your-api-key-here",
    "base_url": "https://api.deepseek.com/v1",  # or your LLM service address
    ...
}
```

### 3. Run Main Program

```bash
python main.py
```

### 4. View Results

After running, two files will be generated:
- **`results_test_ds.json`**: Complete competition results
  - Contains all strategies from each round
  - All investor scores and feedback
  - Final winner and scores
- **`dialogs_test_ds.json`**: All LLM dialog records
  - Each agent's prompt and response
  - Can be used for analysis and debugging

### 5. Analyze Results (Optional)

```bash
python analyze_results.py
```
