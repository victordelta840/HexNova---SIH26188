"use client";

import { FormEvent, useEffect, useState, useRef } from "react";

type ScreeningResult = {
  case_id: string;
  screening_id: string;
  document_type: string;
  document_hash: string;
  audit_timestamp: string;
  audit_modules: string[];
  risk: { level: "low" | "medium" | "high"; score: number; reasons: string[] };
  ocr: { mode: string; message: string; confidence: number | null; fields: { name: string; value: string | null; status: string }[] };
  validation: { name: string; status: string; message: string }[];
  tampering: { assessment: string; message: string; risk_score: number; indicators: string[] };
  metadata: { status: string; format: string; width: number | null; height: number | null; findings: string[] };
  face_verification: { result: string; reason: string };
  face_comparison: { status: string; document_face: { status: string }; presented_face: { status: string }; comparison: { available: boolean; similarity_signal?: number | null; method: string }; review: { message: string } };
  audit_record_hash: string;
  integration_status: string;
};

type CaseSummary = { case_id: string; document_type: string; risk_level: string | null; risk_score: number | null; screening_status: string; created_at: string; completed_at: string | null; mode: string };
type DemoScenario = { id: string; name: string; description: string; document_type: string; document_label: string };
type CaseHistory = CaseSummary & { document_hash: string | null; audit_events: { event_type: string; module_name: string; status: string; timestamp: string; details: string }[]; ocr?: { message?: string; confidence?: number | null; fields?: { name: string; value: string | null; status: string }[] }; validation?: { name: string; status: string; message: string }[]; tampering?: { assessment?: string; risk_score?: number; indicators?: string[] }; metadata?: { status?: string; findings?: string[] }; face_comparison?: { status?: string; comparison?: { available?: boolean }; review?: { message?: string } }; risk?: { level?: string; score?: number; reasons?: string[] } };

const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
type AuthUser = { user_id: string; username: string; role: "OFFICER" | "ADMIN" };

export default function Home() {
  const [token, setToken] = useState<string | null>(null);
  const [authUser, setAuthUser] = useState<AuthUser | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [loginName, setLoginName] = useState("");
  const [loginPassword, setLoginPassword] = useState("");
  const [loginLoading, setLoginLoading] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [documentType, setDocumentType] = useState("passport");
  const [file, setFile] = useState<File | null>(null);
  const [presentedPerson, setPresentedPerson] = useState<File | null>(null);
  const [result, setResult] = useState<ScreeningResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState<CaseSummary[]>([]);
  const [demoScenarios, setDemoScenarios] = useState<DemoScenario[]>([]);
  const [demoLoading, setDemoLoading] = useState("");
  
  // Scroll Animation State
  const [activeSection, setActiveSection] = useState("hero");
  const observerRefs = useRef<(HTMLElement | null)[]>([]);

  useEffect(() => {
    const storedToken = sessionStorage.getItem("screening_access_token");
    const storedUser = sessionStorage.getItem("screening_user");
    if (storedToken && storedUser) { setToken(storedToken); setAuthUser(JSON.parse(storedUser)); }
    setAuthReady(true);
  }, []);

  useEffect(() => {
    if (authReady && token) {
        void loadDemoScenarios();
        void loadHistory();
    }
  }, [authReady, token]);

  // Setup Intersection Observer for Scroll Narrative
  useEffect(() => {
    if (!result) { setActiveSection("hero"); return; }
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) setActiveSection(entry.target.id);
        });
      },
      { threshold: 0.4 }
    );
    observerRefs.current.forEach((ref) => { if (ref) observer.observe(ref); });
    return () => observer.disconnect();
  }, [result]);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setLoginLoading(true); setLoginError("");
    try {
      const response = await fetch(`${apiBase}/auth/login`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: loginName, password: loginPassword }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "Invalid username or password.");
      sessionStorage.setItem("screening_access_token", payload.access_token); sessionStorage.setItem("screening_user", JSON.stringify(payload.user));
      setToken(payload.access_token); setAuthUser(payload.user); setLoginPassword("");
    } catch (requestError) { setLoginError(requestError instanceof Error ? requestError.message : "Invalid username or password."); }
    finally { setLoginLoading(false); }
  }

  function logout() {
    sessionStorage.removeItem("screening_access_token"); sessionStorage.removeItem("screening_user"); setToken(null); setAuthUser(null); setHistory([]); setResult(null);
  }

  function authenticatedRequest(input: RequestInfo | URL, init: RequestInit = {}) {
    const headers = new Headers(init.headers); if (token) headers.set("Authorization", `Bearer ${token}`); return fetch(input, { ...init, headers });
  }

  async function runDemo(scenario: DemoScenario) {
    setDemoLoading(scenario.id); setError("");
    try {
      const response = await authenticatedRequest(`${apiBase}/demo/scenarios/${scenario.id}/run`, { method: "POST" });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "The demonstration could not run.");
      setResult(payload); 
      setTimeout(() => document.getElementById("intake")?.scrollIntoView({ behavior: "smooth" }), 500);
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "The demonstration could not run."); }
    finally { setDemoLoading(""); }
  }

  async function loadDemoScenarios() {
    const response = await authenticatedRequest(`${apiBase}/demo/scenarios`);
    if (response.ok) setDemoScenarios(await response.json());
  }

  async function loadHistory() {
    try {
      const response = await authenticatedRequest(`${apiBase}/cases?page=1&page_size=10`);
      const payload = await response.json();
      if (response.ok) setHistory(payload.items);
    } catch (e) { console.error(e); }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) { setError("Select a document before starting screening."); return; }
    setLoading(true); setError(""); setResult(null);
    const form = new FormData(); form.append("document_type", documentType); form.append("document", file); if (presentedPerson) form.append("presented_person", presentedPerson);
    try {
      const response = await authenticatedRequest(`${apiBase}/screening/analyze`, { method: "POST", body: form });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail ?? "The screening request failed.");
      setResult(payload);
      setTimeout(() => document.getElementById("intake")?.scrollIntoView({ behavior: "smooth" }), 500);
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "The screening request failed."); }
    finally { setLoading(false); }
  }

  async function exportReport(caseId: string) {
    const response = await authenticatedRequest(`${apiBase}/cases/${encodeURIComponent(caseId)}/report`);
    if (!response.ok) return;
    const blob = await response.blob();
    const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = `${caseId}-screening-report.pdf`; link.click(); URL.revokeObjectURL(link.href);
  }

  if (!authReady) return null;
  if (!token || !authUser) return (
    <main className="cinematic-shell">
      <div className="space-bg"><div className="stars"></div></div>
      <section className="login-panel cinematic-glass">
        <div className="eyebrow">Clearance Desk · Secure Access</div>
        <h1>Authenticate</h1>
        <form onSubmit={login}>
          <label>Operator ID<input value={loginName} onChange={(e) => setLoginName(e.target.value)} required /></label>
          <label style={{ marginTop: 16 }}>Passkey<input type="password" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} required /></label>
          <button className="primary block-btn" type="submit" disabled={loginLoading}>{loginLoading ? "Authenticating..." : "Establish Connection"}</button>
          {loginError && <div className="error">{loginError}</div>}
        </form>
      </section>
    </main>
  );

  return (
    <main className="cinematic-shell" data-active-section={activeSection}>
      <header className="command-topbar">
        <div className="brand">CLEARANCE DESK <span className="command-tag">AI FORENSIC PIPELINE</span></div>
        <div className="topnote">{authUser.role} · {authUser.username} · DEMONSTRATION MODE <button onClick={logout}>Disconnect</button></div>
      </header>

      {/* FIXED 3D SCENE */}
      <div className="sticky-stage">
        <div className="space-bg"><div className="stars"></div><div className="nebula"></div></div>
        
        <div className="scene-container">
          <div className="document-model">
            <div className="doc-layer doc-base">
              <div className="doc-header">{result ? result.document_type.toUpperCase() : "AWAITING UPLOAD"}</div>
              <div className="doc-hash">{result ? result.document_hash.substring(0, 24) + "..." : "---"}</div>
              <div className="scanner-beam"></div>
            </div>
            {/* Forensic Layers */}
            <div className="doc-layer doc-forensic-1">METADATA LAYER</div>
            <div className="doc-layer doc-forensic-2">STRUCTURAL INTEGRITY</div>
            <div className="doc-layer doc-forensic-3">TAMPER SIGNALS</div>
          </div>
          
          {/* Face Comparison Geometry */}
          <div className="face-comparison-model">
            <div className="face-node document-face">DOC</div>
            <div className="face-link"></div>
            <div className="face-node presented-face">LIVE</div>
          </div>
        </div>
      </div>

      {/* SCROLLABLE NARRATIVE CONTENT */}
      <div className="narrative-content">
        
        {/* SECTION 1: HERO */}
        <section id="hero" className="narrative-section hero-section" ref={(el) => { observerRefs.current[0] = el; }}>
          <div className="hero-content">
            <div className="eyebrow">AI-POWERED IDENTITY SCREENING</div>
            <h1 className="cinematic-title">Analyze.<br/>Verify.<br/>Investigate.</h1>
            
            <form className="cinematic-glass upload-form" onSubmit={submit}>
              <div className="form-grid">
                <label>Document Type
                  <select value={documentType} onChange={(e) => setDocumentType(e.target.value)}>
                    <option value="passport">Passport</option>
                    <option value="visa">Visa</option>
                    <option value="national_id">National ID</option>
                  </select>
                </label>
                <label>Status <input value={loading ? "ANALYSIS IN PROGRESS..." : "READY FOR UPLOAD"} readOnly /></label>
              </div>
              
              {/* FIXED BULLETPROOF DROPZONES */}
              <label className="dropzone">
                <span className="dropzone-text">{file ? file.name : "+ Select Primary Document"}</span>
                <input type="file" style={{ display: 'none' }} onChange={(e) => setFile(e.target.files?.[0] ?? null)} accept="image/jpeg,image/png,application/pdf" />
              </label>
              
              <label className="dropzone">
                <span className="dropzone-text">{presentedPerson ? presentedPerson.name : "+ Select Presented Face (Optional)"}</span>
                <input type="file" style={{ display: 'none' }} onChange={(e) => setPresentedPerson(e.target.files?.[0] ?? null)} accept="image/jpeg,image/png" />
              </label>
              
              <button className="primary run-btn" type="submit" disabled={loading}>
                {loading ? "INITIALIZING FORENSICS..." : "START SCREENING"}
              </button>
              {error && <div className="error">{error}</div>}
            </form>

            {!result && (
              <div className="dashboard-extras">
                <div className="cinematic-glass extra-panel">
                  <div className="eyebrow">Simulation Lab</div>
                  <div className="demo-list">
                    {demoScenarios.map(sc => (
                      <button key={sc.id} onClick={() => runDemo(sc)} disabled={demoLoading !== ""}>
                        {demoLoading === sc.id ? "Running..." : `Run: ${sc.name}`}
                      </button>
                    ))}
                  </div>
                </div>
                <div className="cinematic-glass extra-panel">
                  <div className="eyebrow">Recent Cases</div>
                  {history.slice(0,3).map(h => (
                     <div key={h.case_id} className="history-line">{h.case_id} · {h.risk_level}</div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>

        {result && (
          <>
            {/* SECTION 2: INTAKE */}
            <section id="intake" className="narrative-section align-left" ref={(el) => { observerRefs.current[1] = el; }}>
              <div className="narrative-card cinematic-glass">
                <div className="eyebrow">Phase 01</div>
                <h2>DOCUMENT INGESTED</h2>
                <dl className="data-list">
                  <dt>Type</dt><dd>{result.document_type}</dd>
                  <dt>Status</dt><dd>Secured in processing chamber</dd>
                  <dt>Integrity Hash</dt><dd className="mono">{result.document_hash}</dd>
                </dl>
              </div>
            </section>

            {/* SECTION 3: SCANNING */}
            <section id="scanning" className="narrative-section align-right" ref={(el) => { observerRefs.current[2] = el; }}>
              <div className="narrative-card cinematic-glass">
                <div className="eyebrow">Phase 02</div>
                <h2>SCANNING PIPELINE</h2>
                <div className="conceptual-tags">
                  <span>OCR</span><span>METADATA</span><span>STRUCTURE</span><span>VISUAL FORENSICS</span>
                </div>
                <p className="narrative-desc">The document is being structurally mapped and normalized for AI evaluation.</p>
              </div>
            </section>

            {/* SECTION 4: OCR / IDENTITY */}
            <section id="ocr" className="narrative-section align-right" ref={(el) => { observerRefs.current[3] = el; }}>
              <div className="narrative-card cinematic-glass wide-card">
                <div className="eyebrow">Phase 03</div>
                <h2>EXTRACTED IDENTITY</h2>
                <div className="ocr-grid">
                  {result.ocr.fields.map(f => (
                    <div className="data-box" key={f.name}>
                      <div className="label">{f.name}</div>
                      <div className="value">{f.value ?? "Not detected"}</div>
                      <div className="status">{f.status}</div>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* SECTION 5: FORENSICS */}
            <section id="forensics" className="narrative-section align-left" ref={(el) => { observerRefs.current[4] = el; }}>
              <div className="narrative-card cinematic-glass">
                <div className="eyebrow">Phase 04</div>
                <h2>FORENSIC ANALYSIS</h2>
                <div className={`risk-badge risk-${result.tampering.risk_score > 50 ? 'high' : 'low'}`}>
                  Tamper Risk: {result.tampering.risk_score}/100
                </div>
                <ul className="forensic-list">
                  {result.tampering.indicators.length > 0 ? 
                    result.tampering.indicators.map(ind => <li key={ind}>{ind}</li>) : 
                    <li>No digital tampering indicators detected.</li>
                  }
                  {result.metadata.findings.map(finding => <li key={finding}>{finding}</li>)}
                </ul>
              </div>
            </section>

            {/* SECTION 6: FACE COMPARISON */}
            <section id="face" className="narrative-section align-center" ref={(el) => { observerRefs.current[5] = el; }}>
              <div className="narrative-card cinematic-glass">
                <div className="eyebrow">Phase 05</div>
                <h2>BIOMETRIC COMPARISON</h2>
                <div className="face-stats">
                  <div><span>Document Face</span><strong>{result.face_comparison.document_face.status}</strong></div>
                  <div><span>Presented Face</span><strong>{result.face_comparison.presented_face.status}</strong></div>
                </div>
                <div className="face-conclusion">
                   {result.face_comparison.review.message ?? "Human review required."}
                </div>
              </div>
            </section>

            {/* SECTION 7: RISK ENGINE */}
            <section id="risk" className="narrative-section align-center" ref={(el) => { observerRefs.current[6] = el; }}>
              <div className="narrative-card borderless transparent-bg">
                <div className="eyebrow">Phase 06 · SYSTEM ASSESSMENT</div>
                <div className={`huge-risk text-${result.risk.level}`}>
                  {result.risk.score} / 100<br/><span>{result.risk.level} RISK</span>
                </div>
                <ul className="risk-reasons cinematic-glass">
                  {result.risk.reasons.length > 0 ? 
                    result.risk.reasons.map(r => <li key={r}>{r}</li>) : 
                    <li>No severe risk indicators identified.</li>
                  }
                </ul>
              </div>
            </section>

            {/* SECTION 8: INTEGRITY / AUDIT */}
            <section id="integrity" className="narrative-section align-left" ref={(el) => { observerRefs.current[7] = el; }}>
              <div className="narrative-card cinematic-glass technical-card">
                <div className="eyebrow">Phase 07</div>
                <h2>DATABASE-BACKED INTEGRITY LEDGER</h2>
                <dl className="data-list">
                  <dt>Case ID</dt><dd>{result.case_id}</dd>
                  <dt>Audit Hash</dt><dd className="mono">{result.audit_record_hash}</dd>
                  <dt>Timestamp</dt><dd>{result.audit_timestamp}</dd>
                  <dt>Modules Executed</dt><dd>{result.audit_modules.join(" · ")}</dd>
                </dl>
              </div>
            </section>

            {/* SECTION 9: REPORT */}
            <section id="report" className="narrative-section align-center" ref={(el) => { observerRefs.current[8] = el; }}>
              <div className="narrative-card cinematic-glass summary-card">
                <h2>SCREENING COMPLETE</h2>
                <p>Case {result.case_id} has been recorded into the internal demonstration ledger.</p>
                <div className="action-row">
                  <button className="primary" onClick={() => exportReport(result.case_id)}>EXPORT SECURE PDF</button>
                  <button className="secondary" onClick={() => { setResult(null); window.scrollTo(0,0); }}>CLOSE CASE & RETURN</button>
                </div>
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}