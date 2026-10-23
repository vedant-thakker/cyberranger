export type CategoryType = 'sqli' | 'xss' | 'cmdi' | 'path_traversal'

export type OutcomeType = 'Clean' | 'Blocked' | 'Evaded' | 'Unknown'

export interface RoundEvent {
  experiment_id: string
  round_number: number
  category: CategoryType
  injection_point: string
  strategy: string
  transformations: string[]
  payload: string
  status_code: number
  duration_ms: number
  target_compromised: boolean
  detector_outcome: OutcomeType
  rule_fired: string | null
  ml_confidence: number
  one_line_reason: string
  novelty_reward: number
  fitness_score: number
  evidence_snippet?: string
  detector_version?: string
  archive_occupied?: number
  archive_coverage?: number
  bandit_stats?: Record<string, { pull_count: number; total_reward: number; mean_reward: number; selection_percentage: number }>
  retrain_event?: {
    round: number
    version: string
    training_samples: number
    validation_metrics: { val_accuracy: number; val_precision: number; val_recall: number }
  } | null
}

export interface StatsData {
  current_round: number
  total_rounds: number
  status: string
  detector_version: string
  detection_rate: number
  evasion_rate: number
  total_compromises: number
  total_blocked: number
  total_clean: number
  active_rules_count: number
  archive_occupied: number
  archive_capacity: number
  archive_coverage: number
  bandit_stats: Record<string, { pull_count: number; total_reward: number; mean_reward: number; selection_percentage: number }>
  pending_reviews_count: number
}

export interface TriageItem {
  id: number
  experiment_id: string
  round_number: number
  category: CategoryType
  payload: string
  detector_verdict: string
  target_evidence: string
  human_status: 'Pending' | 'Confirmed' | 'Rejected' | 'Duplicate'
  reviewer_note?: string
  created_at: number
}
