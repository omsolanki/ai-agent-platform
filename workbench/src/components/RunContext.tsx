import { useState } from 'react'

import { copyToClipboard } from '@/utils/copy'

interface RunContextProps {
  requestId: string | null
  traceId: string | null
}

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    const ok = await copyToClipboard(value)
    if (ok) {
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    }
  }

  return (
    <div className="flex items-center gap-2 rounded-lg border border-[var(--color-surface-border)] bg-[var(--color-surface)] px-3 py-2">
      <div className="min-w-0 flex-1">
        <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
        <p className="truncate font-mono text-xs text-slate-300">{value}</p>
      </div>
      <button
        type="button"
        onClick={() => void handleCopy()}
        className="shrink-0 rounded px-2 py-1 text-xs text-slate-400 transition hover:bg-slate-800 hover:text-white"
      >
        {copied ? 'Copied' : 'Copy'}
      </button>
    </div>
  )
}

export function RunContext({ requestId, traceId }: RunContextProps) {
  if (!requestId) return null

  const jaegerBase = import.meta.env.VITE_JAEGER_URL as string | undefined
  const jaegerHref = traceId && jaegerBase ? `${jaegerBase.replace(/\/$/, '')}/trace/${traceId}` : null

  return (
    <section className="rounded-xl border border-[var(--color-surface-border)] bg-[var(--color-surface-raised)] p-4">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Run context</h2>
      <p className="mt-1 text-xs text-slate-500">Request and trace identifiers for ops/debugging</p>
      <div className="mt-3 space-y-2">
        <CopyField label="Request ID" value={requestId} />
        {traceId && <CopyField label="Trace ID" value={traceId} />}
      </div>
      {jaegerHref && (
        <a
          href={jaegerHref}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-block text-xs text-[var(--color-accent)] hover:underline"
        >
          View trace in Jaeger →
        </a>
      )}
    </section>
  )
}
