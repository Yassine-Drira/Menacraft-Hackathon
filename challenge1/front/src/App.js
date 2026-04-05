import React, { useState, useRef, useCallback } from 'react';

/* ─── Global Styles ──────────────────────────────────────────────────────── */
const globalStyles = `
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:       #050508;
    --surface:  #0e0e14;
    --border:   #1e1e2e;
    --accent:   #00ffe7;
    --danger:   #ff3b5c;
    --safe:     #00e676;
    --muted:    #5a5a7a;
    --text:     #e8e8f0;
    --mono:     'Space Mono', monospace;
    --display:  'Syne', sans-serif;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: var(--mono);
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Scanline overlay */
  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background: repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(0,0,0,0.06) 2px,
      rgba(0,0,0,0.06) 4px
    );
    pointer-events: none;
    z-index: 9999;
  }

  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: .4; }
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
  @keyframes slideUp {
    from { transform: translateY(20px); opacity: 0; }
    to   { transform: translateY(0);    opacity: 1; }
  }
  @keyframes glitch {
    0%   { clip-path: inset(40% 0 61% 0); transform: translate(-2px, 0); }
    20%  { clip-path: inset(92% 0 1%  0); transform: translate( 2px, 0); }
    40%  { clip-path: inset(43% 0 50% 0); transform: translate(-2px, 0); }
    60%  { clip-path: inset(25% 0 58% 0); transform: translate( 2px, 0); }
    80%  { clip-path: inset(54% 0 7%  0); transform: translate(-2px, 0); }
    100% { clip-path: inset(58% 0 43% 0); transform: translate( 0,   0); }
  }
  @keyframes flicker {
    0%, 19.999%, 22%, 62.999%, 64%, 64.999%, 70%, 100% { opacity: 1; }
    20%,  21.999%, 63%, 63.999%, 65%, 69.999%           { opacity: .6; }
  }
`;

/* ─── Inject styles ──────────────────────────────────────────────────────── */
const styleEl = document.createElement('style');
styleEl.textContent = globalStyles;
document.head.appendChild(styleEl);

/* ─── Utility ────────────────────────────────────────────────────────────── */
const API = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function fmt(n) { return (n * 100).toFixed(1) + '%'; }

/* ─── Sub-components ─────────────────────────────────────────────────────── */
function ScannerRing({ active }) {
  return (
    <div style={{
      width: 160, height: 160, borderRadius: '50%',
      border: `2px solid ${active ? 'var(--accent)' : 'var(--border)'}`,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      position: 'relative',
      boxShadow: active ? '0 0 30px rgba(0,255,231,.25)' : 'none',
      transition: 'all .4s ease',
    }}>
      {/* spinning arc */}
      {active && (
        <div style={{
          position: 'absolute', inset: -6,
          border: '3px solid transparent',
          borderTopColor: 'var(--accent)',
          borderRadius: '50%',
          animation: 'spin .9s linear infinite',
        }} />
      )}
      {/* inner ring */}
      <div style={{
        width: 120, height: 120, borderRadius: '50%',
        border: `1px solid ${active ? 'rgba(0,255,231,.3)' : 'var(--border)'}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <span style={{ fontSize: 42 }}>🎭</span>
      </div>
    </div>
  );
}

function ProgressBar({ value, color }) {
  return (
    <div style={{
      height: 6, background: 'var(--border)', borderRadius: 3, overflow: 'hidden',
    }}>
      <div style={{
        height: '100%', width: `${value * 100}%`,
        background: color, borderRadius: 3,
        transition: 'width .6s cubic-bezier(.4,0,.2,1)',
        boxShadow: `0 0 8px ${color}88`,
      }} />
    </div>
  );
}

function ResultCard({ result }) {
  const isFake = result.label === 'FAKE';
  const color = isFake ? 'var(--danger)' : 'var(--safe)';

  return (
    <div style={{
      background: 'var(--surface)',
      border: `1px solid ${color}44`,
      borderRadius: 12, padding: '24px 28px',
      animation: 'slideUp .35s ease',
      boxShadow: `0 0 40px ${color}18`,
    }}>
      {/* Verdict */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
        <div style={{
          width: 48, height: 48, borderRadius: 8,
          background: `${color}22`, border: `1px solid ${color}`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 22,
        }}>
          {isFake ? '⚠️' : '✅'}
        </div>
        <div>
          <div style={{
            fontFamily: 'var(--display)', fontWeight: 800,
            fontSize: 26, color, letterSpacing: 3,
            animation: isFake ? 'flicker 3s infinite' : 'none',
          }}>
            {result.label}
          </div>
          <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 2 }}>
            CONFIDENCE: {fmt(result.confidence)}
          </div>
        </div>
      </div>

      {/* Bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 11, color: 'var(--muted)' }}>
            <span>FAKE PROBABILITY</span><span style={{ color: 'var(--danger)' }}>{fmt(result.prob_fake)}</span>
          </div>
          <ProgressBar value={result.prob_fake} color="var(--danger)" />
        </div>
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 11, color: 'var(--muted)' }}>
            <span>REAL PROBABILITY</span><span style={{ color: 'var(--safe)' }}>{fmt(result.prob_real)}</span>
          </div>
          <ProgressBar value={result.prob_real} color="var(--safe)" />
        </div>
      </div>

      {/* Meta */}
      {(result.frames_used || result.grid_size) && (
        <div style={{
          marginTop: 20, paddingTop: 16,
          borderTop: '1px solid var(--border)',
          display: 'flex', gap: 24,
        }}>
          {result.frames_used && (
            <div>
              <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 2 }}>FRAMES USED</div>
              <div style={{ fontSize: 14 }}>{result.frames_used}</div>
            </div>
          )}
          {result.grid_size && (
            <div>
              <div style={{ fontSize: 10, color: 'var(--muted)', marginBottom: 2 }}>GRID</div>
              <div style={{ fontSize: 14 }}>{result.grid_size}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function DropZone({ onFile, accept, label, icon }) {
  const [drag, setDrag] = useState(false);
  const inputRef = useRef();

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDrag(false);
    const f = e.dataTransfer.files[0];
    if (f) onFile(f);
  }, [onFile]);

  return (
    <div
      onClick={() => inputRef.current.click()}
      onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
      onDragLeave={() => setDrag(false)}
      onDrop={handleDrop}
      style={{
        border: `1.5px dashed ${drag ? 'var(--accent)' : 'var(--border)'}`,
        borderRadius: 10, padding: '28px 20px',
        textAlign: 'center', cursor: 'pointer',
        background: drag ? 'rgba(0,255,231,.04)' : 'transparent',
        transition: 'all .2s ease',
      }}
    >
      <input
        ref={inputRef} type="file" accept={accept}
        style={{ display: 'none' }}
        onChange={(e) => e.target.files[0] && onFile(e.target.files[0])}
      />
      <div style={{ fontSize: 28, marginBottom: 10 }}>{icon}</div>
      <div style={{ fontSize: 12, color: 'var(--muted)', lineHeight: 1.6 }}>
        {label}<br />
        <span style={{ color: 'var(--accent)', fontSize: 11 }}>click or drag & drop</span>
      </div>
    </div>
  );
}

/* ─── Main App ───────────────────────────────────────────────────────────── */
export default function App() {
  const [tab, setTab] = useState('video');          // 'video' | 'image'
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [health, setHealth] = useState(null);

  /* health-check on mount */
  React.useEffect(() => {
    fetch(`${API}/health`)
      .then(r => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: 'unreachable' }));
  }, []);

  const handleFile = useCallback((f) => {
    setFile(f);
    setResult(null);
    setError(null);
    if (f.type.startsWith('image/')) {
      const url = URL.createObjectURL(f);
      setPreview(url);
    } else {
      setPreview(null);
    }
  }, []);

  const analyse = useCallback(async () => {
    if (!file) return;
    setLoading(true); setResult(null); setError(null);
    const form = new FormData();
    form.append('file', file);
    const endpoint = tab === 'video' ? '/predict/video' : '/predict/image';
    try {
      const res = await fetch(`${API}${endpoint}`, { method: 'POST', body: form });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        throw new Error(e.detail || `HTTP ${res.status}`);
      }
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [file, tab]);

  const reset = () => { setFile(null); setPreview(null); setResult(null); setError(null); };

  const healthColor = !health ? 'var(--muted)'
    : health.status === 'ok' ? 'var(--safe)' : 'var(--danger)';

  return (
    <div style={{ minHeight: '100vh', padding: '40px 20px' }}>
      {/* ── Header ── */}
      <header style={{ maxWidth: 680, margin: '0 auto 48px', textAlign: 'center' }}>
        <div style={{
          display: 'inline-block', marginBottom: 8,
          fontFamily: 'var(--mono)', fontSize: 11,
          color: 'var(--accent)', letterSpacing: 4,
          borderBottom: '1px solid var(--accent)', paddingBottom: 4,
        }}>
          FORENSIC MEDIA ANALYSIS SYSTEM
        </div>
        <h1 style={{
          fontFamily: 'var(--display)', fontWeight: 800,
          fontSize: 'clamp(32px, 6vw, 52px)', letterSpacing: -1,
          lineHeight: 1.05,
          background: 'linear-gradient(135deg, #fff 40%, var(--accent))',
          WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
        }}>
          DeepFake<br />Detector
        </h1>
        <p style={{ color: 'var(--muted)', marginTop: 12, fontSize: 13, lineHeight: 1.6 }}>
          Thumbnail-grid EfficientNet-B0 · Frame-temporal analysis
        </p>

        {/* status pill */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 7,
          marginTop: 16, padding: '5px 14px',
          background: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: 999, fontSize: 11,
        }}>
          <span style={{
            width: 7, height: 7, borderRadius: '50%',
            background: healthColor,
            animation: health?.status === 'ok' ? 'pulse 2s infinite' : 'none',
          }} />
          <span style={{ color: healthColor }}>
            {!health ? 'CONNECTING…'
              : health.status === 'ok'
                ? `ONLINE · ${health.device?.toUpperCase()} · MODEL ${health.model_loaded ? 'LOADED' : 'NOT LOADED'}`
                : 'BACKEND UNREACHABLE'}
          </span>
        </div>
      </header>

      {/* ── Card ── */}
      <main style={{
        maxWidth: 680, margin: '0 auto',
        background: 'var(--surface)', border: '1px solid var(--border)',
        borderRadius: 16, overflow: 'hidden',
      }}>
        {/* Tab bar */}
        <div style={{ display: 'flex', borderBottom: '1px solid var(--border)' }}>
          {['video', 'image'].map(t => (
            <button
              key={t}
              onClick={() => { setTab(t); reset(); }}
              style={{
                flex: 1, padding: '16px 0',
                background: tab === t ? 'rgba(0,255,231,.06)' : 'transparent',
                border: 'none',
                borderBottom: tab === t ? '2px solid var(--accent)' : '2px solid transparent',
                color: tab === t ? 'var(--accent)' : 'var(--muted)',
                fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: 2,
                cursor: 'pointer', transition: 'all .2s',
              }}
            >
              {t === 'video' ? '▶  VIDEO' : '🖼  IMAGE'}
            </button>
          ))}
        </div>

        <div style={{ padding: 28 }}>
          {/* Scanner + drop area */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 28, marginBottom: 28 }}>
            <ScannerRing active={loading} />
            <div style={{ flex: 1 }}>
              {!file ? (
                <DropZone
                  onFile={handleFile}
                  accept={tab === 'video' ? 'video/*' : 'image/*'}
                  icon={tab === 'video' ? '🎬' : '🖼️'}
                  label={tab === 'video'
                    ? 'Upload a video file (.mp4, .avi, .mov…)'
                    : 'Upload an image file (.jpg, .png…)'}
                />
              ) : (
                <div style={{
                  background: 'var(--bg)', border: '1px solid var(--border)',
                  borderRadius: 10, padding: '14px 16px',
                  display: 'flex', alignItems: 'center', gap: 14,
                }}>
                  {preview
                    ? <img src={preview} alt="" style={{ width: 56, height: 56, borderRadius: 6, objectFit: 'cover' }} />
                    : <div style={{ width: 56, height: 56, borderRadius: 6, background: 'var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22 }}>🎬</div>
                  }
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontSize: 13, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {file.name}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 3 }}>
                      {(file.size / 1e6).toFixed(2)} MB
                    </div>
                  </div>
                  <button onClick={reset} style={{
                    background: 'none', border: '1px solid var(--border)',
                    borderRadius: 6, padding: '4px 10px',
                    color: 'var(--muted)', fontFamily: 'var(--mono)',
                    fontSize: 11, cursor: 'pointer',
                  }}>✕</button>
                </div>
              )}
            </div>
          </div>

          {/* Analyse button */}
          <button
            onClick={analyse}
            disabled={!file || loading}
            style={{
              width: '100%', padding: '14px 0',
              background: file && !loading ? 'var(--accent)' : 'var(--border)',
              border: 'none', borderRadius: 8,
              color: file && !loading ? '#050508' : 'var(--muted)',
              fontFamily: 'var(--display)', fontWeight: 700,
              fontSize: 14, letterSpacing: 2,
              cursor: file && !loading ? 'pointer' : 'not-allowed',
              transition: 'all .2s',
              boxShadow: file && !loading ? '0 0 20px rgba(0,255,231,.3)' : 'none',
            }}
          >
            {loading
              ? '⟳  ANALYSING…'
              : file ? 'RUN ANALYSIS' : 'SELECT A FILE FIRST'}
          </button>

          {/* Error */}
          {error && (
            <div style={{
              marginTop: 20, padding: '14px 16px',
              background: 'rgba(255,59,92,.08)',
              border: '1px solid rgba(255,59,92,.3)',
              borderRadius: 8, fontSize: 12, color: 'var(--danger)',
              animation: 'slideUp .3s ease',
            }}>
              ⚠ {error}
            </div>
          )}

          {/* Result */}
          {result && <div style={{ marginTop: 20 }}><ResultCard result={result} /></div>}
        </div>
      </main>

      {/* ── Footer ── */}
      <footer style={{ textAlign: 'center', marginTop: 40, color: 'var(--muted)', fontSize: 11, letterSpacing: 1 }}>
        THUMBNAIL-GRID DEEPFAKE DETECTOR · EFFICIENTNET-B0
      </footer>
    </div>
  );
}