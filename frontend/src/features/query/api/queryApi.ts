import type { QueryRequest, TaskCreatedResponse, PollResult } from '../types'

const BASE_URL = import.meta.env.VITE_API_URL

export async function submitQuery(payload: QueryRequest): Promise<TaskCreatedResponse> {
  const res = await fetch(`${BASE_URL}/api/v1/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error(`Error al enviar la consulta: ${res.status}`)
  return res.json() as Promise<TaskCreatedResponse>
}

export async function pollQuery(taskId: string): Promise<PollResult> {
  const res = await fetch(`${BASE_URL}/api/v1/query/${taskId}`)

  // 422 = guardrails bloquearon la query — no es un error de red, es resultado válido
  if (res.status === 422) {
    const body = await res.json() as { detail: string }
    return { status: 'blocked', blocked: true, block_reason: body.detail }
  }

  // 500 = error de ejecución del pipeline (ej: SQL inválido por columna inexistente)
  if (res.status === 500) {
    const body = await res.json() as { detail: string }
    console.error('[pollQuery] error de ejecución:', body.detail)
    throw new Error('No se pudo completar la consulta. Intentá reformular la pregunta.')
  }

  if (!res.ok) throw new Error(`Error al consultar el resultado: ${res.status}`)

  const data = await res.json() as Record<string, unknown>

  // 202 = sigue procesando
  if (data['status'] === 'processing') return { status: 'processing' }

  // 200 = completado — el backend no envía "status", lo inyectamos acá
  return { status: 'completed', ...data } as PollResult
}
