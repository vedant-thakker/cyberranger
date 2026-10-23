import React from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts'
import { RoundEvent } from '../types'

interface ArmsRaceChartProps {
  rounds: RoundEvent[]
}

export const ArmsRaceChart: React.FC<ArmsRaceChartProps> = ({ rounds }) => {
  // Compute cumulative values for the arms race
  let cumulativeCompromises = 0
  let cumulativeBlocked = 0

  const data = rounds.map((r) => {
    if (r.target_compromised) cumulativeCompromises += 1
    if (r.detector_outcome === 'Blocked') cumulativeBlocked += 1

    return {
      round: `R${r.round_number}`,
      round_num: r.round_number,
      compromises: cumulativeCompromises,
      blocked: cumulativeBlocked,
      category: r.category,
      outcome: r.detector_outcome,
    }
  })

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 tracking-tight">Co-Evolutionary Arms Race</h3>
          <p className="text-xs text-slate-400 font-mono">Target Compromises vs Intercepted Threats</p>
        </div>
      </div>

      <div className="h-64 w-full">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center font-mono text-xs text-slate-500">
            No rounds recorded yet. Start experiment to plot data.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="round" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0b0f19',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontFamily: 'JetBrains Mono',
                }}
              />
              <Legend
                wrapperStyle={{ fontSize: '11px', fontFamily: 'JetBrains Mono', paddingTop: '10px' }}
              />
              <Line
                type="monotone"
                dataKey="compromises"
                name="Generator Compromises"
                stroke="#ec4899"
                strokeWidth={2}
                dot={{ r: 3, fill: '#ec4899' }}
              />
              <Line
                type="monotone"
                dataKey="blocked"
                name="Detector Interceptions"
                stroke="#06b6d4"
                strokeWidth={2}
                dot={{ r: 3, fill: '#06b6d4' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
