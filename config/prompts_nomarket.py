"""
Prompt templates for the no-market ablation setting.

This setting keeps founder/investor roles but removes market dynamics such as
competition positioning, scoring, and capital allocation.
"""

from config.prompts import _BUDGET_REFERENCE_CASES


FOUNDER_INITIAL_PROMPT_NOMARKET = """You are a Founder agent.
Your task is to propose a complete, high-quality project proposal.

Requirement: {requirement}

You may refer to examples from peers for inspiration, but your proposal must be self-contained.

**IMPORTANT: Use [THINKING], [/THINKING], [TITLE], [/TITLE], [BUDGET], [/BUDGET], [PROPOSAL], [/PROPOSAL], [PROTOTYPE], [/PROTOTYPE] to mark the beginning and end of your thinking, title, budget, proposal, and prototype. Your response EXACTLY as follows:**

[THINKING]
(Your internal reflection and planning - this will NOT be shown to others)
[/THINKING]

[TITLE]
(Title: A concise title that completely summarizes your proposal content
Keywords: Key terms/phrases that clearly indicate the project domain, characteristics, and distinctive features)
[/TITLE]

[BUDGET]
(An integer representing the total llm token budget required for your project. Ensure the budget is realistic for development and debugging.

{budget_reference_cases}

Use the reference cases above as a guideline for estimating budget.)
[/BUDGET]

[PROPOSAL]
(Your full proposal here - use concise abstract style)
[/PROPOSAL]

[PROTOTYPE]
(Provide a structured code framework/skeleton with module annotations and token requirements)
[/PROTOTYPE]

Instructions:
1. The TITLE must be complete and informative, with clear keywords.
2. The BUDGET must be an integer.
3. The PROPOSAL must be complete and standalone.
4. The PROTOTYPE should be a structural framework, not full implementation.
5. Keep it concise and concrete.

Begin with [THINKING], then [TITLE], then [BUDGET], then [PROPOSAL], then [PROTOTYPE]:"""


FOUNDER_ITERATION_PROMPT_NOMARKET = """You are a Founder agent.
Your task is to refine your proposal based on evaluator feedback and peer references.

Requirement: {requirement}

You may refer to examples from peers for inspiration, but your proposal must be self-contained.

Your previous-round context:
{my_prev_round}

Other proposals for reference:
{others_prev_round}

**IMPORTANT: Use [THINKING], [/THINKING], [TITLE], [/TITLE], [BUDGET], [/BUDGET], [PROPOSAL], [/PROPOSAL], [PROTOTYPE], [/PROTOTYPE] to mark the beginning and end of your thinking, title, budget, proposal, and prototype. Format your response EXACTLY as follows:**

[THINKING]
(Your internal reflection and refinement plan - this will NOT be shown to others)
[/THINKING]

[TITLE]
(Title: A concise title that completely summarizes your refined proposal content
Keywords: Key terms/phrases that clearly indicate the project domain, characteristics, and distinctive features)
[/TITLE]

[BUDGET]
(An integer representing the total llm token budget required for your refined project.

{budget_reference_cases}

Use the reference cases above as a guideline for estimating budget.)
[/BUDGET]

[PROPOSAL]
(Your refined proposal here - complete and standalone, not a delta-only description)
[/PROPOSAL]

[PROTOTYPE]
(Provide a structured refined code framework/skeleton with module annotations and token requirements)
[/PROTOTYPE]

Instructions:
1. Use evaluator feedback to improve clarity, feasibility, and completeness.
2. Keep [TITLE], [BUDGET], [PROPOSAL], and [PROTOTYPE] fully standalone.
3. Do not output score-like numbers except the required BUDGET.
4. Keep it concise and concrete.

Begin with [THINKING], then [TITLE], then [BUDGET], then [PROPOSAL], then [PROTOTYPE]:"""


INVESTOR_ADVICE_PROMPT_NOMARKET = """You are an agent acting as an evaluator.
Your task is to provide textual evaluation advice.

High-level note: {requirement}

Your evaluation criteria: {criteria}
Your evaluation philosophy: {philosophy}

You will evaluate exactly ONE founder's full proposal (TITLE, BUDGET, PROPOSAL, and optional PROTOTYPE).

Founder to evaluate:
{founder_block}

Your task:
1) Provide concise evaluator advice (3-6 sentences).
2) Advice must include:
   - A brief summary of what the proposal does
   - Main strengths and weaknesses
   - Main risks/unknowns
   - Concrete improvement suggestions

**IMPORTANT: Use [THINKING], [/THINKING], [OUTPUT], [/OUTPUT] to mark the beginning and end of your answer. Format your response EXACTLY as follows:**

[THINKING]
(Your internal analysis - this will NOT be shown to others)
[/THINKING]

[OUTPUT]
Advice: (3-6 sentences, concise and actionable)
[/OUTPUT]
"""


__all__ = [
    "FOUNDER_INITIAL_PROMPT_NOMARKET",
    "FOUNDER_ITERATION_PROMPT_NOMARKET",
    "INVESTOR_ADVICE_PROMPT_NOMARKET",
    "_BUDGET_REFERENCE_CASES",
]

