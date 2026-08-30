# Deployment Guide

This guide explains how to deploy the Skylark Drones BI Agent to **Streamlit Community Cloud** so it's accessible via a public URL.

## Prerequisites

You will need:

1. **GitHub account** (free)
2. **Streamlit account** (free, linked to GitHub)
3. **Monday.com API Token** (from your Monday account)
4. **Monday.com Board IDs** (Deals and Work Orders boards)
5. **OpenAI API Key** (from your OpenAI account)

## Step 1: Get Your Monday.com Credentials

### Get your Monday.com API Token

1. Go to **[monday.com](https://monday.com)** and log in
2. Click your **profile icon** (bottom left)
3. Select **Admin**
4. Go to **Developers** → **API Tokens**
5. Click **Create token**
6. Name it "Skylark BI Agent"
7. Select **Read** access
8. Click **Create**
9. **Copy the token and save it securely** (you'll only see it once)

### Get your Board IDs

1. In Monday.com, open your **Deals** board
2. Look at the URL: `https://monday.com/boards/BOARD_ID_HERE/...`
3. Copy the **BOARD_ID** (the number)
4. Repeat for your **Work Orders** board
5. Save both IDs

## Step 2: Get Your OpenAI API Key

1. Go to **[platform.openai.com](https://platform.openai.com)**
2. Log in with your OpenAI account
3. Click **API keys** (left sidebar)
4. Click **Create new secret key**
5. Copy the key and save it securely

## Step 3: Push the Project to GitHub

If you haven't already:

1. Create a new **public** repository on GitHub (e.g., `skylark-bi-agent`)
2. Clone it locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/skylark-bi-agent.git
   cd skylark-bi-agent
   ```
3. Copy all project files into it
4. Create `.env` file (NOT committed):
   ```
   MONDAY_API_TOKEN=your_token_here
   DEALS_BOARD_ID=your_board_id
   WORK_ORDERS_BOARD_ID=your_board_id
   OPENAI_API_KEY=your_openai_key
   OPENAI_MODEL=gpt-4-turbo-preview
   CACHE_EXPIRY_SECONDS=3600
   MAX_API_RETRIES=3
   API_TIMEOUT_SECONDS=30
   ```
5. Verify `.env` is in `.gitignore` ✅
6. Push to GitHub:
   ```bash
   git add .
   git commit -m "Initial commit: Skylark BI Agent"
   git push origin main
   ```

## Step 4: Deploy to Streamlit Community Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Click **New app** (top right)
3. Select:
   - **Repository**: your GitHub repo
   - **Branch**: `main`
   - **Main file path**: `main.py`
4. Click **Deploy**

The app will deploy. You'll see a URL like:
```
https://YOUR-USERNAME-skylark-bi-agent-RANDOM.streamlit.app
```

## Step 5: Add Secrets in Streamlit Cloud

1. After deployment, click the **⋮** menu (top right of the app)
2. Select **Settings**
3. Go to **Secrets**
4. Paste this template and fill in your values:

```toml
MONDAY_API_TOKEN = "your_monday_api_token_here"
DEALS_BOARD_ID = "your_deals_board_id"
WORK_ORDERS_BOARD_ID = "your_work_orders_board_id"
OPENAI_API_KEY = "your_openai_api_key_here"
OPENAI_MODEL = "gpt-4-turbo-preview"
CACHE_EXPIRY_SECONDS = "3600"
MAX_API_RETRIES = "3"
API_TIMEOUT_SECONDS = "30"
```

5. Click **Save**

The app will automatically rerun with the new secrets.

## Step 6: Test the Deployment

1. Your app is now live at the URL provided
2. Click **Test Connection** in the sidebar
3. You should see ✅ "Connected to Monday.com successfully!"
4. Ask a question:
   - "What's our total pipeline?"
   - "Which sector has the strongest pipeline?"
   - Click **Leadership Update** button

## Troubleshooting

### "Missing configuration" error

- Go to app **Settings** → **Secrets**
- Verify all four required variables are set:
  - MONDAY_API_TOKEN
  - DEALS_BOARD_ID
  - WORK_ORDERS_BOARD_ID
  - OPENAI_API_KEY
- Save and wait for app to redeploy

### "Connection failed" error

- Verify your MONDAY_API_TOKEN is correct
- Verify your board IDs are correct (should be numbers)
- Check that your Monday.com workspace is active

### "Invalid API key" for OpenAI

- Verify your OPENAI_API_KEY is correct
- Check that your OpenAI account has active credits

### App takes a long time to load

- First load can take 30-60 seconds as dependencies install
- Subsequent loads are faster
- Check Streamlit logs: click **⋮** → **Manage app** → **Logs**

## Local Testing Before Deployment

To test locally before deploying:

1. Create `.streamlit/secrets.toml`:
   ```toml
   MONDAY_API_TOKEN = "your_monday_api_token_here"
   DEALS_BOARD_ID = "your_deals_board_id"
   WORK_ORDERS_BOARD_ID = "your_work_orders_board_id"
   OPENAI_API_KEY = "your_openai_api_key_here"
   OPENAI_MODEL = "gpt-4-turbo-preview"
   ```

2. Run:
   ```bash
   streamlit run main.py
   ```

3. Open http://localhost:8501

## Sharing Your Deployment

Once deployed, your public URL can be shared with anyone:
- Send the URL directly
- Include it in an email or Slack message
- Add it to a GitHub README

Anyone with the link can access the AI agent (no authentication required).

## Updating Your Deployment

To update the app:

1. Make changes locally
2. Push to GitHub:
   ```bash
   git add .
   git commit -m "Update description"
   git push origin main
   ```
3. Streamlit automatically redeploys

To update secrets (API keys, board IDs):

1. Go to **Settings** → **Secrets**
2. Update the values
3. Click **Save**
4. App automatically reruns

## Important: Security Best Practices

✅ DO:
- Keep API keys in **Streamlit Secrets** (not in code)
- Use `.env` locally only (add to `.gitignore`)
- Use read-only API tokens
- Make your GitHub repo **public** (Streamlit Community Cloud requires it)

❌ DON'T:
- Commit `.env` to GitHub
- Share API keys via email or Slack
- Use your personal OpenAI account for production
- Enable authentication/login (Streamlit Community Cloud is public)

## Further Help

- **Streamlit Cloud Docs**: https://docs.streamlit.io/deploy/streamlit-cloud
- **Monday.com API**: https://developer.monday.com/
- **OpenAI API**: https://platform.openai.com/docs
