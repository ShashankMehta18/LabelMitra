import { Link } from "react-router-dom";

export default function Home() {
  return (
    <div className="page home-page">
      <section className="workspace-hero">
        <div>
          <div className="workspace-kicker"><span /> LABELMITRA • PRODUCT INTELLIGENCE</div>
          <h1>One platform.<br /><em>Two ways to understand a product.</em></h1>
          <p>Choose the workflow that matches your goal — verify legal declarations or understand what a food label means.</p>
        </div>
        <div className="workspace-badge"><span>LABELMITRA</span><strong>Product<br />Intelligence</strong><small>Evidence-led • AI-assisted</small></div>
      </section>

      <div className="choose-heading">
        <div><span>CHOOSE YOUR WORKFLOW</span><h2>What do you want to check?</h2></div>
        <p>Both tools use package-label evidence, but answer different questions.</p>
      </div>

      <section className="workflow-choice-grid">
        <article className="workflow-choice legal-choice">
          <div className="choice-top"><span className="choice-icon">⌁</span><span className="choice-audience">FOR INSPECTORS</span></div>
          <h2>Legal Metrology<br /><em>Inspection</em></h2>
          <p className="choice-question">“Is this packaged commodity compliant?”</p>
          <p>Capture package evidence and check mandatory declarations against the Legal Metrology requirements.</p>
          <div className="choice-tags"><span>OCR</span><span>Rule checks</span><span>Evidence</span><span>Inspection report</span></div>
          <Link className="choice-button legal-button" to="/scan">Start Legal Inspection <b>→</b></Link>
        </article>

        <article className="workflow-choice food-choice">
          <div className="choice-top"><span className="choice-icon">✦</span><span className="choice-audience">FOR CONSUMERS</span></div>
          <h2>Food<br /><em>Intelligence</em></h2>
          <p className="choice-question">“What am I actually eating?”</p>
          <p>Scan a food label to understand nutrition, ingredients, useful nutrients and potential concerns in simple language.</p>
          <div className="choice-tags"><span>Nutrition</span><span>Ingredients</span><span>Health signals</span><span>Food profile</span></div>
          <Link className="choice-button food-button" to="/quality">Analyse Food <b>→</b></Link>
        </article>
      </section>

      <section className="distinction-note">
        <div className="distinction-icon">i</div>
        <div><strong>Different purpose. Same evidence-first foundation.</strong><p>Legal Metrology helps an inspector verify declarations. Food Intelligence helps a consumer understand the information printed on a food label.</p></div>
      </section>

      <section className="stat-grid-green">
        {[
          ["Legal Inspections","No inspections recorded yet"],
          ["Products Inspected","No products scanned yet"],
          ["Needs Review","No review cases yet"],
          ["Potential Issues","No potential issues yet"]
        ].map(([title,sub]) => (
          <div className="green-stat" key={title}><span>{title}</span><strong>0</strong><small>{sub}</small></div>
        ))}
      </section>

      <section className="about-section-green" id="why-labelmitra">
        <div className="about-heading-green">
          <span className="inspection-kicker">WHY LABELMITRA?</span>
          <h2>Built around the label, not just the scan.</h2>
          <p>LabelMitra keeps the evidence visible, the analysis understandable and the next action clear.</p>
        </div>
        <div className="about-grid-green">
          {[
            ["01","Capture evidence","Use package photographs or live camera capture as the source for analysis."],
            ["02","Understand the label","Extract declarations, nutrition and ingredient information from visible evidence."],
            ["03","Trace the result","Keep findings connected to the evidence that produced them."],
            ["04","Review with confidence","Separate clear signals from information that still needs human verification."],
          ].map(([n,t,d]) => <article className="about-card-green" key={n}><span>{n}</span><h3>{t}</h3><p>{d}</p></article>)}
        </div>
      </section>
    </div>
  );
}
