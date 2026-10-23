import React, { useState, useEffect, useRef } from 'react'
import { StatusBar } from './components/StatusBar'
import { MetricCards } from './components/MetricCards'
import { ArmsRaceChart } from './components/ArmsRaceChart'
import { DetectorImprovementChart } from './components/DetectorImprovementChart'
import { MapElitesMatrix } from './components/MapElitesMatrix'
import { BanditChart } from './components/BanditChart'
import { EventFeed } from './components/EventFeed'
import { ControlsBar } from './components/ControlsBar'
import { TriageModal } from './components/TriageModal'
import { RoundEvent, StatsData, TriageItem } from './types'
import {
  checkHealth,
  startExperiment,
  stepExperiment,
  runAllRounds,
  pauseExperiment,
  resumeExperiment,
  stopExperiment,
  getExperimentStats,
  getPendingTriage,
  exportExperimentData,
} from './services/api'
import { Layers, Shield, Zap } from 'lucide-react'

type ViewMode = 'combined' | 'generator' | 'defender'

export default function App(): React.JSX.Element {
  const [expId, setExpId] = useState<string | null>(null)
  const [stats, setStats] = useState<StatsData | null>(null)
  const [rounds, setRounds] = useState<RoundEvent[]>([])
  const [targetHealthy, setTargetHealthy] = useState<boolean>(true)
  const [viewMode, setViewMode] = useState<ViewMode>('combined')
  const [isTriageOpen, setIsTriageOpen] = useState<boolean>(false)
  const [pendingTriage, setPendingTriage] = useState<TriageItem[]>([])
  const sseRef = useRef<EventSource | null>(null)

  // Initial health check & fetch pending reviews
  useEffect(() => {
    checkHealth()
      .then((res) => setTargetHealthy(res.target_healthy))
      .catch(() => setTargetHealthy(false))

    getPendingTriage()
      .then((items) => setPendingTriage(items))
      .catch(() => {})
  }, [])

  // Setup SSE stream when expId changes
  useEffect(() => {
    if (!expId) return

    // Close existing SSE stream if any
    if (sseRef.current) {
      sseRef.current.close()
    }

    const eventSource = new EventSource(`/api/events/${expId}`)
    sseRef.current = eventSource

    eventSource.addEventListener('round_complete', (event: MessageEvent) => {
      try {
        const roundData: RoundEvent = JSON.parse(event.data)
        setRounds((prev) => {
          // Prevent duplicates
          if (prev.some((r) => r.round_number === roundData.round_number)) return prev
          return [...prev, roundData]
        })
        // Refresh stats & triage count
        getExperimentStats(expId).then(setStats).catch(() => {})
        getPendingTriage(expId).then(setPendingTriage).catch(() => {})
      } catch (err) {
        console.error('Failed to parse SSE round data:', err)
      }
    })

    eventSource.onerror = () => {
      // Automatic browser reconnection handles reconnection
    }

    return () => {
      eventSource.close()
    }
  }, [expId])

  // Periodic poll for stats fallback
  useEffect(() => {
    if (!expId) return
    const interval = setInterval(() => {
      getExperimentStats(expId).then(setStats).catch(() => {})
      getPendingTriage(expId).then(setPendingTriage).catch(() => {})
    }, 3000)
    return () => clearInterval(interval)
  }, [expId])

  const handleStart = async (params: { totalRounds: number; seed: number; enableLLM: boolean }) => {
    try {
      const res = await startExperiment({
        total_rounds: params.totalRounds,
        seed: params.seed,
        enable_llm: params.enableLLM,
      })
      setExpId(res.experiment_id)
      setRounds([])
      const initialStats = await getExperimentStats(res.experiment_id)
      setStats(initialStats)
    } catch (err) {
      console.error('Failed to start experiment:', err)
    }
  }

  const handleStep = async () => {
    if (!expId) {
      // Auto-start if not started
      const res = await startExperiment({ total_rounds: 20, seed: 42 })
      setExpId(res.experiment_id)
      const r = await stepExperiment(res.experiment_id)
      setRounds([r])
      const s = await getExperimentStats(res.experiment_id)
      setStats(s)
      return
    }
    try {
      const r = await stepExperiment(expId)
      setRounds((prev) => {
        if (prev.some((item) => item.round_number === r.round_number)) return prev
        return [...prev, r]
      })
      const s = await getExperimentStats(expId)
      setStats(s)
    } catch (err) {
      console.error('Failed to step round:', err)
    }
  }

  const handleRunAll = async () => {
    if (!expId) {
      const res = await startExperiment({ total_rounds: 20, seed: 42 })
      setExpId(res.experiment_id)
      await runAllRounds(res.experiment_id)
      return
    }
    await runAllRounds(expId)
  }

  const handlePause = async () => {
    if (!expId) return
    await pauseExperiment(expId)
    const s = await getExperimentStats(expId)
    setStats(s)
  }

  const handleResume = async () => {
    if (!expId) return
    await resumeExperiment(expId)
    const s = await getExperimentStats(expId)
    setStats(s)
  }

  const handleStop = async () => {
    if (!expId) return
    await stopExperiment(expId)
    const s = await getExperimentStats(expId)
    setStats(s)
  }

  const handleExport = async () => {
    if (!expId) return
    const data = await exportExperimentData(expId)
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cyberranger_experiment_${expId}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* Top Header Status Bar */}
      <StatusBar
        stats={stats}
        expId={expId}
        targetHealthy={targetHealthy}
        onOpenTriage={() => setIsTriageOpen(true)}
      />

      {/* Main Command Center Body */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 space-y-6">
        {/* Controls Bar */}
        <ControlsBar
          isRunning={stats?.status === 'running'}
          isPaused={false}
          onStart={handleStart}
          onStep={handleStep}
          onRunAll={handleRunAll}
          onPause={handlePause}
          onResume={handleResume}
          onStop={handleStop}
          onExport={handleExport}
        />

        {/* View Mode Toggle Pill Bar */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center gap-1.5 p-1 rounded-lg bg-slate-900 border border-slate-800 font-mono text-xs">
            <button
              onClick={() => setViewMode('combined')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                viewMode === 'combined'
                  ? 'bg-cyan-500/20 text-cyan-300 font-bold border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="h-3.5 w-3.5" /> Combined Overview
            </button>
            <button
              onClick={() => setViewMode('generator')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                viewMode === 'generator'
                  ? 'bg-violet-500/20 text-violet-300 font-bold border border-violet-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Zap className="h-3.5 w-3.5" /> Generator Side (Red)
            </button>
            <button
              onClick={() => setViewMode('defender')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md transition-all cursor-pointer ${
                viewMode === 'defender'
                  ? 'bg-emerald-500/20 text-emerald-300 font-bold border border-emerald-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Shield className="h-3.5 w-3.5" /> Detector Side (Blue)
            </button>
          </div>

          <div className="text-xs font-mono text-slate-500 hidden sm:block">
            {expId ? `Session ID: ${expId}` : 'No active session'}
          </div>
        </div>

        {/* 4 Primary Metric Cards */}
        <MetricCards stats={stats} />

        {/* Conditional View Renders */}
        {viewMode === 'combined' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <ArmsRaceChart rounds={rounds} />
              <DetectorImprovementChart rounds={rounds} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <MapElitesMatrix
                rounds={rounds}
                occupiedCount={stats?.archive_occupied || 0}
                coverageRatio={stats?.archive_coverage || 0}
              />
              <BanditChart banditStats={stats?.bandit_stats} />
            </div>

            <EventFeed rounds={rounds} />
          </div>
        )}

        {viewMode === 'generator' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <MapElitesMatrix
                rounds={rounds}
                occupiedCount={stats?.archive_occupied || 0}
                coverageRatio={stats?.archive_coverage || 0}
              />
              <BanditChart banditStats={stats?.bandit_stats} />
            </div>
            <ArmsRaceChart rounds={rounds} />
            <EventFeed rounds={rounds} />
          </div>
        )}

        {viewMode === 'defender' && (
          <div className="space-y-6">
            <DetectorImprovementChart rounds={rounds} />
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 font-mono text-xs">
              <h3 className="text-sm font-semibold text-slate-100 mb-2 font-sans">
                Active Detection Engine Configuration
              </h3>
              <p className="text-slate-400 mb-4">
                Version: <span className="text-cyan-400 font-bold">{stats?.detector_version || 'rules-v1.4'}</span> | Active Heuristic Rules:{' '}
                <span className="text-emerald-400 font-bold">{stats?.active_rules_count || 12}</span>
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-slate-300">
                <div className="p-3 rounded bg-slate-950 border border-slate-800">
                  <span className="font-bold text-slate-200 block mb-1">Random Forest Architecture</span>
                  <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px]">
                    <li>Trees: 50 estimators, max depth: 6</li>
                    <li>Feature dimensions: 14 statistical & lexical indicators</li>
                    <li>Retraining policy: Fixed 5-round cadence strictly from human-confirmed findings</li>
                  </ul>
                </div>
                <div className="p-3 rounded bg-slate-950 border border-slate-800">
                  <span className="font-bold text-slate-200 block mb-1">Containment & Safety Guard</span>
                  <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px]">
                    <li>Strict loopback destination pinning (127.0.0.1:8080 only)</li>
                    <li>Redirect interception & DNS rebinding guard active</li>
                    <li>Emergency kill-switch enabled</li>
                  </ul>
                </div>
              </div>
            </div>
            <EventFeed rounds={rounds} />
          </div>
        )}
      </main>

      {/* Human Review Triage Modal */}
      <TriageModal
        isOpen={isTriageOpen}
        onClose={() => setIsTriageOpen(false)}
        items={pendingTriage}
        onReviewCompleted={() => {
          if (expId) {
            getExperimentStats(expId).then(setStats)
            getPendingTriage(expId).then(setPendingTriage)
          }
        }}
      />
    </div>
  )
}
