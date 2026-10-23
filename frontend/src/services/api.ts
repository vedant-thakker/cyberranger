import { RoundEvent, StatsData, TriageItem } from '../types'

const BASE_URL = '/api'

export async function checkHealth(): Promise<{ status: string; target_healthy: boolean; guard_active: boolean }> {
  const res = await fetch(`${BASE_URL}/health`)
  return res.json()
}

export async function startExperiment(params: {
  name?: string
  total_rounds?: number
  seed?: number
  cadence_rounds?: number
  enable_llm?: boolean
}): Promise<{ experiment_id: string; total_rounds: number; seed: number }> {
  const res = await fetch(`${BASE_URL}/experiments/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: params.name || 'CyberRanger Autonomous Session',
      total_rounds: params.total_rounds || 20,
      seed: params.seed ?? 42,
      cadence_rounds: params.cadence_rounds || 5,
      enable_llm: params.enable_llm || false,
    }),
  })
  return res.json()
}

export async function stepExperiment(expId: string): Promise<RoundEvent> {
  const res = await fetch(`${BASE_URL}/experiments/${expId}/step`, { method: 'POST' })
  if (!res.ok) throw new Error('Step failed')
  return res.json()
}

export async function runAllRounds(expId: string): Promise<void> {
  await fetch(`${BASE_URL}/experiments/${expId}/run`, { method: 'POST' })
}

export async function pauseExperiment(expId: string): Promise<void> {
  await fetch(`${BASE_URL}/experiments/${expId}/pause`, { method: 'POST' })
}

export async function resumeExperiment(expId: string): Promise<void> {
  await fetch(`${BASE_URL}/experiments/${expId}/resume`, { method: 'POST' })
}

export async function stopExperiment(expId: string): Promise<void> {
  await fetch(`${BASE_URL}/experiments/${expId}/stop`, { method: 'POST' })
}

export async function getExperimentStats(expId: string): Promise<StatsData> {
  const res = await fetch(`${BASE_URL}/experiments/${expId}/stats`)
  return res.json()
}

export async function getExperimentRounds(expId: string): Promise<RoundEvent[]> {
  const res = await fetch(`${BASE_URL}/experiments/${expId}/rounds`)
  return res.json()
}

export async function getPendingTriage(expId?: string): Promise<TriageItem[]> {
  const url = expId ? `${BASE_URL}/triage/pending?exp_id=${expId}` : `${BASE_URL}/triage/pending`
  const res = await fetch(url)
  return res.json()
}

export async function submitTriageReview(
  reviewId: number,
  decision: 'Confirmed' | 'Rejected' | 'Duplicate',
  note: string = '',
): Promise<void> {
  await fetch(`${BASE_URL}/triage/${reviewId}/review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ decision, note }),
  })
}

export async function exportExperimentData(expId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/experiments/${expId}/export`)
  return res.json()
}
