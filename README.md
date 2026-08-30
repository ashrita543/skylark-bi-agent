# Skylark Drones BI Agent

Skylark Drones BI Agent is a Vercel-ready business-intelligence dashboard. It reads Deals and Work Orders from Monday.com, normalizes inconsistent operational data, calculates deterministic metrics, and answers natural-language BI questions. Monday.com credentials never leave the server.

## Architecture

- **Next.js** (`pages/`, `styles/`): responsive dashboard served at `/`.
- **FastAPI** (`api/index.py`): Vercel Python Function providing `/api/*` endpoints.
- **Python domain logic** (`app/`): retained Monday GraphQL client, normalizer, analytics, and question agent.

The frontend calls same-origin API routes, so there are no browser-side tokens, CORS configuration, or hard-coded localhost URLs. Streamlit and Docker are no longer part of the runtime.

## Required environment variables

Create a local `.env` from `.env.example`, and add the same values in Vercel Project Settings → Environment Variables:

```dotenv
MONDAY_API_TOKEN=your_read_only_monday_token
DEALS_BOARD_ID=your_deals_board_id
WORK_ORDERS_BOARD_ID=your_work_orders_board_id
```

Optional tuning values are `CACHE_EXPIRY_SECONDS`, `MAX_API_RETRIES`, and `API_TIMEOUT_SECONDS`. No OpenAI key is needed: the current agent is deterministic and does not make OpenAI calls.

## Local development

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm install
python -m pytest -q
```

For a faithful Vercel local environment, install the Vercel CLI then run `vercel dev`. It serves both the Next.js UI and Python API. Alternatively, use two terminals:

```powershell
python -m uvicorn api.index:app --reload --port 8000
npm run dev
```

Open `http://localhost:3000`. The FastAPI docs are at `http://localhost:8000/api/docs` in the two-server workflow.

## Testing and deployment

```powershell
python -m pytest -q
npm run build
vercel
vercel --prod
```

Vercel detects the root Next.js app and the FastAPI application exported as `api.index:app`; no `vercel.json` is required. See [DEPLOYMENT.md](DEPLOYMENT.md) for the GitHub-to-Vercel release steps.
