import type { BlockedResult } from '../types'

interface BlockedMessageProps {
  result: BlockedResult
}

export function BlockedMessage({ result }: BlockedMessageProps) {
  return (
    <div className="w-full rounded-xl border border-amber-700/40 bg-amber-900/10 p-6">
      <div className="flex items-start gap-3">
        <WarningIcon />

        <div className="space-y-2">
          <p className="font-medium text-amber-300">
            Esta consulta no está disponible
          </p>
          <p className="text-sm leading-relaxed text-slate-400">
            {humanize(result.block_reason)}
          </p>
          <p className="text-xs text-slate-500">
            Intentá reformular la pregunta o consultá con el administrador si creés que es un error.
          </p>
        </div>
      </div>
    </div>
  )
}

// Traduce block_reason técnico a lenguaje simple para usuarios de negocio
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

  // Fallback: mostrar el motivo original limpio si no matchea ningún patrón conocido
  return reason
}

function WarningIcon() {
  return (
    <svg
      className="mt-0.5 h-5 w-5 shrink-0 text-amber-400"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      aria-hidden="true"
    >
      <path
        d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  )
}
