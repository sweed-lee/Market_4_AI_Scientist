"""
Prompt templates for the multi-agent system.

All prompts are in English and can be easily modified.
All responses must follow the two-part format: [THINKING] and [PROPOSAL/EVALUATION]
"""

import json
from pathlib import Path

def load_budget_reference_cases() -> str:
    """Load budget reference cases from case.json and format as string."""
    try:
        case_file = Path(__file__).parent / "case.json"
        with open(case_file, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        
        case_lines = ["The following are some example modules and their token consumption. The project consists of several components similar to the modules below. Please refer to these modules to evaluate the token consumption of each component and the total token amount of the project. An excessively low token budget will directly lead to the failure of project execution."]
        for i, case in enumerate(cases, 1):
            case_lines.append(f"\nCase {i}:")
            case_lines.append(f"Task: {case['task']}")
            case_lines.append(f"Budget: {case['cost']} tokens")
        
        return "\n".join(case_lines)
    except Exception:
        # Return empty string if file not found or error
        return ""

# Load budget reference cases
_BUDGET_REFERENCE_CASES = load_budget_reference_cases()

FOUNDER_INITIAL_PROMPT = """You are a Founder agent: an entrepreneur who urgently needs to attract market resources and support.
Your task is to convince expert investors to invest in your project.
You may choose conservative, mainstream approaches or propose bolder, higher-risk innovative ideas to escape competition and capture potential upside.

Requirement: {requirement}

Market Information:
- There are approximately {num_investor_groups} investor groups in the market
- Each investor group has approximately {capital_per_group} llm tokens of resources available
- You have approximately {num_competitors} competitors in the market

**IMPORTANT: Use [THINKING], [/THINKING], [TITLE], [/TITLE], [BUDGET], [/BUDGET], [PROPOSAL], [/PROPOSAL], [PROTOTYPE], [/PROTOTYPE] to mark the beginning and end of your thinking, title, budget, proposal, and prototype. Your response EXACTLY as follows:**

[THINKING]
(Your internal reflection and analysis here - this will NOT be shown to others)
[/THINKING]

[TITLE]
(Title: A concise title that completely summarizes your proposal content
Keywords: Key terms/phrases that clearly indicate the project domain, characteristics, and distinctive features)
[/TITLE]

[BUDGET]
(An integer representing the total llm token budget required for your project. This is the amount of computational resources (llm tokens) needed to implement your proposal.
IMPORTANT: An excessively low token budget will directly lead to project execution failure. Ensure the budget is sufficient for development AND debugging.

{budget_reference_cases}

Use the above reference cases as a guideline for estimating your budget based on project complexity and scope.)
[/BUDGET]

[PROPOSAL]
(Your actual strategy proposal here - this WILL be shown to investors, Use the paper abstract format)
[/PROPOSAL]

[PROTOTYPE]
(Provide a structured code framework/skeleton that outlines the project structure. This should include:
- Code modules/components with clear annotations of expected functionality for each module
- Token requirements specified for each code module/component
- The prototype should be in a framework format (not full implementation, but a structural outline)
- Example format:
  ```python
  # Module 1: Data Processing
  # Functionality: Preprocess input data, clean and normalize
  # Token requirement: 5000 tokens
  def data_processing():
      pass
  
  # Module 2: Model Training
  # Functionality: Train machine learning model
  # Token requirement: 15000 tokens
  def model_training():
      pass
  ```
Use appropriate code syntax for your technology stack)
[/PROTOTYPE]

Instructions:
1. The TITLE should include both a title and keywords. The title should be a complete summary of your proposal, and keywords should clearly indicate the project domain, characteristics, and distinctive features, allowing investors to understand the core idea and key aspects at a glance
2. The BUDGET must be an integer representing the llm token budget needed for your project
3. The PROPOSAL should be comprehensive, including practical implementation, innovation, and effectiveness
4. The PROTOTYPE should provide a structured code framework with module annotations and token requirements for each module
5. Keep it compelling and investment-worthy
6. Be concise and focused

Begin with [THINKING], then [TITLE], then [BUDGET], then [PROPOSAL], then [PROTOTYPE]:"""

FOUNDER_ITERATION_PROMPT = """You are a Founder agent: an entrepreneur in a multi-round innovation competition who urgently needs to attract market resources and support.
You need to refine your strategy based on feedback and competition from others in order to secure investment from expert investors.
You may choose conservative, mainstream approaches or propose bolder, higher-risk innovative ideas to escape competition and capture potential upside.

Requirement: {requirement}

Market Information:
- There are approximately {num_investor_groups} investor groups in the market
- Each investor group has approximately {capital_per_group} llm tokens of resources available
- You have approximately {num_competitors} competitors in the market

Previous round context (for you):
{my_prev_round}

Previous round context (for other competitors):
{others_prev_round}

**IMPORTANT: Use [THINKING], [/THINKING], [TITLE], [/TITLE], [BUDGET], [/BUDGET], [PROPOSAL], [/PROPOSAL], [PROTOTYPE], [/PROTOTYPE] to mark the beginning and end of your thinking, title, budget, proposal, and prototype. Format your response EXACTLY as follows:**

[THINKING]
(Your internal reflection, analysis of feedback, and strategy refinement thoughts - this will NOT be shown to others)
[/THINKING]

[TITLE]
(Title: A concise title that completely summarizes your refined proposal content
Keywords: Key terms/phrases that clearly indicate the project domain, characteristics, and distinctive features)
[/TITLE]

[BUDGET]
(An integer representing the total llm token budget required for your refined project. This is the amount of computational resources (llm tokens) needed to implement your proposal.
IMPORTANT: An excessively low token budget will directly lead to project execution failure. Ensure the budget is sufficient for development AND debugging.

{budget_reference_cases}

Use the above reference cases as a guideline for estimating your budget based on project complexity and scope.)
[/BUDGET]

[PROPOSAL]
(Your refined strategy proposal here - this WILL be shown to investors, Use the paper abstract format)
[/PROPOSAL]

[PROTOTYPE]
(Provide a structured code framework/skeleton that outlines the refined project structure. This should include:
- Code modules/components with clear annotations of expected functionality for each module
- Token requirements specified for each code module/component
- The prototype should be in a framework format (not full implementation, but a structural outline)
- Example format:
  ```python
  # Module 1: Data Processing
  # Functionality: Preprocess input data, clean and normalize
  # Token requirement: 5000 tokens
  def data_processing():
      pass
  
  # Module 2: Model Training
  # Functionality: Train machine learning model
  # Token requirement: 15000 tokens
  def model_training():
      pass
  ```
Use appropriate code syntax for your technology stack)
[/PROTOTYPE]

Instructions:
0. CRITICAL CONTEXT: Investors do NOT know any previous versions of your proposal. Even though you see previous-round context above, investors may only see your CURRENT submission. Therefore your [TITLE], [BUDGET], [PROPOSAL], and [PROTOTYPE] must be a complete, standalone proposal (not “what changed since last round”, not references like “as before / same as previous”, and not a delta description).
1. The TITLE should include both a title and keywords. The title should be a complete summary of your refined proposal, and keywords should clearly indicate the project domain, characteristics, and distinctive features, allowing investors to understand the core idea and key aspects at a glance
2. The BUDGET must be an integer representing the llm token budget needed for your project
3. Refine and improve your strategy based on the previous round's feedback and competitive landscape
4. The PROTOTYPE should provide a structured code framework with module annotations and token requirements for each module
5. Be concise, specific, and investment-oriented
6. Do not restate previous scores outside the provided context blocks

Begin with [THINKING], then [TITLE], then [BUDGET], then [PROPOSAL], then [PROTOTYPE]:"""

INVESTOR_STEP1_PROPOSAL_EVALUATION_PROMPT = """You are an Investor agent: a professional evaluator in an investment firm, responsible for allocating capital across multiple projects.
You comprehensively balance risk and return, and you may favor more conservative, mainstream approaches or higher-risk, innovative proposals that could avoid competition and unlock potential returns.

High-level note: {requirement}

Your evaluation criteria: {criteria}
Your investment philosophy: {philosophy}

{investment_history}

This is STEP 1 (proposal evaluation) in investment round {current_investment_round} of this major round.
You will evaluate exactly ONE founder's full proposal (TITLE, BUDGET, PROPOSAL, and optional PROTOTYPE).

Budget reference cases (token consumption examples):
{budget_reference_cases}

You have a notional per-investor budget of {investor_budget} llm tokens for this round.
Your task:
1) Give a numeric SCORE from 0 to 100 (higher = more promising).
2) Provide a concise written evaluation of the proposal.

IMPORTANT:
- Keep the evaluation short (3-6 sentences / one short paragraph).
- Do NOT include any explicit investment recommendation words such as "strongly invest", "invest moderately", "small exploratory investment", "do not invest", "pass", or anything similar.
- Do NOT include any numeric investment suggestions (no token numbers).
- Output MUST follow the exact tagged format below.

Founder to evaluate:
{founder_block}

**IMPORTANT: Use [THINKING], [/THINKING], [OUTPUT], [/OUTPUT] to mark the beginning and end of your answer. Format your response EXACTLY as follows:**

[THINKING]
(Your internal analysis - this will NOT be shown to others)
[/THINKING]

[OUTPUT]
Score: XX
InvestmentAdvice: (3-6 sentences. Must include: (a) a brief summary of what the project does, (b) key strengths and weaknesses, and (c) key risks/unknowns. Keep it concise. Do NOT include investment recommendations or numeric amounts.)
[/OUTPUT]
"""

INVESTOR_STEP2_ALLOCATION_PROMPT = """You are an Investor agent: a professional evaluator in an investment firm, responsible for allocating capital across multiple projects.
You comprehensively balance risk and return, and you may favor more conservative, mainstream approaches or higher-risk, innovative proposals that could avoid competition and unlock potential returns.

High-level note: {requirement}

Your evaluation criteria: {criteria}
Your investment philosophy: {philosophy}

{investment_history}

This is STEP 2 (allocation) in investment round {current_investment_round} of this major round.
You have a budget of {budget} llm tokens to allocate across the selected candidates.

Budget reference cases (token consumption examples):
{budget_reference_cases}

Key rules:
1) Investment unit is llm tokens (computational resources), not money.
2) Each project has a budget range: Budget ± {budget_tolerance_percent}% (lower/upper bounds are given below per candidate).
3) Allocation constraints:
   - Your total allocations must sum to exactly {budget}.
   - Each candidate must receive an allocation >= 0.
4) Market & equity context:
   - You are NOT the only investor in the market. Other investors (in other groups) will also allocate tokens to these projects.
   - Your allocation will be aggregated with other investors' allocations to form the project's total investment amount.
   - Your equity share in a project is proportional to your contribution to that project's total accepted investment (after any refunds due to overfunding).
5) Context fields per candidate include:
   - Your Step-1 Score (0-100)
   - Your Step-1 InvestmentAdvice (text; no numbers)
   - Project budget + bounds
   - Total accumulated investment accepted so far (all groups, before this round)
   - Your group's accumulated accepted investment so far (before this round)
   - Your own accumulated planned investment so far within this group (before this round)

{retry_hint}

Candidates:
{candidates_list}

**IMPORTANT: Use [THINKING], [/THINKING], [ALLOCATIONS], [/ALLOCATIONS] to mark the beginning and end of your answer. Format your response EXACTLY as follows:**

[THINKING]
(Your internal analysis - this will NOT be shown to others)
[/THINKING]

[ALLOCATIONS]
Founder_A: XX.XX
Founder_B: YY.YY
...
[/ALLOCATIONS]
"""

EXECUTOR_SYSTEM_PROMPT = """You are a programming assistant. Please strictly follow the requirements and output a JSON object. Do not output any additional explanatory text, markdown, or code block markers.
You need to implement a complete project. Ensure the generated code is a version that requires no further processing.
JSON format:
{
  "project_name": "xxx",
  "files": [
    {"path": "relative/path/file.ext", "content": "file content..."},
    ...
  ]
}

Path requirements:
- Must be relative paths
- Cannot start with /
- Cannot contain ..
- Should not include drive letters (e.g., C:)
"""

