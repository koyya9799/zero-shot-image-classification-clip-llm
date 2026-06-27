'use client'

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { 
  AlertTriangle, 
  CheckCircle, 
  Info, 
  ChevronDown,
  ChevronUp,
  Download,
  RefreshCw,
  Plus,
  X,
  Brain
} from "lucide-react"
import { useState } from "react"
import { ResultCardData } from "@/types"

interface EnhancedResultsCardProps {
  resultCard: ResultCardData | null
  imagePreview: string | null
  onAction?: (action: string) => void
}

export default function EnhancedResultsCard({ 
  resultCard, 
  onAction 
}: EnhancedResultsCardProps) {
  const [showTransparencyTrace, setShowTransparencyTrace] = useState(false)
  const [showRefinementDetails, setShowRefinementDetails] = useState(false)

  if (!resultCard) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Enhanced Classification Results
          </CardTitle>
          <CardDescription>
            Results will appear here after classification
          </CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-64 text-muted-foreground">
          <div className="text-center">
            <p>No results yet</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const handleAction = (action: string) => {
    console.log(`Action triggered: ${action}`)
    onAction?.(action)
  }

  const getConfidenceBadgeColor = (band: string) => {
    switch (band) {
      case 'High':
        return 'bg-green-500 text-white dark:bg-green-600 dark:text-white border-green-500 dark:border-green-600'
      case 'Medium':
        return 'bg-yellow-500 text-white dark:bg-yellow-600 dark:text-white border-yellow-500 dark:border-yellow-600'
      case 'Low':
        return 'bg-red-500 text-white dark:bg-red-600 dark:text-white border-red-500 dark:border-red-600'
      default:
        return 'bg-gray-500 text-white dark:bg-gray-600 dark:text-white'
    }
  }

  const getBandEmoji = (band: string) => {
    switch (band) {
      case 'High': return '■'
      case 'Medium': return '◐'
      case 'Low': return '□'
      default: return '◯'
    }
  }

  const handleDownloadJSON = () => {
    const dataStr = JSON.stringify(resultCard, null, 2)
    const dataBlob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement('a')
    link.href = url
    link.download = `result_${resultCard.image_id}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Card className="h-full overflow-auto">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              Enhanced Classification Results
            </CardTitle>
            <CardDescription>
              Image ID: {resultCard.image_id}
            </CardDescription>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownloadJSON}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            Export JSON
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* TOP PREDICTIONS */}
        <section>
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            🎯 Top Predictions
          </h3>
          <div className="space-y-2">
            {resultCard.top_predictions.map((pred, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-lg">
                      {pred.refined_label}
                    </span>
                    <Badge className={getConfidenceBadgeColor(pred.band)}>
                      {getBandEmoji(pred.band)} {pred.band}
                    </Badge>
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {pred.confidence.toFixed(1)}% confidence
                    {pred.source_candidates.length > 0 && (
                      <span className="ml-2">
                        • Sources: {pred.source_candidates.join(', ')}
                      </span>
                    )}
                  </div>
                </div>
                <div className="text-3xl font-bold text-muted-foreground/30">
                  #{idx + 1}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* LABEL REFINEMENT */}
        {resultCard.label_refinement.length > 0 && (
          <section>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                🔧 Label Refinement
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowRefinementDetails(!showRefinementDetails)}
              >
                {showRefinementDetails ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </div>
            {showRefinementDetails && (
              <div className="space-y-2">
                {resultCard.label_refinement.map((ref, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg border bg-muted/50"
                  >
                    <div className="flex items-center gap-2">
                      <code className="px-2 py-1 rounded bg-background text-sm">
                        {ref.candidate}
                      </code>
                      <span className="text-muted-foreground">→</span>
                      <span className="font-semibold">{ref.refined}</span>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {ref.reason}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>
        )}

        {/* EXPLANATION SECTION */}
        {resultCard.explanation && (
          <section>
            <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
              💡 Explanation
            </h3>
            <div className="p-3 rounded-lg border bg-card">
              <p className="text-sm leading-relaxed">
                {resultCard.explanation}
              </p>
            </div>
          </section>
        )}

        {/* DOMAIN ADAPTATION */}
        <section>
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            🎨 Domain Adaptation & Auto-Tuning
          </h3>
          <div className="p-4 rounded-lg border bg-card space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Detected Style</span>
              <div className="flex items-center gap-2">
                <span className="font-semibold">{resultCard.domain_adaptation.style}</span>
                <Badge variant="outline">
                  {resultCard.domain_adaptation.style_confidence.toFixed(1)}%
                </Badge>
              </div>
            </div>
            
            {resultCard.domain_adaptation.auto_tuning_actions.length > 0 && (
              <>
                <div className="border-t pt-3">
                  <p className="text-sm font-medium mb-2">Auto-Tuning Applied</p>
                  <div className="space-y-1">
                    {resultCard.domain_adaptation.auto_tuning_actions.map((action, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-sm">
                        <CheckCircle className="h-3 w-3 text-black dark:text-white" />
                        <span>{action}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="text-sm text-muted-foreground italic">
                  {resultCard.domain_adaptation.effect_summary}
                </div>
              </>
            )}
          </div>
        </section>

        {/* ANOMALIES */}
        <section>
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            ⚠️ Anomalies & Suggested Fixes
          </h3>
          {resultCard.anomalies.length === 0 ? (
            <div className="p-4 rounded-lg border bg-blue-50 dark:bg-blue-950/30 border-blue-300 dark:border-blue-700">
              <div className="flex items-center gap-2 text-gray-800 dark:text-gray-200">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">No anomalies detected</span>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              {resultCard.anomalies.map((anomaly, idx) => (
                <div
                  key={idx}
                  className="p-4 rounded-lg border bg-blue-50 dark:bg-blue-950/30 border-blue-300 dark:border-blue-700"
                >
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-gray-700 dark:text-gray-300 mt-0.5" />
                    <div className="flex-1 space-y-2">
                      <p className="font-medium text-sm">{anomaly.issue}</p>
                      <div className="flex items-center gap-2">
                        <Info className="h-4 w-4 text-muted-foreground" />
                        <p className="text-sm text-muted-foreground">
                          {anomaly.suggested_fix}
                        </p>
                      </div>
                      <Badge variant="outline" className="text-xs">
                        Confidence: {anomaly.confidence.toFixed(1)}%
                      </Badge>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* TRANSPARENCY TRACE - Hidden */}
        <section className="hidden">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              🔍 Transparency Trace
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowTransparencyTrace(!showTransparencyTrace)}
            >
              {showTransparencyTrace ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
          {showTransparencyTrace && (
            <div className="space-y-4 p-4 rounded-lg border bg-muted/30">
              {/* Final Prompt */}
              <div>
                <p className="text-sm font-medium mb-2">Final Prompt (truncated)</p>
                <code className="block p-2 rounded bg-background text-xs break-all">
                  {resultCard.transparency_trace.final_prompt}
                </code>
              </div>

              {/* Top Text Prompts */}
              <div>
                <p className="text-sm font-medium mb-2">Top Text Prompts</p>
                <div className="space-y-1">
                  {resultCard.transparency_trace.top_text_prompts.map((prompt, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2 rounded bg-background text-sm"
                    >
                      <span className="flex-1 truncate">&quot;{prompt.prompt}&quot;</span>
                      <Badge variant="secondary" className="ml-2 text-xs">
                        {prompt.score.toFixed(2)}
                      </Badge>
                    </div>
                  ))}
                </div>
              </div>

              {/* Tuning Steps */}
              {resultCard.transparency_trace.tuning_steps.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Tuning Steps</p>
                  <div className="space-y-1">
                    {resultCard.transparency_trace.tuning_steps.map((step, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-sm">
                        <div className="h-2 w-2 rounded-full bg-primary" />
                        <span>{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>

        {/* UI ACTIONS */}
        <section>
          <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
            🎬 Actions
          </h3>
          <div className="flex flex-wrap gap-2">
            {resultCard.ui_actions.map((action, idx) => {
              // Map action names to icons
              let Icon = Brain
              if (action.includes('incorrect')) Icon = X
              if (action.includes('Refine')) Icon = RefreshCw
              if (action.includes('Add')) Icon = Plus
              if (action.includes('Export') || action.includes('Download')) Icon = Download

              return (
                <Button
                  key={idx}
                  variant="outline"
                  size="sm"
                  onClick={() => handleAction(action)}
                  className="gap-2"
                >
                  <Icon className="h-4 w-4" />
                  {action}
                </Button>
              )
            })}
          </div>
        </section>
      </CardContent>
    </Card>
  )
}
