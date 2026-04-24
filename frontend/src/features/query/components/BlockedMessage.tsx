import type { BlockedResult } from '../types'

interface BlockedMessageProps {
  result: BlockedResult
}

export function BlockedMessage({ result }: BlockedMessageProps) {
  return (
    <div style={{ animation: 'fadeUp 0.4s ease' }}>
      <div style={{
        background: 'var(--surface)',
        border: '1px solid rgba(245,158,11,0.25)',
        borderRadius: 12, padding: '16px 20px',
        display: 'flex', gap: 14, alignItems: 'flex-start',
      }}>
        <div style={{
          width: 34, height: 34, borderRadius: 9, flexShrink: 0,
          background: 'rgba(245,158,11,0.1)',
          border: '1px solid rgba(245,158,11,0.2)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 15,
        }}>⚠️</div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#fbbf24', marginBottom: 6 }}>
            Esta consulta no está disponible
          </div>
          <p style={{ fontSize: 12.5, color: 'var(--text-muted)', lineHeight: 1.6, marginBottom: 6 }}>
            {humanize(result.block_reason)}
          </p>
          <p style={{ fontSize: 11.5, color: 'var(--text-muted)', opacity: 0.7 }}>
            Intentá reformular la pregunta o consultá con el administrador si creés que es un error.
          </p>
        </div>
      </div>
    </div>
  )
}

function humanize(reason: string): string {
  const lower = reason.toLowerCase()
  if (lower.includes('drop') || lower.includes('delete') || lower.includes('truncate'))
    return 'La consulta intenta eliminar datos, lo cual no está permitido.'
  if (lower.includes('insert') || lower.includes('update'))
    return 'La consulta intenta modificar datos. Solo se permiten consultas de lectura.'
  if (lower.includes('schema') || lower.includes('table') || lower.includes('column'))
    return 'La consulta accede a información estructural del sistema, lo cual no está habilitado.'
  if (lower.includes('timeout') || lower.includes('too long'))
    return 'La consulta tomó demasiado tiempo. Intentá una pregunta más específica.'
  return reason
}
