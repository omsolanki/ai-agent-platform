import type { AgentOutput, AgentRole, PipelineNodeState } from '@/types/workflow'

const NODE_META: Record<AgentRole, { title: string; description: string }> = {
  research: {
    title: 'Research',
    description: 'Gather and structure findings',
  },
  knowledge: {
    title: 'Knowledge',
    description: 'Retrieve and ground answers',
  },
  summarization: {
    title: 'Summarization',
    description: 'Executive summary & actions',
  },
}

const STATE_STYLES: Record<PipelineNodeState, string> = {
  pending: 'border-slate-600 bg-slate-800/50 text-slate-500',
  running: 'border-[var(--color-accent)] bg-[var(--color-accent-muted)] text-blue-200 animate-pulse',
  done: 'border-[var(--color-success)] bg-green-950/40 text-green-300',
  skipped: 'border-slate-700 bg-slate-900/50 text-slate-600 line-through',
  failed: 'border-[var(--color-danger)] bg-red-950/40 text-red-300',
}

const STATE_LABELS: Record<PipelineNodeState, string> = {
  pending: 'Pending',
  running: 'Running',
  done: 'Done',
  skipped: 'Skipped',
  failed: 'Failed',
}

interface PipelineVizProps {
  pipeline: AgentRole[]
  states: Record<AgentRole, PipelineNodeState>
  agentOutputs?: AgentOutput[]
}

export function PipelineViz({ pipeline, states, agentOutputs }: PipelineVizProps) {
  return (
    <section className="flex h-full flex-col gap-4 rounded-xl border border-[var(--color-surface-border)] bg-[var(--color-surface-raised)] p-4">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Agent pipeline</h2>
        <p className="mt-1 text-xs text-slate-500">Multi-agent orchestration — not a single LLM call</p>
      </div>

      <div className="flex flex-1 flex-col items-center justify-center gap-3 py-4">
        {pipeline.map((agent, index) => {
          const meta = NODE_META[agent]
          const state = states[agent]
          const output = agentOutputs?.find((o) => o.agent === agent)

          return (
            <div key={agent} className="flex w-full max-w-sm flex-col items-center gap-3">
              <div
                className={`w-full rounded-xl border-2 px-4 py-3 transition ${STATE_STYLES[state]}`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">{meta.title}</p>
                    <p className="text-xs opacity-80">{meta.description}</p>
                  </div>
                  <span className="rounded-full bg-black/20 px-2 py-0.5 text-xs font-medium">
                    {STATE_LABELS[state]}
                  </span>
                </div>
                {output && state === 'done' && (
                  <div className="mt-2 flex gap-3 border-t border-white/10 pt-2 text-xs opacity-70">
                    <span>{output.tokens_used} tokens</span>
                    <span>{output.latency_ms.toFixed(0)} ms</span>
                    {output.model && <span>{output.model}</span>}
                  </div>
                )}
              </div>
              {index < pipeline.length - 1 && (
                <div className="h-6 w-0.5 bg-[var(--color-surface-border)]" />
              )}
            </div>
          )
        })}
      </div>
    </section>
  )
}
