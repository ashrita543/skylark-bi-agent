import { useEffect, useState } from "react";

const money = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 });

function Metric({ label, value, hint }) {
  return <article className="metric"><p>{label}</p><strong>{value}</strong>{hint && <span>{hint}</span>}</article>;
}

export default function Home() {
  const [dashboard, setDashboard] = useState(null);
  const [connection, setConnection] = useState("Checking configuration…");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function readError(response) {
    const body = await response.json().catch(() => ({}));
    const detail = body.detail;
    return typeof detail === "string" ? detail : detail?.message || "The request could not be completed.";
  }
  async function loadDashboard(force_refresh = false) {
    setLoading(true); setError("");
    try {
      const [connectionResponse, dashboardResponse] = await Promise.all([
        fetch("/api/connection"), fetch("/api/dashboard", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ force_refresh }) }),
      ]);
      if (!connectionResponse.ok) throw new Error(await readError(connectionResponse));
      setConnection("Connected to Monday.com");
      if (!dashboardResponse.ok) throw new Error(await readError(dashboardResponse));
      setDashboard(await dashboardResponse.json());
    } catch (err) { setConnection("Connection needs attention"); setError(err.message); }
    finally { setLoading(false); }
  }
  async function submitQuestion(event) {
    event.preventDefault(); if (question.trim().length < 3) return;
    setLoading(true); setError(""); setAnswer(null);
    try {
      const response = await fetch("/api/questions", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
      if (!response.ok) throw new Error(await readError(response));
      setAnswer(await response.json());
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }
  useEffect(() => { loadDashboard(); }, []);
  const summary = dashboard?.summary;
  return <main>
    <nav><div className="brand"><span>✦</span> SKYLARK DRONES</div><div className="connection"><i />{connection}</div></nav>
    <header><div><p className="eyebrow">BUSINESS INTELLIGENCE</p><h1>Mission control for<br />commercial growth.</h1><p className="intro">Live visibility across your Monday.com deals and work orders, built for decisions that need to move at flight speed.</p></div><button onClick={() => loadDashboard(true)} disabled={loading}>{loading ? "Refreshing…" : "Refresh data"}</button></header>
    {error && <section className="error"><strong>Unable to load live data.</strong><span>{error}</span></section>}
    <section className="metrics">
      <Metric label="Total pipeline" value={summary ? money.format(summary.pipeline.total_value) : "—"} hint={summary ? `${summary.pipeline.total_count} qualified deals` : "Waiting for data"} />
      <Metric label="Active pipeline" value={summary ? money.format(summary.pipeline.active_value) : "—"} hint={summary ? `${summary.pipeline.active_deal_count} active deals` : "Waiting for data"} />
      <Metric label="Billed value" value={summary ? money.format(summary.work_orders.total_billed) : "—"} hint={summary ? `${summary.work_orders.billed_count} billed work orders` : "Waiting for data"} />
      <Metric label="Work orders" value={summary ? summary.work_orders.active_count : "—"} hint={summary ? `${summary.work_orders.completed_count} completed · ${summary.work_orders.delayed_count} delayed` : "Waiting for data"} />
    </section>
    <section className="panels"><article className="panel"><p className="eyebrow">PIPELINE MIX</p><h2>Pipeline by sector</h2><div className="rows">{summary ? Object.entries(summary.by_sector.pipeline).map(([sector, [value, count]]) => <div className="row" key={sector}><span>{sector}</span><b>{money.format(value)}</b><small>{count} deals</small></div>) : <p>Load your Monday.com configuration to see sector performance.</p>}</div></article>
      <article className="panel"><p className="eyebrow">EXECUTION</p><h2>Work order status</h2><div className="rows">{summary ? Object.entries(summary.status_distribution.work_orders).map(([status, count]) => <div className="row" key={status}><span>{status}</span><b>{count}</b><small>work orders</small></div>) : <p>Live execution status will appear here.</p>}</div></article></section>
    <section className="ask"><p className="eyebrow">ASK THE BI AGENT</p><h2>What do you need to know?</h2><form onSubmit={submitQuestion}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="e.g. Which sectors have the strongest pipeline?" aria-label="Business intelligence question" /><button disabled={loading}>Ask agent</button></form>{answer && <div className="answer"><p>{answer.response}</p>{answer.caveats?.length > 0 && <small>Data notes: {answer.caveats.join(" ")}</small>}</div>}</section>
    {dashboard?.data_quality_issues?.length > 0 && <section className="notes"><strong>Data quality notes</strong>{dashboard.data_quality_issues.map((item) => <span key={item}>{item}</span>)}</section>}
  </main>;
}
