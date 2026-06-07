import type { ScenarioTemplate, WorkflowRequest } from '@/types/workflow'

export const SCENARIO_TEMPLATES: ScenarioTemplate[] = [
  {
    id: 'enterprise-platform',
    label: 'Enterprise platform design',
    query: 'How should we design an enterprise multi-agent AI platform?',
  },
  {
    id: 'observability',
    label: 'Agentic observability',
    query: 'What are the key components of agentic AI observability?',
  },
  {
    id: 'governance',
    label: 'AI governance',
    query: 'What governance controls should an enterprise agentic AI platform enforce?',
  },
  {
    id: 'cost-control',
    label: 'Cost governance',
    query: 'How can organizations control LLM costs in multi-agent workflows?',
  },
  {
    id: 'memory',
    label: 'Memory architecture',
    query: 'What memory architecture supports both short-term context and long-term knowledge?',
  },
]

interface QueryPanelProps {
  query: string
  flags: Pick<WorkflowRequest, 'enable_research' | 'enable_knowledge' | 'enable_summarization'>
  isRunning: boolean
  onQueryChange: (query: string) => void
  onFlagsChange: (flags: Pick<WorkflowRequest, 'enable_research' | 'enable_knowledge' | 'enable_summarization'>) => void
  onRun: () => void
  onReset: () => void
}

export function QueryPanel({
  query,
  flags,
  isRunning,
  onQueryChange,
  onFlagsChange,
  onRun,
  onReset,
}: QueryPanelProps) {
  return (
    <section className="flex h-full flex-col gap-4 rounded-xl border border-[var(--color-surface-border)] bg-[var(--color-surface-raised)] p-4">
      <div>
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Query</h2>
        <p className="mt-1 text-xs text-slate-500">Ask a business question or pick a scenario</p>
      </div>

      <textarea
        className="min-h-32 flex-1 resize-none rounded-lg border border-[var(--color-surface-border)] bg-[var(--color-surface)] px-3 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:border-[var(--color-accent)] focus:outline-none"
        placeholder="Enter your question..."
        value={query}
        onChange={(e) => onQueryChange(e.target.value)}
        disabled={isRunning}
      />

      <div className="flex flex-wrap gap-2">
        {SCENARIO_TEMPLATES.map((scenario) => (
          <button
            key={scenario.id}
            type="button"
            disabled={isRunning}
            onClick={() => onQueryChange(scenario.query)}
            className="rounded-full border border-[var(--color-surface-border)] bg-[var(--color-surface)] px-3 py-1 text-xs text-slate-300 transition hover:border-[var(--color-accent)] hover:text-white disabled:opacity-50"
          >
            {scenario.label}
          </button>
        ))}
      </div>

      <div className="space-y-2 rounded-lg border border-[var(--color-surface-border)] bg-[var(--color-surface)] p-3">
        <p className="text-xs font-medium text-slate-400">Agent toggles</p>
        {(
          [
            ['enable_research', 'Research'],
            ['enable_knowledge', 'Knowledge'],
            ['enable_summarization', 'Summarization'],
          ] as const
        ).map(([key, label]) => (
          <label key={key} className="flex cursor-pointer items-center gap-2 text-sm text-slate-300">
            <input
              type="checkbox"
              checked={flags[key]}
              disabled={isRunning}
              onChange={(e) => onFlagsChange({ ...flags, [key]: e.target.checked })}
              className="accent-[var(--color-accent)]"
            />
            {label}
          </label>
        ))}
      </div>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={onRun}
          disabled={isRunning || !query.trim()}
          className="flex-1 rounded-lg bg-[var(--color-accent)] px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {isRunning ? 'Running...' : 'Run workflow'}
        </button>
        <button
          type="button"
          onClick={onReset}
          disabled={isRunning}
          className="rounded-lg border border-[var(--color-surface-border)] px-4 py-2 text-sm text-slate-300 transition hover:border-slate-500 disabled:opacity-50"
        >
          Reset
        </button>
      </div>
    </section>
  )
}
