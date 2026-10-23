import React, { useState } from 'react'
import { Terminal, ChevronDown, ChevronRight, Shield, Zap } from 'lucide-react'
import { RoundEvent, OutcomeType } from '../types'

interface EventFeedProps {
  rounds: RoundEvent[]
}

export const EventFeed: React.FC<EventFeedProps> = ({ rounds }) => {
  const [expandedRow, setExpandedRow] = useState<number | null>(null)

  const toggleRow = (roundNum: number) => {
    setExpandedRow(expandedRow === roundNum ? null : roundNum)
  }

  // Display newest events first
  const reversed = [...rounds].reverse()

  const getStatusBadge = (outcome: OutcomeType) => {
    switch (outcome) {
      case 'Blocked':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
            <Shield className="h-3 w-3" />
            BLOCKED
          </span>
        )
      case 'Evaded':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-rose-500/10 text-rose-400 border border-rose-500/30 animate-pulse">
            <Zap className="h-3 w-3" />
            EVADED
          </span>
        )
      case 'Clean':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-800 text-slate-400 border border-slate-700">
            CLEAN
          </span>
        )
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium bg-slate-800 text-slate-500 border border-slate-700">
            UNKNOWN
          </span>
        )
    }
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-100 tracking-tight">Live Engagement Log (SSE Stream)</h3>
        </div>
        <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-cyan-400" /> Blocked = Intercepted
          </span>
          <span className="flex items-center gap-1">
            <span className="h-2 w-2 rounded-full bg-rose-400" /> Evaded = Target Compromised
          </span>
        </div>
      </div>

      <div className="overflow-x-auto max-h-96 overflow-y-auto">
        <table className="w-full text-left font-mono text-xs">
          <thead className="bg-slate-950/80 sticky top-0 border-b border-slate-800 text-slate-400">
            <tr>
              <th className="py-2 px-3">#</th>
              <th className="py-2 px-3">Category</th>
              <th className="py-2 px-3">Strategy</th>
              <th className="py-2 px-3">Verdict</th>
              <th className="py-2 px-3">Detection Summary / Reason</th>
              <th className="py-2 px-3 text-right">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {reversed.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-slate-500">
                  Awaiting experiment initialization...
                </td>
              </tr>
            ) : (
              reversed.map((r) => {
                const isExpanded = expandedRow === r.round_number
                return (
                  <React.Fragment key={r.round_number}>
                    <tr
                      onClick={() => toggleRow(r.round_number)}
                      className={`hover:bg-slate-800/40 cursor-pointer transition-colors ${
                        isExpanded ? 'bg-slate-800/30' : ''
                      }`}
                    >
                      <td className="py-2.5 px-3 font-semibold text-slate-300">
                        <span className="flex items-center gap-1">
                          {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                          {r.round_number}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">
                        <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-bold bg-slate-950 text-slate-300 border border-slate-800">
                          {r.category}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                        {r.strategy.replace('_', ' ')}
                      </td>
                      <td className="py-2.5 px-3">{getStatusBadge(r.detector_outcome)}</td>
                      <td className="py-2.5 px-3 text-slate-300 truncate max-w-xs">{r.one_line_reason}</td>
                      <td className="py-2.5 px-3 text-right text-slate-500">{r.duration_ms}ms</td>
                    </tr>

                    {/* Expanded details */}
                    {isExpanded && (
                      <tr className="bg-slate-950/60 border-b border-slate-800">
                        <td colSpan={6} className="p-3 text-xs">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                            <div>
                              <span className="text-slate-400 block mb-1">Generated Input Payload:</span>
                              <pre className="p-2 rounded bg-slate-950 border border-slate-800 text-cyan-300 text-[11px] overflow-x-auto whitespace-pre-wrap break-all">
                                {r.payload}
                              </pre>
                              <div className="mt-2 text-slate-400">
                                <span>Applied Transforms: </span>
                                <span className="text-slate-200">
                                  {r.transformations.length > 0 ? r.transformations.join(', ') : 'none'}
                                </span>
                              </div>
                            </div>

                            <div>
                              <span className="text-slate-400 block mb-1">Local DVWA Target Outcome:</span>
                              <div className="p-2 rounded bg-slate-950 border border-slate-800 text-slate-200 text-[11px]">
                                <div>
                                  <span className="text-slate-400">Status Code:</span> {r.status_code} |{' '}
                                  <span className="text-slate-400">Compromised:</span>{' '}
                                  {r.target_compromised ? (
                                    <span className="text-rose-400 font-bold">YES</span>
                                  ) : (
                                    <span className="text-slate-400">NO</span>
                                  )}
                                </div>
                                <div className="mt-1 text-slate-300 italic">
                                  Evidence: {r.evidence_snippet || 'None'}
                                </div>
                              </div>

                              <div className="mt-2 flex items-center justify-between text-slate-400">
                                <span>ML Confidence: {(r.ml_confidence * 100).toFixed(1)}%</span>
                                <span>Novelty Reward: {r.novelty_reward.toFixed(2)}</span>
                                <span>Fitness: {r.fitness_score.toFixed(3)}</span>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                )
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
