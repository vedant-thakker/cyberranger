import React from 'react'
import { Shield, Target, Activity, AlertCircle, RefreshCw } from 'lucide-react'
import { StatsData } from '../types'

interface StatusBarProps {
  stats: StatsData | null
  expId: string | null
  targetHealthy: boolean
  onOpenTriage: () => void
}

export const StatusBar: React.FC<StatusBarProps> = ({ stats, expId, targetHealthy, onOpenTriage }) => {
  const isRunning = stats?.status === 'running'
  const isCompleted = stats && stats.current_round >= stats.total_rounds && stats.total_rounds > 0

  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur-md px-6 py-3.5 sticky top-0 z-30 flex flex-wrap items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
          <Shield className="h-5 w-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-lg tracking-tight text-slate-100">CYBERRANGER</span>
            <span className="text-xs px-2 py-0.5 rounded font-mono font-medium bg-slate-800 text-cyan-400 border border-slate-700">
              LAB-CORE
            </span>
          </div>
          <p className="text-xs text-slate-400 font-mono">Autonomous Co-Evolution Security Platform</p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3 font-mono text-xs">
        {/* Target DVWA Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300">
          <Target className="h-3.5 w-3.5 text-slate-400" />
          <span>TARGET:</span>
          {targetHealthy ? (
            <span className="flex items-center gap-1.5 text-emerald-400">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
              DVWA (127.0.0.1:8080)
            </span>
          ) : (
            <span className="text-rose-400">OFFLINE</span>
          )}
        </div>

        {/* Session ID */}
        <div className="px-3 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300 hidden lg:block">
          <span className="text-slate-400">SESSION:</span>{' '}
          <span className="text-cyan-400 font-semibold">{expId ? `#${expId}` : 'NONE'}</span>
        </div>

        {/* Experiment State */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300">
          <Activity className="h-3.5 w-3.5 text-cyan-400" />
          <span>STATE:</span>
          {isRunning ? (
            <span className="text-cyan-400 font-semibold flex items-center gap-1.5">
              <RefreshCw className="h-3 w-3 animate-spin" />
              RUNNING
            </span>
          ) : isCompleted ? (
            <span className="text-emerald-400 font-semibold">FINISHED</span>
          ) : (
            <span className="text-slate-400">IDLE</span>
          )}
        </div>

        {/* Round Progress */}
        <div className="px-3 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300">
          <span className="text-slate-400">ROUND:</span>{' '}
          <span className="text-slate-100 font-semibold">
            {stats ? `${stats.current_round} / ${stats.total_rounds}` : '0 / 20'}
          </span>
        </div>

        {/* Detector Version */}
        <div className="px-3 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-300 hidden md:block">
          <span className="text-slate-400">BLUE AGENT:</span>{' '}
          <span className="text-cyan-300">{stats?.detector_version || 'rules-v1.4+rf-untrained'}</span>
        </div>

        {/* Triage Button / Badge */}
        <button
          onClick={onOpenTriage}
          className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-300 hover:bg-amber-500/20 transition-colors cursor-pointer"
        >
          <AlertCircle className="h-3.5 w-3.5" />
          <span>HUMAN REVIEW:</span>
          <span className="px-1.5 py-0.2 rounded bg-amber-500/30 font-bold">
            {stats?.pending_reviews_count || 0}
          </span>
        </button>
      </div>
    </header>
  )
}
