import type { EvaluationScorecard, FinalResponse } from '@/types/workflow'

export function exportExecutiveSummaryMarkdown(
  result: FinalResponse,
  scorecard: EvaluationScorecard | null,
): string {
  const { executive_summary, grounded_response, research_findings } = result
  const lines: string[] = [
    '# Executive Summary',
    '',
    `**Request ID:** ${result.request_id}`,
  ]

  if (result.trace_id) {
    lines.push(`**Trace ID:** ${result.trace_id}`)
  }

  lines.push(
    '',
    `## ${executive_summary.headline}`,
    '',
  )

  if (executive_summary.key_insights.length > 0) {
    lines.push('### Key insights', '')
    for (const insight of executive_summary.key_insights) {
      lines.push(`- ${insight}`)
    }
    lines.push('')
  }

  if (executive_summary.action_items.length > 0) {
    lines.push('### Action items', '')
    for (const item of executive_summary.action_items) {
      lines.push(`- [${item.priority}] ${item.description}`)
    }
    lines.push('')
  }

  if (executive_summary.detailed_summary) {
    lines.push('### Detailed summary', '', executive_summary.detailed_summary, '')
  }

  if (grounded_response) {
    lines.push('## Grounded answer', '', grounded_response.answer, '')
    if (grounded_response.citations.length > 0) {
      lines.push('### Citations', '')
      for (const citation of grounded_response.citations) {
        lines.push(`- ${citation}`)
      }
      lines.push('')
    }
  }

  if (research_findings) {
    lines.push(`## Research: ${research_findings.topic}`, '')
    for (const finding of research_findings.findings) {
      lines.push(`- ${finding}`)
    }
    lines.push('')
  }

  if (scorecard) {
    lines.push(
      '## Quality scorecard',
      '',
      `| Metric | Score |`,
      `|--------|-------|`,
      `| Task completion | ${(scorecard.task_completion * 100).toFixed(0)}% |`,
      `| Answer quality | ${(scorecard.answer_quality * 100).toFixed(0)}% |`,
      `| Groundedness | ${(scorecard.groundedness * 100).toFixed(0)}% |`,
      `| Hallucination rate | ${(scorecard.hallucination_rate * 100).toFixed(0)}% |`,
      `| Agent accuracy | ${(scorecard.agent_accuracy * 100).toFixed(0)}% |`,
      `| Cost efficiency | ${(scorecard.cost_efficiency * 100).toFixed(0)}% |`,
      '',
      `**Cost:** $${scorecard.cost_usd.toFixed(4)} · **Latency:** ${scorecard.latency_ms.toFixed(0)} ms`,
      '',
    )
  }

  lines.push(
    '---',
    `*Exported from Intelligence Workbench · ${new Date().toISOString()}*`,
  )

  return lines.join('\n')
}

export function downloadMarkdown(content: string, filename: string): void {
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}
