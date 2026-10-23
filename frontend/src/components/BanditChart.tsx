import React from 'react'
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts'
import { Cpu } from 'lucide-react'

interface BanditChartProps {
  banditStats?: Record<string, { pull_count: number; total_reward: number; mean_reward: number; selection_percentage: number }>
}

export const BanditChart: React.FC<BanditChartProps> = ({ banditStats }) => {
  const data = Object.entries(banditStats || {}).map(([key, val]) => ({
    strategy: key.replace('_', ' '),
    pulls: val.pull_count,
    mean_reward: val.mean_reward,
    percentage: val.selection_percentage,
  }))

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-violet-400" />
            <h3 className="text-sm font-semibold text-slate-100 tracking-tight">UCB1 Operator Bandit</h3>
          </div>
          <p className="text-xs text-slate-400 font-mono">Strategy exploration vs exploitation pulls</p>
        </div>
      </div>

      <div className="h-48 w-full">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center font-mono text-xs text-slate-500">
            Awaiting strategy selections...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="strategy" stroke="#64748b" tick={{ fontSize: 10 }} />
              <YAxis stroke="#64748b" tick={{ fontSize: 10 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0b0f19',
                  borderColor: '#334155',
                  borderRadius: '8px',
                  fontSize: '11px',
                  fontFamily: 'JetBrains Mono',
                }}
              />
              <Bar dataKey="pulls" name="Selections" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}
