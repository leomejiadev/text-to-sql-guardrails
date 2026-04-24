interface HealthDotProps {
  healthy: boolean
}

export function HealthDot({ healthy }: HealthDotProps) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '5px 10px',
      background: healthy ? 'rgba(34,197,94,0.08)' : 'rgba(239,68,68,0.08)',
      border: `1px solid ${healthy ? 'rgba(34,197,94,0.2)' : 'rgba(239,68,68,0.2)'}`,
      borderRadius: 20,
      fontSize: 11, fontWeight: 500, letterSpacing: '0.03em',
      color: healthy ? '#4ade80' : '#f87171',
      userSelect: 'none',
      fontFamily: 'var(--font-body)',
    }}>
      <span style={{
        width: 7, height: 7, borderRadius: '50%',
        background: healthy ? '#22c55e' : '#ef4444',
        boxShadow: `0 0 6px ${healthy ? '#22c55e' : '#ef4444'}`,
        animation: healthy ? 'pulse-dot 2s ease-in-out infinite' : 'none',
        flexShrink: 0,
        display: 'inline-block',
      }} />
      {healthy ? 'online' : 'offline'}
    </div>
  )
}
