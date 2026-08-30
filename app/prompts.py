"""
LLM Prompts and System Instructions
Defines prompts for query understanding and response generation
"""

SYSTEM_PROMPT = """You are a business intelligence assistant for Skylark Drones, a drone services company.
You help founders and executives understand their business performance using data from:
1. Deals board - sales pipeline and deal tracking
2. Work Orders board - project execution and billing

Your role:
- Answer questions about pipeline, revenue, and operational metrics
- Provide insights on sector performance
- Help identify risks and opportunities
- Support leadership decision-making

Guidelines:
- Use the provided data and metrics - never fabricate numbers
- Be concise and founder-friendly
- Highlight data quality issues when relevant
- If something cannot be answered from available data, explain why
- Suggest clarifications when questions are ambiguous
- Focus on actionable insights

Current date: Use the knowledge cutoff date unless told otherwise."""

QUERY_UNDERSTANDING_PROMPT = """Analyze this user question and determine what data is needed to answer it.

Question: {question}

Identify:
1. Intent: What is the user trying to understand?
2. Required boards: Which board(s)? (Deals, Work Orders, or Both)
3. Required metrics: What calculations are needed? (e.g., pipeline total, deals by sector, active work orders)
4. Filters: Any time period, sector, status, or other criteria?
5. Aggregation: Do they want totals, breakdown by sector/stage, comparison, etc.?
6. Ambiguities: Any unclear aspects that need clarification?

Format your response as JSON:
{
  "intent": "...",
  "required_boards": ["Deals" or "WorkOrders" or both],
  "required_metrics": [...],
  "filters": {
    "time_period": "...",
    "sector": "...",
    "status": "...",
    "other": "..."
  },
  "aggregation": "...",
  "needs_clarification": true/false,
  "clarification_question": "..." (if needs_clarification is true)
}"""

RESPONSE_GENERATION_PROMPT = """Based on the analysis results below, provide a concise, founder-friendly response to the user's question.

User question: {question}

Analysis results:
{results}

Data quality caveats:
{caveats}

Guidelines for response:
- Be direct and concise (2-3 sentences maximum for main answer)
- Lead with the key number/insight
- Mention caveats only if they materially affect the answer
- Use simple language
- Include specific numbers and comparisons
- Suggest next steps or areas for investigation if relevant

Generate a clear, actionable response."""

CLARIFICATION_PROMPT = """The user asked: {question}

This question is ambiguous. Ask ONE clarifying question to understand their need better.
Provide 2-3 specific options they can choose from.

Format:
Question: ...
Options:
- Option 1
- Option 2
- Option 3
"""

LEADERSHIP_UPDATE_PROMPT = """Generate a concise executive summary (3-4 paragraphs) for leadership using this data:

Metrics:
{metrics}

Data quality notes:
{caveats}

Structure:
1. Current state (revenue, pipeline, operational status)
2. Sector performance highlights
3. Operational highlights (work order status)
4. Key risks or attention areas
5. Recommended next actions

Keep it founder-focused and actionable."""

# Query classification helpers
SECTOR_COMPARISON_KEYWORDS = [
    "compare", "vs", "versus", "which sector", "strongest", "weakest", "performance"
]

LEADERSHIP_KEYWORDS = [
    "executive summary", "leadership update", "board summary", "quarterly update",
    "overview", "snapshot", "status", "how are we doing", "business health"
]

PIPELINE_KEYWORDS = [
    "pipeline", "deals", "sales", "prospects", "opportunities", "deal value",
    "deal size", "deal count", "how's our pipeline", "total pipeline"
]

REVENUE_KEYWORDS = [
    "revenue", "billed", "invoiced", "income", "earnings", "how much", "total revenue",
    "revenue by sector"
]

WORK_ORDER_KEYWORDS = [
    "work order", "project", "execution", "delivery", "completion", "delayed",
    "active projects", "project status"
]
