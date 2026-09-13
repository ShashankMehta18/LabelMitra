import { NavLink } from "react-router-dom";

export default function Layout({ children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark"><img src="/assets/labelmitra-mark.png" alt="LabelMitra" /></div>
          <div className="brand-copy">
            <strong>LabelMitra</strong>
            <small>AI-powered label assistant</small>
          </div>
        </div>

        <div className="nav-section">
          <span className="nav-label">Legal Metrology</span>
          <nav className="nav">
            <NavLink to="/" end><span className="nav-icon">⌂</span><span>Dashboard</span></NavLink>
            <NavLink to="/scan"><span className="nav-icon">＋</span><span>New Inspection</span></NavLink>
            <NavLink to="/result"><span className="nav-icon">✓</span><span>Inspection Results</span></NavLink>
          </nav>
        </div>

        <div className="nav-section food-nav-section">
          <span className="nav-label">Food Intelligence</span>
          <nav className="nav">
            <NavLink to="/quality"><span className="nav-icon food-nav-icon">✦</span><span>Analyse Food</span></NavLink>
          </nav>
        </div>

        <div className="sidebar-bottom">
          <div className="system-status">
            <span className="status-dot" />
            <div><strong>LabelMitra System</strong><span>Ready for analysis</span></div>
          </div>
          <div className="sidebar-version">AI-assisted • Compliance + Food Intelligence</div>
        </div>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-title"><strong>LabelMitra</strong><span>Product Intelligence Workspace</span></div>
          <div className="officer"><span className="officer-status" /><span>Inspector</span><span className="officer-arrow">▾</span></div>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}
