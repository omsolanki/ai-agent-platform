import { useState } from 'react'

import type { EvaluationScorecard, FinalResponse } from '@/types/workflow'
import { downloadMarkdown, exportExecutiveSummaryMarkdown } from '@/utils/exportSummary'

type TabId = 'executive' | 'grounded' | 'research'

const TABS: { id: TabId; label: string }[] = [
  { id: 'executive', label: 'Executive' },
  { id: 'grounded', label: 'Grounded' },
  { id: 'research', label: 'Research' },
]

interface ResultsTabsProps {
  result: FinalResponse | null
  scorecard: EvaluationScorecard | null
  phase: string
}

export function ResultsTabs({ result, scorecard, phase }: ResultsTabsProps) {
  const [activeTab, setActiveTab] = useState<TabId>('executive')

  if (!result) {
    return (
      <section className="flex h-full flex-col rounded-xl border border-[var(--color-surface-border)] bg-[var(--color-surface-raised)] p-4">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Results</h2>
        <div className="flex flex-1 items-center justify-center text-sm text-slate-500">
          {phase === 'idle' && 'Run a workflow to see executive-ready output'}
          {phase === 'estimating' && 'Estimating cost...'}
          {phase === 'running' && 'Agents are working...'}
          {phase === 'evaluating' && 'Evaluating quality...'}
          {phase === 'error' && 'No results — workflow failed'}
        </div>
      </section>
    )
  }

  const { executive_summary, grounded_response, research_findings } = result

  return (
    <section className="flex h-full flex-col rounded-xl border border-[var(--color-surface-border)] bg-[var(--color-surface-raised)] p-4">
      <div className="mb-4 flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Results</h2>
        <button
          type="button"
          onClick={() => {
            const md = exportExecutiveSummaryMarkdown(result, scorecard)
            downloadMarkdown(md, `executive-summary-${result.request_id.slice(0, 8)}.md`)
          }}
          className="rounded-lg border border-[var(--color-surface-border)] px-3 py-1 text-xs text-slate-300 transition hover:border-[var(--color-accent)] hover:text-white"
        >
          Export .md
        </button>
      </div>

      <div className="mb-4 flex gap-1 rounded-lg bg-[var(--color-surface)] p-1">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              activeTab === tab.id
                ? 'bg-[var(--color-accent-muted)] text-blue-200'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto text-sm leading-relaxed text-slate-200">
        {activeTab === 'executive' && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-white">{executive_summary.headline}</h3>
            {executive_summary.key_insights.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium uppercase text-slate-400">Key insights</p>
                <ul className="list-inside list-disc space-y-1 text-slate-300">
                  {executive_summary.key_insights.map((insight, i) => (
                    <li key={i}>{insight}</li>
                  ))}
                </ul>
              </div>
            )}
            {executive_summary.action_items.length > 0 && (
              <div>
                <p className="mb-2 text-xs font-medium uppercase text-slate-400">Action items</p>
                <ul className="space-y-2">
                  {executive_summary.action_items.map((item, i) => (
                    <li
                      key={i}
                      className="rounded-lg border border-[var(--color-surface-border)] bg-[var(--color-surface)] px-3 py-2"
                    >
                      <span className="text-slate-200">{item.description}</span>
                      <span className="ml-2 rounded bg-slate-700 px-1.5 py-0.5 text-xs text-slate-400">
                        {item.priority}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {executive_summary.detailed_summary && (
              <p className="text-slate-400">{executive_summary.detailed_summary}</p>
            )}
          </div>
        )}

        {activeTab === 'grounded' && (
          <div className="space-y-4">
            {grounded_response ? (
              <>
                <p>{grounded_response.answer}</p>
                <div className="rounded-lg border border-[var(--color-surface-border)] bg-[var(--color-surface)] p-3">
                  <p className="text-xs text-slate-400">
                    Confidence: {(grounded_response.confidence.score * 100).toFixed(0)}% ·{' '}
                    {grounded_response.retrieved_chunks} chunks retrieved
                  </p>
                </div>
                {grounded_response.citations.length > 0 && (
                  <div>
                    <p className="mb-2 text-xs font-medium uppercase text-slate-400">Citations</p>
                    <ul className="space-y-1 text-xs text-blue-300">
                      {grounded_response.citations.map((citation, i) => (
                        <li key={i}>{citation}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <p className="text-slate-500">Knowledge agent was not run for this workflow.</p>
            )}
          </div>
        )}

        {activeTab === 'research' && (
          <div className="space-y-4">
            {research_findings ? (
              <>
                <h3 className="font-semibold text-white">{research_findings.topic}</h3>
                <ul className="list-inside list-disc space-y-1">
                  {research_findings.findings.map((finding, i) => (
                    <li key={i}>{finding}</li>
                  ))}
                </ul>
                {research_findings.references.length > 0 && (
                  <div>
                    <p className="mb-2 text-xs font-medium uppercase text-slate-400">References</p>
                    <ul className="space-y-1 text-xs text-slate-400">
                      {research_findings.references.map((ref, i) => (
                        <li key={i}>{ref}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </>
            ) : (
              <p className="text-slate-500">Research agent was not run for this workflow.</p>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
