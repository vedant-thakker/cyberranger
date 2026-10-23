import React from 'react'
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine,
} from 'recharts'
import { RoundEvent } from '../types'

interface DetectorImprovementChartProps {
  rounds: RoundEvent[]
}

export const DetectorImprovementChart: React.FC<DetectorImprovementChartProps> = ({ rounds }) => {
  let blockedCount = 0
  const retrainRounds: { round: number; version: string }[] = []

  const data = rounds.map((r, idx) => {
    if (r.detector_outcome === 'Blocked') blockedCount += 1
    const detectionRate = Math.round((blockedCount / (idx + 1)) * 100)

    if (r.retrain_event) {
      retrainRounds.push({
        round: r.round_number,
        version: r.retrain_event.version,
      })
    }

    return {
      round: `R${r.round_number}`,
      roundNum: r.round_number,
      rate: detectionRate,
      version: r.detector_version,
      retrained: Boolean(r.retrain_event),
    }
  })

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-100 tracking-tight">Detector Learning Curve</h3>
          <p className="text-xs text-slate-400 font-mono">Detection Rate with Model Retraining Cadence Markers</p>
        </div>
      </div>

      <div className="h-64 w-full">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center font-mono text-xs text-slate-500">
            No rounds recorded yet.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 15, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="round" stroke="#64748b" tick={{ fontSize: 11 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 11 }} domain={[0, 100]} unit="%" />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0b0f19',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  fontSize: '12px',
                  fontFamily: 'JetBrains Mono',
                }}
              />
              {/* Vertical Markers for Retrain Events */}
              {retrainRounds.map((ret) => (
                <ReferenceLine
                  key={ret.round}
                  x={`R${ret.round}`}
                  stroke="#10b981"
                  strokeDasharray="4 4"
                  label={{
                    value: `Retrain: ${ret.version}`,
                    fill: '#10b981',
                    fontSize: 10,
                    position: 'top',
                    fontFamily: 'JetBrains Mono',
                  }}
                />
              ))}
              <Line
                type="monotone"
                dataKey="rate"
                name="Detection Rate"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ r: 3, fill: '#10b981' }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
