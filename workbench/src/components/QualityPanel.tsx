import type { EvaluationScorecard } from '@/types/workflow'

interface QualityPanelProps {
  scorecard: EvaluationScorecard | null
  phase: string
}

const METRICS: { key: keyof EvaluationScorecard; label: string; invert?: boolean }[] = [
  { key: 'task_completion', label: 'Task completion' },
  { key: 'answer_quality', label: 'Answer quality' },
  { key: 'groundedness', label: 'Groundedness' },
  { key: 'hallucination_rate', label: 'Hallucination', invert: true },
  { key: 'agent_accuracy', label: 'Agent accuracy' },
  { key: 'cost_efficiency', label: 'Cost efficiency' },
]

function scoreColor(value: number, invert?: boolean): string {
  const effective = invert ? 1 - value : value
  if (effective >= 0.8) return 'bg-green-500'
  if (effective >= 0.6) return 'bg-amber-500'
  return 'bg-red-500'
}

export function QualityPanel({ scorecard, phase }: QualityPanelProps) {
  return (
    <section className="rounded-xl border border-[var(--color-surface-border)] bg-[var(--color-surface-raised)] p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Quality passport</h2>
      <p className="mt-1 text-xs text-slate-500">Automated evaluation scorecard</p>

      {!scorecard ? (
        <p className="mt-4 text-xs text-slate-500">
          {phase === 'evaluating' ? 'Evaluating...' : 'Available after workflow completes'}
        </p>
      ) : (
        <div className="mt-4 space-y-3">
          {METRICS.map(({ key, label, invert }) => {
            const value = scorecard[key] as number
            const pct = Math.round(value * 100)
            return (
              <div key={key}>
                <div className="mb-1 flex justify-between text-xs">
                  <span className="text-slate-400">{label}</span>
                  <span className="text-slate-300">{pct}%</span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-[var(--color-surface)]">
                  <div
                    className={`h-full rounded-full transition-all ${scoreColor(value, invert)}`}
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            )
          })}
          {scorecard.notes && (
            <p className="mt-2 text-xs text-slate-500">{scorecard.notes}</p>
          )}
          <div className="mt-2 flex items-center gap-2 text-xs">
            <span
              className={`rounded-full px-2 py-0.5 ${
                scorecard.workflow_success
                  ? 'bg-green-950 text-green-400'
                  : 'bg-red-950 text-red-400'
              }`}
            >
              {scorecard.workflow_success ? 'Workflow passed' : 'Workflow failed'}
            </span>
          </div>
        </div>
      )}
    </section>
  )
}
