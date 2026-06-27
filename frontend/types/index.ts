// Result Card Types for Zero-Shot Classification with FastAPI Backend

export interface Candidate {
  label: string
  score: number
}

export interface DetectedObject {
  name: string
  score: number
}

export interface TopMatch {
  label: string
  score: number
}

export interface DomainScores {
  [key: string]: number
}

export interface ClassificationMetadata {
  domain_confidence: number
  raw_prediction_score: number
  total_labels_evaluated: number
  confidence_explanation: string
}

export interface Narrative {
  short: string
  detailed: string
  confidence: 'High' | 'Medium' | 'Low'
}

export interface ClassificationResult {
  predictions?: Record<string, number>
  top_prediction?: Record<string, number> | { label: string; score: number }
  narrative?: Narrative | string  // Supports both new Narrative object and legacy string
  explanation?: string
  reasoning?: {
    summary: string
    attributes: string[]
    detailed_reasoning: string
  }
  reasoning_chain?: {
    num_prompts?: number
    top_prompts?: string[]
    similarity_score?: number
  }
  visual_features?: string[]
  domain_info?: {
    domain: string
    confidence: number
    characteristics?: string[]
    embedding_stats: {
      mean: number
      std: number
      range?: number
    }
  }
  // Additional fields from hybrid classification endpoint
  domain?: string
  model_used?: string
  prediction?: string
  confidence_score?: number
  caption?: string
  risk_notes?: string
  objects?: Array<{ name: string; score: number }>
  top_predictions?: Array<{ label: string; score: number }>
  top_matches?: Array<{ label: string; score: number }>
  domain_scores?: Record<string, number>
  inference_time_seconds?: number
  metadata?: ClassificationMetadata
  // Legacy fields
  confidence?: number
  label?: string
  candidates?: Candidate[]
  validation?: {
    domain_similarity: number
    caption_similarity: number
  }
  llm_reranking_used?: boolean
  temperature?: number
}

export interface AddClassRequest {
  label: string
  domain?: string
  images?: File[]
}

export interface AddClassResponse {
  status: string
  label: string
  domain: string
  num_images_used: number
  embedding_norm: number
  message: string
}

// Legacy types (keep for backward compatibility)
export interface TopPrediction {
  label: string
  refined_label: string
  confidence: number
  band: 'High' | 'Medium' | 'Low'
  source_candidates: string[]
}

export interface LabelRefinement {
  candidate: string
  refined: string
  reason: string
}

export interface Narrative {
  short: string
  detailed: string
  confidence: 'High' | 'Medium' | 'Low'
}

export interface DomainAdaptation {
  style: string
  style_confidence: number
  auto_tuning_actions: string[]
  effect_summary: string
}

export interface Anomaly {
  issue: string
  suggested_fix: string
  confidence: number
}

export interface TextPrompt {
  prompt: string
  score: number
}

export interface TransparencyTrace {
  final_prompt: string
  top_text_prompts: TextPrompt[]
  tuning_steps: string[]
}

export interface ResultCardData {
  image_id: string
  top_predictions: TopPrediction[]
  label_refinement: LabelRefinement[]
  narrative: Narrative
  explanation?: string
  domain_adaptation: DomainAdaptation
  anomalies: Anomaly[]
  transparency_trace: TransparencyTrace
  ui_actions: string[]
}

// Evaluation types
export interface PerClassMetrics {
  precision: number
  recall: number
  f1: number
  samples: number
}

export interface DomainPerformance {
  accuracy: number
  samples: number
}

export interface EvaluationMetrics {
  top1_accuracy: number
  top5_accuracy: number
  precision_weighted: number
  recall_weighted: number
  f1_weighted: number
  precision_macro: number
  recall_macro: number
  f1_macro: number
  map: number
  cross_domain_drop: number
  ece: number
  num_samples: number
  num_classes: number
  per_class_metrics?: Record<string, PerClassMetrics>
  domain_performance?: Record<string, DomainPerformance>
}

export interface EvaluationResult {
  status: string
  metrics: EvaluationMetrics
}

export interface EvaluationExport {
  timestamp: string
  num_samples: number
  metrics: EvaluationMetrics
  files: Array<{
    filename: string
    label: string
  }>
}
