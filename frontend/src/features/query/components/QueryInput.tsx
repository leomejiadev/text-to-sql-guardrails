import { useState, useRef, type FormEvent, type KeyboardEvent } from 'react'

const EXAMPLES = [
  '¿Cuáles fueron los 5 sucursales con mayores ventas en enero?',
  '¿Cuántos clientes hay por país?',
  '¿Cuál es el producto más vendido del último trimestre?',
  '¿Qué empleados trabajan en Buenos Aires?',
  'Dame los 5 clientes que más gastaron',
]

const MAX_LENGTH = 500

interface QueryInputProps {
  onSubmit: (query: string) => void
  isLoading: boolean
}

export function QueryInput({ onSubmit, isLoading }: QueryInputProps) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const trimmed = value.trim()
  const canSubmit = trimmed.length >= 3 && trimmed.length <= MAX_LENGTH && !isLoading

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (canSubmit) onSubmit(trimmed)
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      if (canSubmit) onSubmit(trimmed)
    }
  }

  return (
    <div>
      {/* textarea card */}
      <div
        style={{
          background: 'var(--surface)',
          border: '1px solid var(--border2)',
          borderRadius: 14,
          padding: '14px 16px',
          marginBottom: 12,
          transition: 'border-color 0.2s',
        }}
        onFocus={e => (e.currentTarget.style.borderColor = 'var(--purple)')}
        onBlur={e => (e.currentTarget.style.borderColor = 'var(--border2)')}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={e => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Preguntá algo sobre tus datos..."
          disabled={isLoading}
          maxLength={MAX_LENGTH}
          rows={3}
          style={{
            width: '100%', resize: 'none',
            background: 'transparent', border: 'none', outline: 'none',
            color: 'var(--text)', fontSize: 14.5,
            fontFamily: 'var(--font-body)', lineHeight: 1.6,
            caretColor: 'var(--purple)',
          }}
        />
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 8 }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            {navigator.platform?.includes('Mac') ? '⌘' : 'Ctrl'}+Enter para enviar
          </span>
          <button
            type="button"
            onClick={handleSubmit as unknown as React.MouseEventHandler}
            disabled={!canSubmit}
            style={{
              background: isLoading ? 'rgba(124,58,237,0.3)' : 'var(--purple)',
              border: 'none', borderRadius: 8,
              padding: '8px 20px',
              color: '#fff', fontSize: 13, fontWeight: 600,
              cursor: !canSubmit ? 'not-allowed' : 'pointer',
              fontFamily: 'var(--font-body)',
              opacity: !trimmed && !isLoading ? 0.4 : 1,
              transition: 'opacity 0.2s, background 0.2s',
              display: 'flex', alignItems: 'center', gap: 6,
            }}
          >
            {isLoading && (
              <span style={{
                width: 12, height: 12,
                border: '2px solid rgba(255,255,255,0.4)',
                borderTopColor: '#fff', borderRadius: '50%',
                display: 'inline-block',
                animation: 'spin 0.7s linear infinite',
              }} />
            )}
            Consultar
          </button>
        </div>
      </div>

      {/* example chips — siempre visibles */}
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' as const }}>
        {EXAMPLES.map(ex => (
          <button
            key={ex}
            type="button"
            onClick={() => { setValue(ex); textareaRef.current?.focus() }}
            style={{
              background: 'rgba(255,255,255,0.035)',
              border: '1px solid var(--border)',
              borderRadius: 20, padding: '5px 12px',
              color: 'var(--text-muted)', fontSize: 12,
              cursor: 'pointer', fontFamily: 'var(--font-body)',
              transition: 'border-color 0.15s, color 0.15s',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = 'var(--border2)'
              e.currentTarget.style.color = 'var(--text-dim)'
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = 'var(--border)'
              e.currentTarget.style.color = 'var(--text-muted)'
            }}
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  )
}
