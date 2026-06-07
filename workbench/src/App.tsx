import { useState } from 'react'

import { CostPanel } from '@/components/CostPanel'
import { GovernanceBanner } from '@/components/GovernanceBanner'
import { HistoryPanel } from '@/components/HistoryPanel'
import { OpsLinks } from '@/components/OpsLinks'
import { PipelineViz } from '@/components/PipelineViz'
import { QualityPanel } from '@/components/QualityPanel'
import { QueryPanel } from '@/components/QueryPanel'
import { ResultsTabs } from '@/components/ResultsTabs'
import { RunContext } from '@/components/RunContext'
import { useWorkflow } from '@/hooks/useWorkflow'
import type { WorkflowRequest } from '@/types/workflow'

const DEFAULT_FLAGS = {
  enable_research: true,
  enable_knowledge: true,
  enable_summarization: true,
}

export default function App() {
  const [query, setQuery] = useState('')
  const [flags, setFlags] = useState(DEFAULT_FLAGS)

  const {
    phase,
    costEstimate,
    result,
    scorecard,
    pipelineStates,
    governance,
    governanceBlocked,
    error,
    requestId,
    traceId,
    historyEntries,
    historyLoading,
    run,
    reset,
    refreshHistory,
    loadFromHistory,
    agentPipeline,
    agentOutputs,
  } = useWorkflow()

  const isRunning = phase === 'estimating' || phase === 'running' || phase === 'evaluating'

  const handleRun = () => {
    const request: WorkflowRequest = { query: query.trim(), ...flags }
    void run(request)
  }

  const handleReset = () => {
    setQuery('')
    setFlags(DEFAULT_FLAGS)
    reset()
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-[var(--color-surface-border)] bg-[var(--color-surface-raised)] px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-white">Intelligence Workbench</h1>
            <p className="text-xs text-slate-400">
              Enterprise agentic AI — governed, observable, cost-controlled
            </p>
          </div>
          {phase !== 'idle' && (
            <span className="rounded-full border border-[var(--color-surface-border)] px-3 py-1 text-xs capitalize text-slate-300">
              {phase}
            </span>
          )}
        </div>
      </header>

      <GovernanceBanner governance={governance} blocked={governanceBlocked} />

      {error && !governanceBlocked && (
        <div className="mx-6 mt-4 rounded-lg border border-red-900/50 bg-red-950/30 px-4 py-3 text-sm text-red-300">
          {error}
        </div>
      )}

      <main className="grid flex-1 grid-cols-1 gap-4 p-4 lg:grid-cols-12 lg:p-6">
        <div className="flex flex-col gap-4 lg:col-span-3">
          <QueryPanel
            query={query}
            flags={flags}
            isRunning={isRunning}
            onQueryChange={setQuery}
            onFlagsChange={(f) =>
              setFlags({
                enable_research: f.enable_research ?? true,
                enable_knowledge: f.enable_knowledge ?? true,
                enable_summarization: f.enable_summarization ?? true,
              })
            }
            onRun={handleRun}
            onReset={handleReset}
          />
          <HistoryPanel
            entries={historyEntries}
            activeRequestId={requestId}
            isLoading={historyLoading}
            onSelect={(id) => void loadFromHistory(id)}
            onRefresh={() => void refreshHistory()}
          />
        </div>

        <div className="lg:col-span-3">
          <PipelineViz
            pipeline={agentPipeline}
            states={pipelineStates}
            agentOutputs={agentOutputs}
          />
        </div>

        <div className="flex flex-col gap-4 lg:col-span-6">
          <ResultsTabs result={result} scorecard={scorecard} phase={phase} />
          <RunContext requestId={requestId} traceId={traceId} />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <CostPanel estimate={costEstimate} result={result} phase={phase} />
            <QualityPanel scorecard={scorecard} phase={phase} />
          </div>
        </div>
      </main>

      <OpsLinks />
    </div>
  )
}
