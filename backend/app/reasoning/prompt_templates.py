SYSTEM_REPO_CHAT = """You are Code Archaeologist, an AI that understands software repositories and their evolution over time.
You answer questions about codebases using commit history, code changes, and development context.
Be precise, cite specific commits or dates when relevant, and acknowledge uncertainty honestly."""

SYSTEM_CAUSAL = """You are an expert software historian and architect.
Given commit history and code changes, you infer WHY software decisions were made.
Always provide a confidence score (0-100%) and cite your evidence sources."""

SYSTEM_EVOLUTION = """You are a software evolution analyst.
Given a timeline of commits, identify architectural milestones, turning points, and evolutionary patterns.
Present findings as a clear narrative timeline."""


def repo_chat_prompt(query: str, context: str) -> str:
    return f"""Based on the following commit history and code changes from the repository, answer the question.

REPOSITORY CONTEXT (chronological commit snapshots):
{context}

QUESTION: {query}

Provide a clear, specific answer citing relevant commits and dates where possible."""


def causal_reasoning_prompt(query: str, context: str) -> str:
    return f"""Analyze the following commit history to answer WHY this software change happened.

COMMIT HISTORY EVIDENCE:
{context}

QUESTION: {query}

Respond in this format:
EXPLANATION: [Your causal explanation]
EVIDENCE: [Specific commits, dates, or patterns that support this]
CONFIDENCE: [0-100%]
ALTERNATIVE THEORIES: [Other possible explanations if applicable]"""


def evolution_prompt(repo_name: str, context: str) -> str:
    return f"""Analyze the commit history of '{repo_name}' and identify major evolutionary milestones.

COMMIT TIMELINE:
{context}

Identify:
1. Major architectural changes
2. Technology introductions or removals
3. Significant refactoring events
4. Pattern shifts in development

Present as a chronological narrative with specific dates."""