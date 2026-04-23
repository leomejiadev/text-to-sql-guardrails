import { useState, useRef, useCallback } from 'react'
import { submitQuery, pollQuery } from '../api/queryApi'
import type { QueryResult, BlockedResult } from '../types'

type PollerState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'completed'; result: QueryResult }
  | { status: 'blocked'; result: BlockedResult }
  | { status: 'error'; message: string }

export function useQueryPoller(userId: string) {
  const [state, setState] = useState<PollerState>({ status: 'idle' })
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }, [])

  const submit = useCallback(
    async (query: string) => {
      setState({ status: 'loading' })
      stopPolling()

      try {
        const { task_id } = await submitQuery({ query, user_id: userId })

        intervalRef.current = setInterval(async () => {
          try {
            const poll = await pollQuery(task_id)

            if (poll.status === 'processing') return

            stopPolling()

            if (poll.status === 'completed') {
              setState({ status: 'completed', result: poll })
            } else if (poll.status === 'blocked') {
              setState({ status: 'blocked', result: poll })
            }
          } catch (err) {
            stopPolling()
            const message = err instanceof Error ? err.message : 'No se pudo obtener el resultado.'
            setState({ status: 'error', message })
          }
        }, 2000)
      } catch {
        setState({ status: 'error', message: 'No se pudo enviar la consulta.' })
      }
    },
    [userId, stopPolling],
  )

  return { state, submit }
}
