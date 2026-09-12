import { Link } from "react-router-dom";

export default function Result() {
  let result = null;
  try { result = JSON.parse(sessionStorage.getItem("scanResult") || "null"); } catch {}
  const declarations = Array.isArray(result?.declarations) ? result.declarations : Array.isArray(result?.results) ? result.results : [];
  const status = result?.status || "PENDING";
  const issues = Array.isArray(result?.violations) ? result.violations : [];
  return <div className="page result-page">
    <div className="page-heading"><div><span className="inspection-kicker">LABELMITRA / INSPECTION RESULT</span><h1>Inspection Result</h1><p>Review extracted declarations and compliance indicators before taking any official action.</p></div><Link className="secondary-btn-green" to="/scan">＋ New Inspection</Link></div>
    <div className="result-summary-green">
      <div><span>Inspection Status</span><strong>{String(status).toUpperCase()}</strong><small>AI-assisted result • Human review recommended</small></div>
      <div><span>Declarations Detected</span><strong>{declarations.length || "—"}</strong><small>Fields returned by analysis</small></div>
      <div><span>Potential Issues</span><strong>{issues.length || "—"}</strong><small>Requires review where applicable</small></div>
    </div>
    <section className="inspection-panel"><div className="panel-heading"><div className="panel-title"><div className="panel-index">01</div><div><h2>Detected declarations</h2><p>Extracted values are shown for verification.</p></div></div></div>{declarations.length ? <div className="result-table-green">{declarations.map((x,i)=><div key={i}><b>{String(x.field||"Field").replaceAll("_"," ")}</b><span>{x.value||"Not detected"}</span><em>{x.confidence!=null?`${Math.round(Number(x.confidence)*100)}% confidence`:"Review"}</em></div>)}</div> : <div className="empty-green">{result ? "The analysis returned a result, but no declaration list was provided." : "No inspection result is available yet. Start a new inspection to continue."}</div>}</section>
    {issues.length>0 && <section className="inspection-panel"><div className="panel-title"><div className="panel-index">02</div><div><h2>Potential compliance issues</h2><p>Items that may require review.</p></div></div>{issues.map((v,i)=><div className="issue-green" key={i}><b>!</b><div><strong>{v.rule||v.field||"Review required"}</strong><p>{v.message||v.reason||String(v)}</p></div></div>)}</section>}
  </div>;
}
