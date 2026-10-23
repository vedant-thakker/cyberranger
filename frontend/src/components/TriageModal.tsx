import React, { useState } from 'react'
import { X, CheckCircle, XCircle, Copy, AlertTriangle } from 'lucide-react'
import { TriageItem } from '../types'
import { submitTriageReview } from '../services/api'

interface TriageModalProps {
  isOpen: boolean
  onClose: () => void
  items: TriageItem[]
  onReviewCompleted: () => void
}

export const TriageModal: React.FC<TriageModalProps> = ({
  isOpen,
  onClose,
  items,
  onReviewCompleted,
}) => {
  const [selectedItem, setSelectedItem] = useState<TriageItem | null>(null)
  const [note, setNote] = useState<string>('')
  const [submitting, setSubmitting] = useState<boolean>(false)

  if (!isOpen) return null

  const handleDecision = async (decision: 'Confirmed' | 'Rejected' | 'Duplicate') => {
    if (!selectedItem) return
    setSubmitting(true)
    try {
      await submitTriageReview(selectedItem.id, decision, note)
      setNote('')
      setSelectedItem(null)
      onReviewCompleted()
    } catch (err) {
      console.error(err)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-3xl rounded-xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden flex flex-col max-h-[85vh]">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-slate-800 px-6 py-4 bg-slate-950/60">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-amber-400" />
            <h2 className="text-base font-bold text-slate-100 font-mono tracking-tight">
              Human-in-the-Loop Triage Verification Queue
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="flex-1 overflow-y-auto p-6 font-mono text-xs space-y-4">
          <div className="p-3 rounded-lg bg-amber-500/10 border border-amber-500/30 text-amber-300">
            <strong>Mentor Constraint:</strong> The system never self-certifies findings. Only findings explicitly marked{' '}
            <span className="underline font-bold">Confirmed</span> by a human reviewer will enter the blue model retraining dataset.
          </div>

          {items.length === 0 ? (
            <div className="py-12 text-center text-slate-500">
              No pending findings in the triage queue. All discovered candidates reviewed.
            </div>
          ) : (
            <div className="space-y-3">
              {items.map((item) => (
                <div
                  key={item.id}
                  className={`rounded-lg border p-4 transition-all ${
                    selectedItem?.id === item.id
                      ? 'border-cyan-500 bg-slate-800/80 shadow-[0_0_15px_rgba(6,182,212,0.1)]'
                      : 'border-slate-800 bg-slate-950/60 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-cyan-300 font-bold uppercase">
                        {item.category}
                      </span>
                      <span className="text-slate-400">Round {item.round_number}</span>
                    </div>
                    <span className="text-slate-500 text-[10px]">ID: #{item.id}</span>
                  </div>

                  <div className="mb-2">
                    <span className="text-slate-500 block text-[10px] uppercase mb-0.5">Payload</span>
                    <pre className="p-2 rounded bg-slate-900 border border-slate-800 text-cyan-400 whitespace-pre-wrap break-all text-[11px]">
                      {item.payload}
                    </pre>
                  </div>

                  <div className="mb-3 text-slate-300">
                    <span className="text-slate-500 text-[10px] uppercase">DVWA Response Evidence: </span>
                    <span className="italic">{item.target_evidence}</span>
                  </div>

                  {selectedItem?.id === item.id ? (
                    <div className="space-y-3 pt-3 border-t border-slate-800">
                      <div>
                        <label className="block text-slate-400 text-[10px] uppercase mb-1">
                          Reviewer Assessment Note (Optional):
                        </label>
                        <input
                          type="text"
                          value={note}
                          onChange={(e) => setNote(e.target.value)}
                          placeholder="e.g. Valid syntax error disclosure, confirmed payload structure"
                          className="w-full rounded bg-slate-900 border border-slate-700 px-3 py-1.5 text-slate-100 focus:outline-none focus:border-cyan-500"
                        />
                      </div>

                      <div className="flex items-center justify-end gap-2">
                        <button
                          disabled={submitting}
                          onClick={() => handleDecision('Confirmed')}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-bold cursor-pointer transition-colors"
                        >
                          <CheckCircle className="h-3.5 w-3.5" /> Confirm Finding
                        </button>
                        <button
                          disabled={submitting}
                          onClick={() => handleDecision('Duplicate')}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 cursor-pointer transition-colors"
                        >
                          <Copy className="h-3.5 w-3.5" /> Duplicate
                        </button>
                        <button
                          disabled={submitting}
                          onClick={() => handleDecision('Rejected')}
                          className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-rose-600 hover:bg-rose-500 text-white font-bold cursor-pointer transition-colors"
                        >
                          <XCircle className="h-3.5 w-3.5" /> Reject Finding
                        </button>
                      </div>
                    </div>
                  ) : (
                    <button
                      onClick={() => setSelectedItem(item)}
                      className="mt-1 px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 text-[11px] font-medium cursor-pointer transition-colors"
                    >
                      Review This Candidate →
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="border-t border-slate-800 px-6 py-3 bg-slate-950/60 flex items-center justify-between font-mono text-xs text-slate-400">
          <span>Pending: {items.length} candidates</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors cursor-pointer"
          >
            Close Window
          </button>
        </div>
      </div>
    </div>
  )
}
