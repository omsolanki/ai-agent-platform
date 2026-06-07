import type { CostEstimate, FinalResponse } from '@/types/workflow'

interface CostPanelProps {
  estimate: CostEstimate | null
  result: FinalResponse | null
  phase: string
}

function formatUsd(value: number): string {
  if (value < 0.01) return `$${value.toFixed(4)}`
  return `$${value.toFixed(3)}`
}

export function CostPanel({ estimate, result, phase }: CostPanelProps) {
  return (
    <section className="rounded-xl border border-[var(--color-surface-border)] bg-[var(--color-surface-raised)] p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Cost</h2>
      <p className="mt-1 text-xs text-slate-500">Estimate before run · actuals after</p>

      <div className="mt-4 space-y-3">
        {estimate ? (
          <div className="rounded-lg border border-[var(--color-surface-border)] bg-[var(--color-surface)] p-3">
            <p className="text-xs text-slate-400">Pre-run estimate</p>
            <p className="mt-1 text-xl font-semibold text-amber-300">
              {formatUsd(estimate.estimated_cost_usd)}
            </p>
            <p className="mt-1 text-xs text-slate-500">
              ~{estimate.estimated_tokens.toLocaleString()} tokens · {estimate.strategy.replace(/_/g, ' ')}
            </p>
            <p className="mt-2 text-xs text-slate-500">
              Agents: {estimate.agents.map((a) => a.replace('_agent', '')).join(' → ')}
            </p>
          </div>
        ) : (
          <p className="text-xs text-slate-500">
            {phase === 'idle' ? 'Run a workflow to see cost estimate' : 'Calculating...'}
          </p>
        )}

        {result && (
          <div className="rounded-lg border border-green-900/50 bg-green-950/20 p-3">
            <p className="text-xs text-slate-400">Actual</p>
            <p className="mt-1 text-xl font-semibold text-green-300">
              {formatUsd(result.total_cost_usd)}
            </p>
            <div className="mt-2 flex gap-4 text-xs text-slate-400">
              <span>{result.total_tokens.toLocaleString()} tokens</span>
              <span>{result.total_latency_ms.toFixed(0)} ms</span>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
