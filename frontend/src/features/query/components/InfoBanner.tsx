const TAGS = ['RAG', 'LLM', 'Guardrails', 'SQL', 'Chain']

export function InfoBanner() {
  return (
    <div style={{
      background: 'var(--surface)',
      border: '1px solid var(--border)',
      borderRadius: 12,
      padding: '16px 20px',
      display: 'flex', gap: 16, alignItems: 'flex-start',
    }}>
      <div style={{
        width: 36, height: 36, borderRadius: 9,
        background: 'var(--purple-dim)',
        border: '1px solid rgba(124,58,237,0.25)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 16, flexShrink: 0,
      }}>⚡</div>
      <div>
        <div style={{ fontSize: 11.5, fontWeight: 600, color: 'var(--text)', marginBottom: 4 }}>
          Sobre este proyecto
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.65 }}>
          Sistema de consulta de bases de datos en lenguaje natural. Usando RAG para recuperar
          el esquema relevante, un LLM para generar la query SQL, y una cadena de guardrails
          que valida y protege cada paso antes de ejecutar y devolver los resultados.
        </p>
        <div style={{ marginTop: 10, display: 'flex', gap: 8, flexWrap: 'wrap' as const }}>
          {TAGS.map(tag => (
            <span key={tag} style={{
              fontSize: 10.5, fontFamily: 'var(--font-mono)',
              padding: '2px 8px',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border2)',
              borderRadius: 4,
              color: 'var(--text-muted)',
            }}>{tag}</span>
          ))}
        </div>
      </div>
    </div>
  )
}
