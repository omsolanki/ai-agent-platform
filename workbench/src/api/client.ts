import type {
  CostEstimate,
  EvaluationScorecard,
  GovernanceResult,
  HealthResponse,
  WorkflowHistoryDetail,
  WorkflowHistoryEntry,
  WorkflowRequest,
  WorkflowResponse,
  WorkflowRunResponse,
} from '@/types/workflow'

const API_BASE = '/api/v1'

export class GovernanceBlockedError extends Error {
  governance: GovernanceResult

  constructor(message: string, governance: GovernanceResult) {
    super(message)
    this.name = 'GovernanceBlockedError'
    this.governance = governance
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...init?.headers },
    ...init,
  })

  if (!response.ok) {
    const body = await response.text()
    try {
      const parsed = JSON.parse(body) as {
        detail?: string | { message?: string; governance?: GovernanceResult }
      }
      const detail = parsed.detail
      if (typeof detail === 'object' && detail?.governance) {
        throw new GovernanceBlockedError(
          detail.message ?? 'Governance check failed',
          detail.governance,
        )
      }
      const message = typeof detail === 'string' ? detail : JSON.stringify(detail)
      throw new Error(message || `Request failed (${response.status})`)
    } catch (err) {
      if (err instanceof GovernanceBlockedError) throw err
      throw new Error(body || `Request failed (${response.status})`)
    }
  }

  return response.json() as Promise<T>
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export function estimateCost(body: WorkflowRequest): Promise<CostEstimate> {
  return request<CostEstimate>('/workflow/estimate-cost', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function executeWorkflow(body: WorkflowRequest): Promise<WorkflowResponse> {
  return request<WorkflowResponse>('/workflow/execute', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function runWorkflow(body: WorkflowRequest): Promise<WorkflowRunResponse> {
  return request<WorkflowRunResponse>('/workflow/run', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function evaluateWorkflow(body: WorkflowRequest): Promise<EvaluationScorecard> {
  return request<EvaluationScorecard>('/workflow/evaluate', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function getWorkflowHistory(limit = 10): Promise<WorkflowHistoryEntry[]> {
  return request<WorkflowHistoryEntry[]>(`/workflow/history?limit=${limit}`)
}

export function getWorkflowHistoryDetail(requestId: string): Promise<WorkflowHistoryDetail> {
  return request<WorkflowHistoryDetail>(`/workflow/history/${requestId}`)
}

export type StreamEventHandler = (event: string, data: unknown) => void

function parseSseBuffer(buffer: string): { events: Array<{ event: string; data: string }>; rest: string } {
  const events: Array<{ event: string; data: string }> = []
  const parts = buffer.split('\n\n')
  const rest = parts.pop() ?? ''

  for (const part of parts) {
    if (!part.trim()) continue
    let event = 'message'
    let data = ''
    for (const line of part.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      if (line.startsWith('data:')) data = line.slice(5).trim()
    }
    if (data) events.push({ event, data })
  }

  return { events, rest }
}

export async function executeWorkflowStream(
  body: WorkflowRequest,
  onEvent: StreamEventHandler,
): Promise<void> {
  const response = await fetch(`${API_BASE}/workflow/execute/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(body),
  })

  if (!response.ok) {
    const text = await response.text()
    try {
      const parsed = JSON.parse(text) as {
        detail?: string | { message?: string; governance?: GovernanceResult }
      }
      const detail = parsed.detail
      if (typeof detail === 'object' && detail?.governance) {
        throw new GovernanceBlockedError(
          detail.message ?? 'Governance check failed',
          detail.governance,
        )
      }
      throw new Error(typeof detail === 'string' ? detail : text)
    } catch (err) {
      if (err instanceof GovernanceBlockedError) throw err
      throw new Error(text || `Stream failed (${response.status})`)
    }
  }

  const reader = response.body?.getReader()
  if (!reader) throw new Error('No response body')

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const { events, rest } = parseSseBuffer(buffer)
    buffer = rest

    for (const { event, data } of events) {
      onEvent(event, JSON.parse(data) as unknown)
    }
  }

  if (buffer.trim()) {
    const { events } = parseSseBuffer(`${buffer}\n\n`)
    for (const { event, data } of events) {
      onEvent(event, JSON.parse(data) as unknown)
    }
  }
}
