import { useMemo, useState, useEffect, useRef } from 'react'
import { useQueryPoller } from '@/features/query/hooks/useQueryPoller'
import { QueryInput } from '@/features/query/components/QueryInput'
import { ResultDisplay } from '@/features/query/components/ResultDisplay'
import { BlockedMessage } from '@/features/query/components/BlockedMessage'
import { PipelineLoader } from '@/features/query/components/PipelineLoader'
import { HealthDot } from '@/features/query/components/HealthDot'
import { InfoBanner } from '@/features/query/components/InfoBanner'
import { DBContext } from '@/features/query/components/DBContext'

const SESSION_USER_ID = crypto.randomUUID()

export default function App() {
  const userId = useMemo(() => SESSION_USER_ID, [])
  const { state, submit } = useQueryPoller(userId)

  const [healthy, setHealthy] = useState(true)
  const [titleEditing, setTitleEditing] = useState(false)
  const [title, setTitle] = useState('text-to-sql · guardrails')
  const titleInputRef = useRef<HTMLInputElement>(null)
  const resultRef = useRef<HTMLDivElement>(null)

  const isLoading = state.status === 'loading'
  const showPipeline = isLoading || state.status === 'completed' || state.status === 'blocked'

  useEffect(() => {
    const base = import.meta.env.VITE_API_URL ?? ''
    fetch(`${base}/health`)
      .then(r => setHealthy(r.ok))
      .catch(() => setHealthy(false))
  }, [])

  useEffect(() => {
    if (state.status === 'completed' || state.status === 'blocked') {
      setTimeout(() => resultRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 150)
    }
  }, [state.status])

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>

      {/* health dot fixed */}
      <div style={{ position: 'fixed', top: 16, right: 20, zIndex: 100 }}>
        <HealthDot healthy={healthy} />
      </div>

      {/* header */}
      <header style={{
        padding: '40px 20px 24px',
        textAlign: 'center',
        borderBottom: '1px solid var(--border)',
        background: 'linear-gradient(180deg, rgba(11,13,20,0) 0%, rgba(11,13,20,0.6) 100%)',
      }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          {titleEditing ? (
            <input
              ref={titleInputRef}
              value={title}
              onChange={e => setTitle(e.target.value)}
              onBlur={() => setTitleEditing(false)}
              onKeyDown={e => { if (e.key === 'Enter') setTitleEditing(false) }}
              autoFocus
              style={{
                background: 'transparent', border: 'none',
                borderBottom: '2px solid var(--purple)',
                outline: 'none', color: 'var(--text)',
                fontSize: 34, fontFamily: 'var(--font-title)',
                fontWeight: 700, letterSpacing: '-0.02em',
                textAlign: 'center',
                width: `${Math.max(title.length, 10)}ch`,
              }}
            />
          ) : (
            <h1
              onClick={() => setTitleEditing(true)}
              title="Click para editar"
              style={{
                fontSize: 34, fontFamily: 'var(--font-title)',
                fontWeight: 700, letterSpacing: '-0.02em',
                color: 'var(--text)', cursor: 'text',
                userSelect: 'none', lineHeight: 1.1,
                display: 'flex', alignItems: 'center', gap: 6,
                margin: 0,
              }}
            >
              {title}
              <span style={{ fontSize: 12, color: 'var(--text-muted)', opacity: 0.4, fontFamily: 'var(--font-body)', fontWeight: 400 }}>✎</span>
            </h1>
          )}
        </div>
        <p style={{ fontSize: 14, color: 'var(--text-muted)', fontWeight: 400, letterSpacing: '0.01em' }}>
          Consultá los datos de tu database en lenguaje natural.
        </p>
      </header>

      {/* main */}
      <main style={{
        flex: 1,
        padding: '32px 20px 80px',
        maxWidth: 760, margin: '0 auto', width: '100%',
      }}>
        <div style={{ marginBottom: 14 }}>
          <InfoBanner />
        </div>

        <DBContext />

        <div style={{ marginBottom: 20 }}>
          <QueryInput onSubmit={submit} isLoading={isLoading} />
        </div>

        {showPipeline && (
          <PipelineLoader active={isLoading} />
        )}

        <div ref={resultRef}>
          {state.status === 'completed' && !isLoading && (
            <ResultDisplay result={state.result} />
          )}

          {state.status === 'blocked' && !isLoading && (
            <BlockedMessage result={state.result} />
          )}

          {state.status === 'error' && (
            <div style={{
              background: 'var(--surface)',
              border: '1px solid rgba(239,68,68,0.3)',
              borderRadius: 12, padding: '14px 18px',
              fontSize: 13, color: '#f87171',
              animation: 'fadeUp 0.4s ease',
            }}>
              {state.message}
            </div>
          )}
        </div>
      </main>

      {/* footer */}
      <footer style={{
        textAlign: 'center', padding: '18px 16px',
        borderTop: '1px solid var(--border)',
        fontSize: 11.5, color: 'var(--text-muted)',
        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ letterSpacing: '0.04em' }}>text-to-sql · guardrails</span>
          <span style={{ opacity: 0.3 }}>·</span>
          <span style={{ letterSpacing: '0.02em', opacity: 0.6 }}>RAG + LLM + Chain</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 11 }}>
          <span style={{ opacity: 0.5 }}>por</span>
          <span style={{ color: 'var(--text-dim)', fontWeight: 500 }}>Leonardo Mejía</span>
          <span style={{ opacity: 0.3 }}>·</span>
          <a
            href="https://github.com/leomejiadev/text-to-sql-guardrails"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: 'var(--text-muted)', textDecoration: 'none',
              display: 'flex', alignItems: 'center', gap: 5,
              transition: 'color 0.15s',
            }}
            onMouseEnter={e => (e.currentTarget.style.color = 'var(--text)')}
            onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-muted)')}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
            </svg>
            GitHub
          </a>
        </div>
      </footer>
    </div>
  )
}
