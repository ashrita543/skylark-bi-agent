# Deploying Skylark Drones BI Agent to Vercel

## 1. Prepare GitHub

From the project directory, check that no `.env` file is staged, then commit and push the finished project:

```powershell
git status
git add .
git commit -m "Deploy Skylark Drones BI dashboard on Vercel"
git push -u origin main
```

## 2. Create the Vercel project

1. Open [Vercel](https://vercel.com/new), import the GitHub repository, and keep the repository root as the Root Directory.
2. Let Vercel detect **Next.js**. Do not set a custom build or output command.
3. In **Settings → Environment Variables**, add these values for Production, Preview, and Development:

   - `MONDAY_API_TOKEN` — a read-only Monday.com token
   - `DEALS_BOARD_ID` — the Deals board ID
   - `WORK_ORDERS_BOARD_ID` — the Work Orders board ID
   - `CACHE_EXPIRY_SECONDS` — optional; default `600`
   - `MAX_API_RETRIES` — optional; default `3`
   - `API_TIMEOUT_SECONDS` — optional; default `30`

4. Deploy. Vercel uses Python 3.12 (`.python-version`), builds the Next.js UI, and deploys `api/index.py` as the FastAPI function.

## 3. Verify the public deployment

After Vercel gives you a URL such as `https://your-project.vercel.app`, verify:

```powershell
curl https://your-project.vercel.app/api/health
curl https://your-project.vercel.app/api/connection
```

Then open the site, confirm the connection indicator reads “Connected to Monday.com,” refresh live data, and ask a BI question. If `/api/health` lists missing configuration, add the listed variables in Vercel and redeploy.

## CLI alternative

```powershell
npm install -g vercel
vercel link
vercel env pull .env.local
vercel dev
vercel --prod
```

Never commit `.env`, `.env.local`, or an API token. On a Monday API error, confirm the token has read access to both board IDs and inspect Vercel Function logs.
