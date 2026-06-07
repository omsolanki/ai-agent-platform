import { useCallback, useEffect, useState } from 'react'

import {
  GovernanceBlockedError,
  estimateCost,
  executeWorkflowStream,
  getWorkflowHistory,
  getWorkflowHistoryDetail,
  runWorkflow,
} from '@/api/client'
import type {
  AgentOutput,
  AgentRole,
  CostEstimate,
  EvaluationScorecard,
  FinalResponse,
  GovernanceResult,
  PipelineNodeState,
  WorkflowHistoryEntry,
  WorkflowRequest,
} from '@/types/workflow'

export type WorkflowPhase = 'idle' | 'estimating' | 'running' | 'evaluating' | 'done' | 'error'

const AGENT_PIPELINE: AgentRole[] = ['research', 'knowledge', 'summarization']

const AGENT_NODE_MAP: Record<string, AgentRole> = {
  research_agent: 'research',
  knowledge_agent: 'knowledge',
  summarization_agent: 'summarization',
}

const AGENT_LABELS: Record<AgentRole, string> = {
  research: 'Research',
  knowledge: 'Knowledge',
  summarization: 'Summarization',
}

export function buildPipelineStates(
  agentOutputs: FinalResponse['agent_outputs'] | undefined,
  phase: WorkflowPhase,
  runningAgent?: AgentRole | null,
): Record<AgentRole, PipelineNodeState> {
  const states: Record<AgentRole, PipelineNodeState> = {
    research: 'pending',
    knowledge: 'pending',
    summarization: 'pending',
  }

  const completed = new Set(agentOutputs?.map((o) => o.agent) ?? [])

  if (phase === 'running') {
    for (const agent of AGENT_PIPELINE) {
      if (completed.has(agent)) {
        states[agent] = 'done'
      } else if (agent === runningAgent) {
        states[agent] = 'running'
      }
    }
    if (!runningAgent && !completed.size) {
      states.research = 'running'
    }
    return states
  }

  if (!agentOutputs?.length) {
    return states
  }

  const ran = new Set(agentOutputs.map((o) => o.agent))
  for (const agent of AGENT_PIPELINE) {
    const output = agentOutputs.find((o) => o.agent === agent)
    if (!ran.has(agent)) {
      states[agent] = 'skipped'
    } else if (output && !output.success) {
      states[agent] = 'failed'
    } else {
      states[agent] = 'done'
    }
  }

  return states
}

export interface WorkflowState {
  phase: WorkflowPhase
  costEstimate: CostEstimate | null
  result: FinalResponse | null
  scorecard: EvaluationScorecard | null
  governance: GovernanceResult | null
  governanceBlocked: boolean
  pipelineStates: Record<AgentRole, PipelineNodeState>
  partialOutputs: AgentOutput[]
  error: string | null
  requestId: string | null
  traceId: string | null
  historyEntries: WorkflowHistoryEntry[]
  historyLoading: boolean
}

const initialState: WorkflowState = {
  phase: 'idle',
  costEstimate: null,
  result: null,
  scorecard: null,
  governance: null,
  governanceBlocked: false,
  pipelineStates: {
    research: 'pending',
    knowledge: 'pending',
    summarization: 'pending',
  },
  partialOutputs: [],
  error: null,
  requestId: null,
  traceId: null,
  historyEntries: [],
  historyLoading: false,
}

export function useWorkflow() {
  const [state, setState] = useState<WorkflowState>(initialState)

  const refreshHistory = useCallback(async () => {
    setState((prev) => ({ ...prev, historyLoading: true }))
    try {
      const entries = await getWorkflowHistory(10)
      setState((prev) => ({ ...prev, historyEntries: entries, historyLoading: false }))
    } catch {
      setState((prev) => ({ ...prev, historyLoading: false }))
    }
  }, [])

  useEffect(() => {
    void refreshHistory()
  }, [refreshHistory])

  const applyRunResponse = useCallback(
    (result: FinalResponse, scorecard: EvaluationScorecard, governance: GovernanceResult) => {
      setState((prev) => ({
        ...prev,
        phase: 'done',
        result,
        scorecard,
        governance,
        requestId: result.request_id,
        traceId: result.trace_id ?? null,
        partialOutputs: result.agent_outputs,
        pipelineStates: buildPipelineStates(result.agent_outputs, 'done'),
      }))
      void refreshHistory()
    },
    [refreshHistory],
  )

  const loadFromHistory = useCallback(async (requestId: string) => {
    try {
      const detail = await getWorkflowHistoryDetail(requestId)
      setState((prev) => ({
        ...prev,
        phase: 'done',
        result: detail.result,
        scorecard: detail.scorecard,
        governance: detail.governance,
        requestId: detail.request_id,
        traceId: detail.trace_id,
        partialOutputs: detail.result.agent_outputs,
        pipelineStates: buildPipelineStates(detail.result.agent_outputs, 'done'),
        error: null,
        governanceBlocked: false,
      }))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load run'
      setState((prev) => ({ ...prev, error: message }))
    }
  }, [])

  const runWithStream = useCallback(
    async (request: WorkflowRequest) => {
      let runningAgent: AgentRole | null = null
      const partialOutputs: AgentOutput[] = []

      await executeWorkflowStream(request, (event, data) => {
        const payload = data as Record<string, unknown>

        if (event === 'governance') {
          const governance = payload as unknown as GovernanceResult
          setState((prev) => ({ ...prev, governance }))
        }

        if (event === 'agent_start') {
          const agentName = payload.agent as string
          runningAgent = AGENT_NODE_MAP[agentName] ?? null
          setState((prev) => ({
            ...prev,
            phase: 'running',
            pipelineStates: buildPipelineStates(partialOutputs, 'running', runningAgent),
          }))
        }

        if (event === 'agent_done') {
          const agentName = payload.agent as string
          const role = AGENT_NODE_MAP[agentName]
          if (role) {
            partialOutputs.push({
              agent: role,
              output: {},
              tokens_used: (payload.tokens_used as number) ?? 0,
              latency_ms: (payload.latency_ms as number) ?? 0,
              model: (payload.model as string) ?? '',
              success: (payload.success as boolean) ?? true,
              error: (payload.error as string | null) ?? null,
            })
          }
          runningAgent = null
          setState((prev) => ({
            ...prev,
            partialOutputs: [...partialOutputs],
            pipelineStates: buildPipelineStates(partialOutputs, 'running', runningAgent),
          }))
        }

        if (event === 'complete') {
          const result = (payload.result as FinalResponse) ?? null
          if (result) {
            setState((prev) => ({
              ...prev,
              phase: 'evaluating',
              result,
              requestId: result.request_id,
              traceId: result.trace_id ?? null,
              partialOutputs: result.agent_outputs,
              pipelineStates: buildPipelineStates(result.agent_outputs, 'done'),
            }))
          }
        }

        if (event === 'scorecard') {
          const scorecard = payload as unknown as EvaluationScorecard
          setState((prev) => ({
            ...prev,
            phase: 'done',
            scorecard,
          }))
          void refreshHistory()
        }

        if (event === 'error') {
          throw new Error((payload.message as string) ?? 'Workflow stream error')
        }
      })
    },
    [refreshHistory],
  )

  const runWithBatch = useCallback(
    async (request: WorkflowRequest) => {
      setState((prev) => ({ ...prev, phase: 'running' }))
      const response = await runWorkflow(request)
      applyRunResponse(response.result, response.scorecard, response.governance)
    },
    [applyRunResponse],
  )

  const run = useCallback(
    async (request: WorkflowRequest) => {
      setState((prev) => ({
        ...initialState,
        phase: 'estimating',
        historyEntries: prev.historyEntries,
      }))

      try {
        const costEstimate = await estimateCost(request)
        setState((prev) => ({
          ...prev,
          costEstimate,
          phase: 'running',
          pipelineStates: buildPipelineStates(undefined, 'running', 'research'),
        }))

        try {
          await runWithStream(request)
        } catch (streamErr) {
          if (streamErr instanceof GovernanceBlockedError) throw streamErr
          console.warn('SSE stream unavailable, falling back to /workflow/run', streamErr)
          await runWithBatch(request)
        }
      } catch (err) {
        if (err instanceof GovernanceBlockedError) {
          setState((prev) => ({
            ...prev,
            phase: 'error',
            governance: err.governance,
            governanceBlocked: true,
            error: err.message,
          }))
          return
        }
        const message = err instanceof Error ? err.message : 'Unknown error'
        setState((prev) => ({
          ...prev,
          phase: 'error',
          error: message,
        }))
      }
    },
    [runWithStream, runWithBatch],
  )

  const reset = useCallback(() => {
    setState((prev) => ({
      ...initialState,
      historyEntries: prev.historyEntries,
    }))
  }, [])

  return {
    ...state,
    run,
    reset,
    refreshHistory,
    loadFromHistory,
    agentLabels: AGENT_LABELS,
    agentPipeline: AGENT_PIPELINE,
    agentOutputs: state.result?.agent_outputs ?? state.partialOutputs,
  }
}
