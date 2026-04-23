export interface QueryRequest {
  query: string
  user_id: string
}

export interface TaskCreatedResponse {
  task_id: string
  status: 'queued'
  message: string
}

export interface QueryResult {
  status: 'completed'
  sql: string
  confidence: 'high' | 'medium' | 'low'
  tables_used: string[]
  detected_language: string
  response_hint: string
  results: Record<string, unknown>[]
  row_count: number
}

export interface BlockedResult {
  status: 'blocked'
  blocked: true
  block_reason: string
}

export interface ProcessingResult {
  status: 'processing'
}

export type PollResult = QueryResult | BlockedResult | ProcessingResult
