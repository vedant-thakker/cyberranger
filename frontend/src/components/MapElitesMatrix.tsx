import React from 'react'
import { Grid, Sparkles } from 'lucide-react'
import { RoundEvent } from '../types'

interface MapElitesMatrixProps {
  rounds: RoundEvent[]
  occupiedCount: number
  coverageRatio: number
}

const CATEGORIES = ['sqli', 'xss', 'cmdi', 'path_traversal']
const TECHNIQUES = ['none', 'case_variation', 'whitespace_sub', 'url_encode', 'hex_encode', 'comment_placement']

export const MapElitesMatrix: React.FC<MapElitesMatrixProps> = ({ rounds, occupiedCount, coverageRatio }) => {
  // Build lookup of occupied cells from rounds
  const occupiedSet = new Set<string>()
  const cellPayloads: Record<string, string> = {}

  rounds.forEach((r) => {
    const primaryTransform = r.transformations[0] || 'none'
    const key = `${r.category}:${primaryTransform}`
    occupiedSet.add(key)
    cellPayloads[key] = r.payload
  })

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 backdrop-blur-sm">
      <div className="flex items-center justify-between mb-3">
        <div>
          <div className="flex items-center gap-2">
            <Grid className="h-4 w-4 text-cyan-400" />
            <h3 className="text-sm font-semibold text-slate-100 tracking-tight">MAP-Elites Novelty Matrix</h3>
          </div>
          <p className="text-xs text-slate-400 font-mono">Structural behavioral niches (Category x Evasion Transform)</p>
        </div>
        <div className="text-right">
          <span className="text-xs font-mono text-cyan-400 font-semibold">{occupiedCount} cells discovered</span>
          <p className="text-[10px] text-slate-500 font-mono">Capacity: 128 cells</p>
        </div>
      </div>

      {/* Grid Display */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs font-mono">
          <thead>
            <tr>
              <th className="p-1.5 text-left text-slate-500 font-normal">Category</th>
              {TECHNIQUES.map((tech) => (
                <th key={tech} className="p-1.5 text-center text-slate-400 font-normal truncate max-w-[70px]">
                  {tech.replace('_', ' ')}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {CATEGORIES.map((cat) => (
              <tr key={cat} className="border-t border-slate-800/60">
                <td className="p-1.5 font-medium text-slate-300 uppercase">{cat}</td>
                {TECHNIQUES.map((tech) => {
                  const key = `${cat}:${tech}`
                  const isOccupied = occupiedSet.has(key)
                  return (
                    <td key={tech} className="p-1.5 text-center">
                      <div
                        title={isOccupied ? `Occupied: ${cellPayloads[key]}` : 'Empty niche'}
                        className={`h-6 w-full rounded flex items-center justify-center transition-all ${
                          isOccupied
                            ? 'bg-cyan-500/20 border border-cyan-500/40 text-cyan-300 shadow-[0_0_8px_rgba(6,182,212,0.2)]'
                            : 'bg-slate-950 border border-slate-800/80 text-slate-700'
                        }`}
                      >
                        {isOccupied ? <Sparkles className="h-3 w-3" /> : '·'}
                      </div>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/60">
        <span>Coverage Progress:</span>
        <div className="w-1/2 bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
          <div
            className="bg-cyan-500 h-full rounded-full transition-all duration-500"
            style={{ width: `${Math.min(100, Math.max(5, coverageRatio))}%` }}
          />
        </div>
        <span className="text-cyan-400 font-medium">{coverageRatio}%</span>
      </div>
    </div>
  )
}
