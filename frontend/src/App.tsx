import { useMemo } from 'react'
import { useQueryPoller } from '@/features/query/hooks/useQueryPoller'
import { QueryInput } from '@/features/query/components/QueryInput'
import { ResultDisplay } from '@/features/query/components/ResultDisplay'
import { BlockedMessage } from '@/features/query/components/BlockedMessage'
import { LoadingState } from '@/features/query/components/LoadingState'

// UUID generado una sola vez por sesión — nunca expuesto al usuario
const SESSION_USER_ID = crypto.randomUUID()

export default function App() {
  const userId = useMemo(() => SESSION_USER_ID, [])
  const { state, submit } = useQueryPoller(userId)

  return (
    <div className="min-h-screen bg-slate-950 px-4 py-12">
      <div className="mx-auto w-full max-w-2xl space-y-8">
        {/* Header */}
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">
            Consultá tus datos
          </h1>
          <p className="text-sm text-slate-500">
            Hacé preguntas en lenguaje natural y obtené respuestas directas.
          </p>
        </header>

        {/* Input */}
        <QueryInput
          onSubmit={submit}
          isLoading={state.status === 'loading'}
        />

        {/* Estados de resultado */}
        {state.status === 'loading' && <LoadingState />}

        {state.status === 'completed' && (
          <ResultDisplay result={state.result} />
        )}

        {state.status === 'blocked' && (
          <BlockedMessage result={state.result} />
        )}

        {state.status === 'error' && (
          <div className="rounded-xl border border-red-700/40 bg-red-900/10 p-4 text-sm text-red-400">
            {state.message}
          </div>
        )}
      </div>
    </div>
  )
}
