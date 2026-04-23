import { useState, type FormEvent, type KeyboardEvent } from 'react'

interface QueryInputProps {
  onSubmit: (query: string) => void
  isLoading: boolean
}

const EXAMPLES = [
  '¿Cuántos usuarios se registraron en marzo?',
  '¿Cuál es el producto más vendido del último trimestre?',
]

const MIN_LENGTH = 3
const MAX_LENGTH = 500

export function QueryInput({ onSubmit, isLoading }: QueryInputProps) {
  const [value, setValue] = useState('')

  const trimmed = value.trim()
  const isValid = trimmed.length >= MIN_LENGTH && trimmed.length <= MAX_LENGTH
  const canSubmit = isValid && !isLoading

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    if (canSubmit) onSubmit(trimmed)
  }

  // Enviar con Ctrl+Enter / Cmd+Enter sin bloquear saltos de línea normales
  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault()
      if (canSubmit) onSubmit(trimmed)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="relative">
        <textarea
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Preguntá algo sobre tus datos..."
          disabled={isLoading}
          maxLength={MAX_LENGTH}
          rows={3}
          className="w-full resize-none rounded-xl border border-slate-700 bg-slate-800/60 px-4 py-3.5 pr-28 text-slate-100 placeholder-slate-500 outline-none transition-colors focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={!canSubmit}
          className="absolute bottom-3 right-3 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {isLoading ? (
            <span className="flex items-center gap-2">
              <Spinner />
              Analizando
            </span>
          ) : (
            'Consultar'
          )}
        </button>
      </div>

      <div className="mt-3 space-y-1">
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            type="button"
            onClick={() => setValue(ex)}
            disabled={isLoading}
            className="block text-left text-xs text-slate-500 transition-colors hover:text-indigo-400 disabled:pointer-events-none"
          >
            Ej: {ex}
          </button>
        ))}
      </div>

      {value.length > MAX_LENGTH - 50 && (
        <p className="mt-1 text-right text-xs text-slate-500">
          {value.length}/{MAX_LENGTH}
        </p>
      )}
    </form>
  )
}

function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  )
}
