import React from 'react'
import { ShieldCheck, ShieldAlert, Zap, FileCode2 } from 'lucide-react'
import { StatsData } from '../types'

interface MetricCardsProps {
  stats: StatsData | null
}

export const MetricCards: React.FC<MetricCardsProps> = ({ stats }) => {
  const hasData = stats && stats.current_round > 0

  const detectionRateDisplay = hasData ? `${stats.detection_rate}%` : 'N/A'
  const evasionRateDisplay = hasData ? `${stats.evasion_rate}%` : 'N/A'
  const totalSuccesses = hasData ? stats.total_compromises : '0'
  const activeRules = stats ? stats.active_rules_count : 12

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* 1. Detection Rate */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 relative overflow-hidden backdrop-blur-sm">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-mono tracking-wider uppercase">Detection Rate</span>
          <ShieldCheck className="h-4 w-4 text-cyan-400" />
        </div>
        <div className="text-2xl font-bold font-mono tracking-tight text-cyan-400">
          {detectionRateDisplay}
        </div>
        <p className="text-xs text-slate-500 font-mono mt-1">
          {hasData ? `${stats.total_blocked} threats intercepted` : 'Awaiting round execution'}
        </p>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-cyan-500 to-transparent" />
      </div>

      {/* 2. Evasion Rate */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 relative overflow-hidden backdrop-blur-sm">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-mono tracking-wider uppercase">Evasion Rate</span>
          <ShieldAlert className="h-4 w-4 text-amber-400" />
        </div>
        <div className="text-2xl font-bold font-mono tracking-tight text-amber-400">
          {evasionRateDisplay}
        </div>
        <p className="text-xs text-slate-500 font-mono mt-1">
          {hasData ? `${Math.round((stats.evasion_rate / 100) * stats.current_round)} undetected compromises` : 'Generator probe bypasses'}
        </p>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-amber-500 to-transparent" />
      </div>

      {/* 3. Total Test Compromises */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 relative overflow-hidden backdrop-blur-sm">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-mono tracking-wider uppercase">Target Compromises</span>
          <Zap className="h-4 w-4 text-violet-400" />
        </div>
        <div className="text-2xl font-bold font-mono tracking-tight text-violet-400">
          {totalSuccesses}
        </div>
        <p className="text-xs text-slate-500 font-mono mt-1">
          Verified DVWA vulnerable responses
        </p>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-violet-500 to-transparent" />
      </div>

      {/* 4. Active Rules & ML Version */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 relative overflow-hidden backdrop-blur-sm">
        <div className="flex items-center justify-between text-slate-400 mb-2">
          <span className="text-xs font-mono tracking-wider uppercase">Active Rules</span>
          <FileCode2 className="h-4 w-4 text-emerald-400" />
        </div>
        <div className="text-2xl font-bold font-mono tracking-tight text-emerald-400">
          {activeRules}
        </div>
        <p className="text-xs text-slate-500 font-mono mt-1">
          Across 4 educational categories
        </p>
        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500 to-transparent" />
      </div>
    </div>
  )
}
