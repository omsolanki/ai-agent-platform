import type { GovernanceResult } from '@/types/workflow'

const CHECK_LABELS: Record<string, string> = {
  query_length: 'Query length',
  prompt_injection: 'Prompt injection',
  blocked_topics: 'Blocked topics',
  pii_detection: 'PII detection',
}

interface GovernanceBannerProps {
  governance: GovernanceResult | null
  blocked?: boolean
}

export function GovernanceBanner({ governance, blocked }: GovernanceBannerProps) {
  if (!governance && !blocked) {
    return null
  }

  const passed = governance?.passed ?? false
  const isBlocked = blocked || (governance !== null && !passed)

  return (
    <div
      className={`mx-6 mt-4 rounded-lg border px-4 py-3 ${
        isBlocked
          ? 'border-red-900/50 bg-red-950/30'
          : 'border-green-900/50 bg-green-950/20'
      }`}
    >
      <div className="flex items-center gap-2">
        <span
          className={`text-sm font-semibold ${isBlocked ? 'text-red-300' : 'text-green-300'}`}
        >
          {isBlocked ? 'Governance gate — blocked' : 'Governance gate — passed'}
        </span>
      </div>

      {governance && (
        <ul className="mt-2 flex flex-wrap gap-3">
          {governance.checks.map((check) => (
            <li
              key={check.name}
              className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs ${
                check.passed
                  ? 'bg-green-950/50 text-green-400'
                  : 'bg-red-950/50 text-red-400'
              }`}
              title={check.reason || undefined}
            >
              <span>{check.passed ? '✓' : '✗'}</span>
              <span>{CHECK_LABELS[check.name] ?? check.name}</span>
            </li>
          ))}
        </ul>
      )}

      {isBlocked && governance && (
        <p className="mt-2 text-xs text-red-300/80">
          {governance.checks.find((c) => !c.passed)?.reason ?? 'Request blocked by governance policy'}
        </p>
      )}
    </div>
  )
}
