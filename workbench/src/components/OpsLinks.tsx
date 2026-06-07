import { useEffect, useState } from 'react'

import { getHealth } from '@/api/client'

const JAEGER_URL = import.meta.env.VITE_JAEGER_URL as string | undefined

export function OpsLinks() {
  const [health, setHealth] = useState<string>('checking...')

  useEffect(() => {
    getHealth()
      .then((h) => setHealth(`${h.status} · v${h.version}`))
      .catch(() => setHealth('unreachable'))
  }, [])

  const links = [
    { label: 'API docs', href: 'http://localhost:8000/docs' },
    { label: 'Grafana', href: 'http://localhost:3000' },
    { label: 'Metrics', href: 'http://localhost:8000/api/v1/metrics' },
    ...(JAEGER_URL ? [{ label: 'Jaeger', href: JAEGER_URL }] : []),
  ]

  return (
    <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-[var(--color-surface-border)] px-6 py-3 text-xs text-slate-500">
      <span>
        API health: <span className="text-slate-300">{health}</span>
      </span>
      <div className="flex gap-4">
        {links.map((link) => (
          <a
            key={link.label}
            href={link.href}
            target="_blank"
            rel="noreferrer"
            className="text-slate-400 transition hover:text-[var(--color-accent)]"
          >
            {link.label}
          </a>
        ))}
      </div>
    </footer>
  )
}
