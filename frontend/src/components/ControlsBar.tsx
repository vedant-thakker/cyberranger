import React, { useState } from 'react'
import {
  Play,
  Pause,
  Square,
  StepForward,
  Download,
  Sliders,
} from 'lucide-react'

interface ControlsBarProps {
  isRunning: boolean
  isPaused: boolean
  onStart: (params: { totalRounds: number; seed: number; enableLLM: boolean }) => void
  onStep: () => void
  onRunAll: () => void
  onPause: () => void
  onResume: () => void
  onStop: () => void
  onExport: () => void
}

export const ControlsBar: React.FC<ControlsBarProps> = ({
  isRunning,
  isPaused,
  onStart,
  onStep,
  onRunAll,
  onPause,
  onResume,
  onStop,
  onExport,
}) => {
  const [roundsInput, setRoundsInput] = useState<number>(20)
  const [seedInput, setSeedInput] = useState<number>(42)
  const [enableLLM, setEnableLLM] = useState<boolean>(false)
  const [showConfig, setShowConfig] = useState<boolean>(false)

  const handleStartClick = () => {
    onStart({
      totalRounds: roundsInput,
      seed: seedInput,
      enableLLM: enableLLM,
    })
  }

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/80 p-3 backdrop-blur-sm flex flex-wrap items-center justify-between gap-3 font-mono text-xs">
      {/* Primary Action Buttons */}
      <div className="flex flex-wrap items-center gap-2">
        {!isRunning ? (
          <button
            onClick={handleStartClick}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-black font-bold transition-all shadow-[0_0_12px_rgba(6,182,212,0.2)] cursor-pointer"
          >
            <Play className="h-3.5 w-3.5 fill-current" /> Initialize Experiment
          </button>
        ) : isPaused ? (
          <button
            onClick={onResume}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold transition-all cursor-pointer"
          >
            <Play className="h-3.5 w-3.5 fill-current" /> Resume Execution
          </button>
        ) : (
          <button
            onClick={onPause}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-amber-600/20 border border-amber-500/40 text-amber-300 hover:bg-amber-600/30 font-medium transition-all cursor-pointer"
          >
            <Pause className="h-3.5 w-3.5" /> Pause
          </button>
        )}

        <button
          onClick={onStep}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-medium transition-all cursor-pointer"
        >
          <StepForward className="h-3.5 w-3.5" /> Step 1 Round
        </button>

        <button
          onClick={onRunAll}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 font-medium transition-all cursor-pointer"
        >
          <Play className="h-3.5 w-3.5" /> Run Autonomous Session
        </button>

        {isRunning && (
          <button
            onClick={onStop}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-rose-600/20 border border-rose-500/40 text-rose-300 hover:bg-rose-600/30 font-medium transition-all cursor-pointer"
          >
            <Square className="h-3.5 w-3.5 fill-current" /> Emergency Stop
          </button>
        )}
      </div>

      {/* Settings & Export Controls */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setShowConfig(!showConfig)}
          className={`flex items-center gap-1.5 px-3 py-2 rounded-lg border transition-all cursor-pointer ${
            showConfig
              ? 'bg-cyan-500/10 border-cyan-500/40 text-cyan-300'
              : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sliders className="h-3.5 w-3.5" /> Config Parameters
        </button>

        <button
          onClick={onExport}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-300 hover:border-slate-700 transition-all cursor-pointer"
        >
          <Download className="h-3.5 w-3.5" /> Export Run JSON
        </button>
      </div>

      {/* Expandable Configuration Drawer */}
      {showConfig && (
        <div className="w-full mt-2 pt-3 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-4 bg-slate-950/40 p-3 rounded-lg">
          <div>
            <label className="block text-slate-400 text-[10px] uppercase mb-1">Rounds Limit (2-100):</label>
            <input
              type="number"
              min={2}
              max={100}
              value={roundsInput}
              onChange={(e) => setRoundsInput(Number(e.target.value))}
              className="w-full rounded bg-slate-900 border border-slate-700 px-2.5 py-1 text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-slate-400 text-[10px] uppercase mb-1">RNG Random Seed:</label>
            <input
              type="number"
              value={seedInput}
              onChange={(e) => setSeedInput(Number(e.target.value))}
              className="w-full rounded bg-slate-900 border border-slate-700 px-2.5 py-1 text-slate-100 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="flex items-center justify-between sm:justify-start sm:gap-3 mt-4">
            <span className="text-slate-400 text-[10px] uppercase">LLM Proposer Flag:</span>
            <button
              onClick={() => setEnableLLM(!enableLLM)}
              className={`px-3 py-1 rounded text-[11px] font-bold border transition-colors cursor-pointer ${
                enableLLM
                  ? 'bg-cyan-500/20 border-cyan-500/50 text-cyan-300'
                  : 'bg-slate-900 border-slate-800 text-slate-500'
              }`}
            >
              {enableLLM ? 'ENABLED (STRUCTURAL ONLY)' : 'DISABLED (OFF)'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
