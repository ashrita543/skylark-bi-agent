# Skylark Drones BI Agent

**AI-powered business intelligence for Monday.com data**

A Streamlit-based conversational AI agent that answers founder-level business questions about sales pipeline, work orders, and operational metrics. The app connects directly to Monday.com, fetches live data, normalizes messy real-world values, calculates deterministic business metrics, and explains them in natural language.

## Problem Statement

Founders need quick, accurate answers to business questions like:
- "What's our total pipeline?"
- "Which sectors have the strongest performance?"
- "How many active deals do we have?"
- "What should I mention in the leadership update?"

This agent makes that data accessible through a simple chat interface.

## Key Features

✅ **Real Monday.com Integration** — Fetches live data from your Deals and Work Orders boards via GraphQL API

✅ **Conversational Interface** — Ask natural-language questions and get instant answers

✅ **Deterministic Metrics** — All numbers are calculated in Python, never fabricated by the LLM

✅ **Data Normalization** — Handles missing values, inconsistent dates, currency formats, and messy real-world data

✅ **Cross-board Analysis** — Compares pipeline and execution metrics across sectors

✅ **Leadership Updates** — One-click executive summaries with data-quality caveats

✅ **Error Handling** — Gracefully handles API failures, missing data, and edge cases

✅ **Deployed & Public** — Deploy to Streamlit Cloud with a public URL anyone can access

## Architecture

```
User Question
    ↓
[Query Understanding] — Parse intent, identify required boards
    ↓
[Monday.com GraphQL API] — Fetch live data with pagination
    ↓
[Data Normalization] — Clean dates, sectors, statuses, values
    ↓
[Deterministic Analytics] — Calculate metrics in Python
    ↓
[LLM Explanation] — OpenAI formats results as natural language
    ↓
Conversational Response
```

## Tech Stack

- **Streamlit** — Modern Python web UI framework
- **Monday.com GraphQL API** — Live business data source
- **OpenAI GPT-4** — LLM for conversational responses
- **Pandas** — Data processing and analytics
- **Python** — Core logic and normalization
- **pytest** — Comprehensive test suite (88 tests)

## Project Structure

```
app/
├── main.py                 # Streamlit UI (chat interface, sidebar)
├── agent.py                # Query planning & orchestration
├── config.py               # Environment config & validation
├── monday_client.py        # Read-only Monday.com GraphQL client
├── normalizer.py           # Data normalization & cleaning
├── analytics.py            # Deterministic business metrics
└── prompts.py              # Query understanding & keywords

tests/
├── test_agent.py           # Query planning & orchestration
├── test_analytics.py       # Metric calculations (86 tests)
├── test_monday_client.py   # API client with mocked responses
└── test_normalizer.py      # Data normalization (8 tests)

.streamlit/
├── config.toml            # Streamlit configuration
└── secrets.toml.example   # Secrets template for local testing

.env.example               # Environment variable template
requirements.txt           # Python dependencies
Dockerfile                 # Container configuration
DEPLOYMENT.md              # Streamlit Cloud setup guide
DECISION_LOG.md            # Architecture decisions
```

## Getting Started Locally

### 1. Install Python 3.9+

```bash
python --version  # Verify Python 3.9 or later
```

### 2. Clone and Setup

```bash
git clone https://github.com/YOUR_USERNAME/skylark-bi-agent.git
cd skylark-bi-agent
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Credentials

Create a `.env` file in the project root:

```bash
cp .env.example .env
# Then edit .env with your actual values:
MONDAY_API_TOKEN=your_api_token_here
DEALS_BOARD_ID=your_board_id
WORK_ORDERS_BOARD_ID=your_board_id
OPENAI_API_KEY=your_openai_key_here
```

(See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step credential retrieval)

### 5. Run Locally

```bash
streamlit run app/main.py
```

The app opens at `http://localhost:8501`

### 6. Test Connection

In the Streamlit sidebar, click **Test Connection** to verify Monday.com access.

## Deployment to Streamlit Cloud

**Streamlit Community Cloud** is the easiest way to deploy and share a public URL.

### Quick Summary

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **New app** and select your GitHub repo
4. In app settings, add secrets:
   - `MONDAY_API_TOKEN`
   - `DEALS_BOARD_ID`
   - `WORK_ORDERS_BOARD_ID`
   - `OPENAI_API_KEY`

Your app gets a public URL like: `https://your-username-skylark-bi-agent-abc123.streamlit.app`

**Full instructions:** See [DEPLOYMENT.md](DEPLOYMENT.md)

## Example Questions

The agent understands natural language questions like:

**Pipeline Metrics**
- "What's our total pipeline?"
- "How many active deals do we have?"
- "What's the average deal size?"
- "What's our weighted pipeline?"

**Sector Analysis**
- "Which sectors have the strongest pipeline?"
- "Compare energy and manufacturing"
- "What's the mining sector pipeline?"

**Work Orders**
- "How many active work orders?"
- "Which projects are delayed?"
- "What's our total billed revenue?"

**Executive**
- "Give me a leadership update"
- "What should I know for the investor call?"

## Data Normalization

The agent handles messy real-world data:

| Issue | Handled By |
|-------|------------|
| Null/missing values | Exclusion from metrics + caveat |
| Inconsistent dates (MM/DD/YY, DD/MM/YY, etc) | Date parser with fallback |
| Currency formatting ($1,000 vs 1000) | Regex extraction |
| Inconsistent sectors ("Energy", "energy", "Oil & Gas") | Normalization mapping |
| Status variants ("Open", "OPEN", "In Progress") | Case-insensitive matching |
| Probability formats (0.8, 80%, "high") | Conversion to 0-1 range |

## Deterministic Analytics

All business calculations happen in Python, never in the LLM:

```python
# Example: Total Pipeline
total = sum(deal["deal_value"] for deal in deals if deal["deal_value"])

# Example: Active Pipeline (Open deals only)
active = sum(deal["deal_value"] for deal in deals if deal["deal_status"] == "Open")

# Example: By Sector
by_sector = {}
for deal in deals:
    sector = deal["sector"] or "Unknown"
    by_sector[sector] = by_sector.get(sector, 0) + deal["deal_value"]
```

The LLM receives these numbers and explains them naturally.

## Error Handling

The agent gracefully handles:

- **Missing API token** → "Please configure MONDAY_API_TOKEN"
- **Invalid token** → "Authentication failed - check your API token"
- **Invalid board IDs** → "Board not found - check DEALS_BOARD_ID"
- **Network failure** → "Cannot connect to Monday.com API"
- **Missing OpenAI key** → "OpenAI configuration missing"
- **Empty boards** → "No data available in this board"
- **Missing columns** → "Required column not found"

## Testing

The project includes 88 comprehensive tests:

```bash
# Run all tests
python -m pytest -v

# Run specific test file
python -m pytest tests/test_analytics.py -v

# Run with coverage
python -m pytest --cov=app tests/
```

**Test Coverage:**
- ✅ Monday API client (connection, pagination, errors)
- ✅ Data normalization (dates, numbers, sectors, statuses)
- ✅ Analytics calculations (totals, averages, by sector)
- ✅ Query planning (intent detection)
- ✅ Agent orchestration (fetch → normalize → analyze)

**Tests use mocked API responses** — no real API calls required

## Security

✅ **Secrets Protection**
- API tokens stored in `.env` (never committed)
- Streamlit Cloud uses encrypted secrets
- No credentials in source code
- No sensitive values printed to logs

✅ **Read-Only Access**
- Only reads data from Monday.com
- No write/update/delete operations
- GraphQL queries validated

✅ **Best Practices**
- `.env` in `.gitignore`
- `.env.example` with placeholders only
- Environment variables for all secrets
- Token rotation recommended periodically

## Limitations & Assumptions

1. **Fiscal Year**: Assumes calendar year (Jan-Dec) unless overridden
2. **Time Zones**: Uses board's configured time zone
3. **Join Strategy**: Can join boards only if they share a customer/deal identifier
4. **Rate Limits**: Respects Monday.com API rate limits with retry logic
5. **Data Age**: Results are current as of last Monday API call (max cached 10 min)
6. **Natural Language**: Intent detection heuristic-based, not ML-trained

## Troubleshooting

### "Monday.com connection failed"

- Verify `MONDAY_API_TOKEN` is correct
- Check that token has read permissions
- Confirm `DEALS_BOARD_ID` and `WORK_ORDERS_BOARD_ID` are valid

### "Invalid OpenAI API Key"

- Verify `OPENAI_API_KEY` is correct
- Check that account has active credits
- Confirm key is for API (not web interface)

### "No data in board"

- Verify board has items/records
- Check that columns are correctly named
- Ensure API token has access to that board

### App runs slowly

- First load: Streamlit caches dependencies (30-60 sec)
- Subsequent loads: Fast (2-5 sec)
- Large boards (1000+ items): May take longer, increase timeout

## Resources

- **Monday.com API Docs**: https://developer.monday.com/
- **Streamlit Docs**: https://docs.streamlit.io/
- **OpenAI API**: https://platform.openai.com/docs
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Architecture Decisions**: See [DECISION_LOG.md](DECISION_LOG.md)

## Support

For issues or questions:

1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for setup issues
2. Check [DECISION_LOG.md](DECISION_LOG.md) for architecture questions
3. Review test files for usage examples
4. Check Streamlit logs: app ⋮ menu → Manage app → Logs

