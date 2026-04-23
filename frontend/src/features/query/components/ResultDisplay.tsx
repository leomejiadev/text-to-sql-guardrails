import { useState } from 'react'
import type { QueryResult } from '../types'

interface ResultDisplayProps {
  result: QueryResult
}

const confidenceConfig = {
  high:   { label: 'Alta confianza',  className: 'bg-emerald-900/50 text-emerald-400 ring-1 ring-emerald-500/30' },
  medium: { label: 'Confianza media', className: 'bg-amber-900/50 text-amber-400 ring-1 ring-amber-500/30' },
  low:    { label: 'Baja confianza',  className: 'bg-red-900/50 text-red-400 ring-1 ring-red-500/30' },
}

export function ResultDisplay({ result }: ResultDisplayProps) {
  const [sqlOpen, setSqlOpen] = useState(false)
  const conf = confidenceConfig[result.confidence]
  const isSingleValue = result.results.length === 1 && Object.keys(result.results[0]).length === 1

  return (
    <div className="w-full space-y-5 rounded-xl border border-slate-700 bg-slate-800/40 p-6">

      {/* Datos — protagonistas */}
      {isSingleValue ? (
        <SingleValue row={result.results[0]} hint={result.response_hint} />
      ) : (
        <ResultsTable rows={result.results} rowCount={result.row_count} hint={result.response_hint} />
      )}

      {/* Metadata: confianza + tablas */}
      <div className="flex flex-wrap items-center gap-2">
        <span className={`rounded-full px-3 py-1 text-xs font-medium ${conf.className}`}>
          {conf.label}
        </span>
        {result.tables_used.map((table) => (
          <span
            key={table}
            className="rounded-full bg-slate-700/60 px-3 py-1 text-xs text-slate-400 ring-1 ring-slate-600/40"
          >
            {table}
          </span>
        ))}
      </div>

      {/* SQL colapsable — secundario */}
      <div className="border-t border-slate-700/50 pt-3">
        <button
          type="button"
          onClick={() => setSqlOpen((o) => !o)}
          className="flex items-center gap-1.5 text-xs text-slate-500 transition-colors hover:text-slate-300"
        >
          <ChevronIcon open={sqlOpen} />
          {sqlOpen ? 'Ocultar' : 'Ver'} SQL generado
        </button>
        {sqlOpen && (
          <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-900 p-4 text-xs leading-relaxed text-slate-300">
            <code>{result.sql}</code>
          </pre>
        )}
      </div>
    </div>
  )
}

// Métrica única: número o valor grande centrado con la explicación debajo
function SingleValue({ row, hint }: { row: Record<string, unknown>; hint: string }) {
  const [key, value] = Object.entries(row)[0]
  return (
    <div className="space-y-1">
      <p className="text-5xl font-semibold tracking-tight text-slate-100">
        {String(value)}
      </p>
      <p className="text-sm text-slate-400">{formatColumnLabel(key)}</p>
      <p className="pt-1 text-sm leading-relaxed text-slate-500">{hint}</p>
    </div>
  )
}

// Tabla para múltiples filas o columnas
function ResultsTable({
  rows,
  rowCount,
  hint,
}: {
  rows: Record<string, unknown>[]
  rowCount: number
  hint: string
}) {
  if (rows.length === 0) {
    return <p className="text-sm text-slate-400">Sin resultados para esta consulta.</p>
  }

  const columns = Object.keys(rows[0])

  return (
    <div className="space-y-3">
      <p className="text-sm leading-relaxed text-slate-300">{hint}</p>
      <div className="overflow-x-auto rounded-lg border border-slate-700">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700 bg-slate-900/60">
              {columns.map((col) => (
                <th
                  key={col}
                  className="px-4 py-2.5 text-left text-xs font-medium uppercase tracking-wider text-slate-400"
                >
                  {formatColumnLabel(col)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={i}
                className="border-b border-slate-700/50 last:border-0 hover:bg-slate-700/20"
              >
                {columns.map((col) => (
                  <td key={col} className="px-4 py-2.5 text-slate-300">
                    {String(row[col] ?? '—')}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rowCount > rows.length && (
        <p className="text-xs text-slate-500">
          Mostrando {rows.length} de {rowCount} filas
        </p>
      )}
    </div>
  )
}

// Convierte snake_case a título legible: "cantidad_clientes" → "Cantidad clientes"
function formatColumnLabel(col: string): string {
  return col.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
}

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      className={`h-3.5 w-3.5 transition-transform ${open ? 'rotate-90' : ''}`}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      aria-hidden="true"
    >
      <path d="M9 18l6-6-6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}
