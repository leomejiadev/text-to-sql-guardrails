import { useState } from 'react'
import type { QueryResult } from '../types'

interface ResultDisplayProps {
  result: QueryResult
}

export function ResultDisplay({ result }: ResultDisplayProps) {
  const [sqlOpen, setSqlOpen] = useState(false)
  const [copied, setCopied] = useState(false)

  function copySQL() {
    navigator.clipboard.writeText(result.sql).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 1800)
    })
  }

  const rows = result.results
  const cols = rows.length > 0 ? Object.keys(rows[0]) : []

  return (
    <div style={{ animation: 'fadeUp 0.5s ease', display: 'flex', flexDirection: 'column', gap: 14 }}>

      {/* respuesta NL */}
      <div style={{
        background: 'var(--surface)',
        border: '1px solid var(--border2)',
        borderRadius: 12, padding: '16px 20px',
      }}>
        <div style={{
          fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
          textTransform: 'uppercase' as const, color: 'var(--text-muted)',
          marginBottom: 8, display: 'flex', alignItems: 'center', gap: 6,
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--cyan)', display: 'inline-block' }} />
          Respuesta
        </div>
        <p style={{ fontSize: 14, lineHeight: 1.7, color: 'var(--text)' }}>
          {result.response_hint}
        </p>
      </div>

      {/* tabla */}
      {rows.length > 0 && (
        <div style={{
          background: 'var(--surface)',
          border: '1px solid var(--border2)',
          borderRadius: 12, overflow: 'hidden',
        }}>
          <div style={{
            padding: '12px 20px',
            borderBottom: '1px solid var(--border)',
            fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
            textTransform: 'uppercase' as const, color: 'var(--text-muted)',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--purple)', display: 'inline-block' }} />
              Resultados · {rows.length} {rows.length === 1 ? 'fila' : 'filas'}
              {result.row_count > rows.length && ` (de ${result.row_count})`}
            </span>
          </div>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5, fontFamily: 'var(--font-mono)' }}>
              <thead>
                <tr style={{ background: 'rgba(255,255,255,0.03)' }}>
                  {cols.map(col => (
                    <th key={col} style={{
                      padding: '9px 16px', textAlign: 'left',
                      fontSize: 10, fontWeight: 600, letterSpacing: '0.08em',
                      textTransform: 'uppercase' as const, color: 'var(--text-muted)',
                      borderBottom: '1px solid var(--border)', whiteSpace: 'nowrap',
                    }}>{col.replace(/_/g, ' ')}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr
                    key={i}
                    style={{ borderBottom: i < rows.length - 1 ? '1px solid var(--border)' : 'none', transition: 'background 0.15s' }}
                    onMouseEnter={e => (e.currentTarget.style.background = 'rgba(255,255,255,0.025)')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >
                    {cols.map(col => (
                      <td key={col} style={{ padding: '9px 16px', color: 'var(--text-dim)', whiteSpace: 'nowrap' }}>
                        {String(row[col] ?? '—')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* tablas usadas */}
      {result.tables_used.length > 0 && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' as const, alignItems: 'center' }}>
          <span style={{ fontSize: 10.5, color: 'var(--text-muted)', fontWeight: 500, marginRight: 2 }}>
            Tablas usadas:
          </span>
          {result.tables_used.map(t => (
            <span key={t} style={{
              fontSize: 11, fontFamily: 'var(--font-mono)', fontWeight: 500,
              padding: '3px 10px',
              background: 'var(--purple-dim)',
              border: '1px solid rgba(124,58,237,0.25)',
              borderRadius: 20, color: 'oklch(75% 0.18 280)',
            }}>{t}</span>
          ))}
        </div>
      )}

      {/* SQL colapsable */}
      <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden' }}>
        <button
          type="button"
          onClick={() => setSqlOpen(o => !o)}
          style={{
            width: '100%', padding: '11px 20px',
            background: 'transparent', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            color: 'var(--text-dim)', fontSize: 12, fontWeight: 500,
            fontFamily: 'var(--font-body)',
          }}
        >
          <span style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
            <span style={{
              fontSize: 10, fontFamily: 'var(--font-mono)',
              background: 'rgba(255,255,255,0.06)',
              padding: '2px 7px', borderRadius: 4, color: 'var(--text-muted)',
            }}>SQL</span>
            {sqlOpen ? 'Ocultar query generado' : 'Ver query generado'}
          </span>
          <span style={{ transition: 'transform 0.25s', transform: sqlOpen ? 'rotate(180deg)' : 'none', fontSize: 10, opacity: 0.5 }}>▾</span>
        </button>
        {sqlOpen && (
          <div style={{ borderTop: '1px solid var(--border)' }}>
            <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '8px 16px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
              <button
                type="button"
                onClick={copySQL}
                style={{
                  background: 'rgba(255,255,255,0.05)',
                  border: '1px solid var(--border2)',
                  borderRadius: 6, padding: '4px 12px',
                  fontSize: 11, color: copied ? '#4ade80' : 'var(--text-dim)',
                  cursor: 'pointer', fontFamily: 'var(--font-body)', transition: 'color 0.2s',
                }}
              >
                {copied ? '✓ Copiado' : 'Copiar'}
              </button>
            </div>
            <pre style={{
              padding: '14px 20px',
              fontFamily: 'var(--font-mono)', fontSize: 12,
              color: 'var(--text-dim)', overflowX: 'auto',
              lineHeight: 1.7, margin: 0, background: 'rgba(0,0,0,0.2)',
            }}>{result.sql}</pre>
          </div>
        )}
      </div>
    </div>
  )
}
