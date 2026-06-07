export type AgentRole = 'research' | 'knowledge' | 'summarization'

export type WorkflowStatus = 'pending' | 'running' | 'completed' | 'failed' | 'retrying'

export type PipelineNodeState = 'pending' | 'running' | 'done' | 'skipped' | 'failed'

export interface ConfidenceIndicator {
  score: number
  rationale: string
  source_count: number
}

export interface ResearchFinding {
  topic: string
  findings: string[]
  references: string[]
  confidence: ConfidenceIndicator
  metadata: Record<string, unknown>
}

export interface GroundedResponse {
  answer: string
  citations: string[]
  confidence: ConfidenceIndicator
  retrieved_chunks: number
}

export interface ActionItem {
  description: string
  priority: string
  owner: string | null
}

export interface ExecutiveSummary {
  headline: string
  key_insights: string[]
  action_items: ActionItem[]
  detailed_summary: string
}

export interface AgentOutput {
  agent: AgentRole
  output: Record<string, unknown>
  tokens_used: number
  latency_ms: number
  model: string
  success: boolean
  error: string | null
}

export interface FinalResponse {
  request_id: string
  trace_id?: string | null
  executive_summary: ExecutiveSummary
  grounded_response: GroundedResponse | null
  research_findings: ResearchFinding | null
  agent_outputs: AgentOutput[]
  total_tokens: number
  total_cost_usd: number
  total_latency_ms: number
  status: WorkflowStatus
}

export interface WorkflowRequest {
  query: string
  session_id?: string | null
  context?: Record<string, unknown>
  enable_research?: boolean
  enable_knowledge?: boolean
  enable_summarization?: boolean
}

export interface GovernanceCheck {
  name: string
  passed: boolean
  reason: string
}

export interface GovernanceResult {
  passed: boolean
  checks: GovernanceCheck[]
}

export interface WorkflowResponse {
  request_id: string
  status: WorkflowStatus
  result: FinalResponse | null
  error: string | null
  governance: GovernanceResult | null
  created_at: string
}

export interface WorkflowRunResponse {
  result: FinalResponse
  scorecard: EvaluationScorecard
  governance: GovernanceResult
  routing: CostEstimate
}

export interface EvaluationScorecard {
  request_id: string
  task_completion: number
  answer_quality: number
  groundedness: number
  hallucination_rate: number
  agent_accuracy: number
  workflow_success: boolean
  latency_ms: number
  cost_usd: number
  cost_efficiency: number
  notes: string
}

export interface CostEstimate {
  strategy: string
  agents: string[]
  estimated_cost_usd: number
  estimated_tokens: number
}

export interface HealthResponse {
  status: string
  service: string
  version: string
}

export interface ScenarioTemplate {
  id: string
  label: string
  query: string
}

export interface ScorecardSummary {
  task_completion: number
  groundedness: number
  hallucination_rate: number
  workflow_success: boolean
}

export interface WorkflowHistoryEntry {
  request_id: string
  trace_id: string | null
  query: string
  status: WorkflowStatus
  cost_usd: number
  latency_ms: number
  timestamp: string
  scorecard_summary: ScorecardSummary | null
}

export interface WorkflowHistoryDetail extends WorkflowHistoryEntry {
  result: FinalResponse
  scorecard: EvaluationScorecard | null
  governance: GovernanceResult | null
}
