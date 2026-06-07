import { useState } from 'react'

import type { WorkflowHistoryEntry } from '@/types/workflow'

interface HistoryPanelProps {
  entries: WorkflowHistoryEntry[]
  activeRequestId: string | null
  isLoading: boolean
  onSelect: (requestId: string) => void
  onRefresh: () => void
}

function formatTime(timestamp: string): string {
  try {
    return new Date(timestamp).toLocaleString()
  } catch {
    return timestamp
  }
}

export function HistoryPanel({
  entries,
  activeRequestId,
  isLoading,
  onSelect,
  onRefresh,
}: HistoryPanelProps) {
  const [open, setOpen] = useState(true)

  return (
    <section className="rounded-xl border border-[var(--color-surface-border)] bg-[var(--color-surface-raised)] p-4">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between text-left"
      >
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Recent runs</h2>
          <p className="mt-1 text-xs text-slate-500">Last {entries.length} completed workflows</p>
        </div>
        <span className="text-xs text-slate-500">{open ? '−' : '+'}</span>
      </button>

      {open && (
        <div className="mt-3 space-y-2">
          <button
            type="button"
            onClick={onRefresh}
            disabled={isLoading}
            className="text-xs text-slate-400 transition hover:text-white disabled:opacity-50"
          >
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </button>

          {entries.length === 0 ? (
            <p className="text-xs text-slate-500">No completed runs yet</p>
          ) : (
            <ul className="max-h-64 space-y-2 overflow-y-auto">
              {entries.map((entry) => (
                <li key={entry.request_id}>
                  <button
                    type="button"
                    onClick={() => onSelect(entry.request_id)}
                    className={`w-full rounded-lg border px-3 py-2 text-left transition ${
                      activeRequestId === entry.request_id
                        ? 'border-[var(--color-accent)] bg-[var(--color-accent-muted)]'
                        : 'border-[var(--color-surface-border)] bg-[var(--color-surface)] hover:border-slate-500'
                    }`}
                  >
                    <p className="truncate text-xs text-slate-200">{entry.query}</p>
                    <div className="mt-1 flex flex-wrap gap-2 text-[10px] text-slate-500">
                      <span>{formatTime(entry.timestamp)}</span>
                      <span>${entry.cost_usd.toFixed(4)}</span>
                      {entry.scorecard_summary && (
                        <span>
                          grounded {(entry.scorecard_summary.groundedness * 100).toFixed(0)}%
                        </span>
                      )}
                    </div>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  )
}
