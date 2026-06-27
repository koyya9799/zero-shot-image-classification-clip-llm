"use client"

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { BarChart3, ChevronDown, ChevronUp, TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { EvaluationMetrics } from '@/types'

interface MetricsTableProps {
  metrics?: EvaluationMetrics
  loading?: boolean
  className?: string
}

export default function MetricsTable({
  metrics,
  loading = false,
  className
}: MetricsTableProps) {
  const [showPerClass, setShowPerClass] = useState(false)
  const [showDomains, setShowDomains] = useState(false)

  if (loading) {
    return (
      <Card className={cn("w-full", className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 animate-pulse" />
            Computing Metrics...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="flex justify-between">
                <div className="h-4 bg-muted rounded animate-pulse w-32" />
                <div className="h-4 bg-muted rounded animate-pulse w-16" />
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!metrics) {
    return (
      <Card className={cn("w-full", className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Evaluation Metrics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            No metrics available. Run evaluation to see results.
          </p>
        </CardContent>
      </Card>
    )
  }

  const formatPercentage = (value: number) => {
    return (value * 100).toFixed(1) + '%'
  }

  const formatNumber = (value: number, decimals: number = 3) => {
    return value.toFixed(decimals)
  }

  const getScoreBadge = (score: number, threshold: { good: number; fair: number }) => {
    if (score >= threshold.good) {
      return <Badge className="bg-green-500 text-white dark:bg-green-600 dark:text-white">Excellent</Badge>
    } else if (score >= threshold.fair) {
      return <Badge className="bg-yellow-500 text-white dark:bg-yellow-600 dark:text-white">Good</Badge>
    } else {
      return <Badge className="bg-red-500 text-white dark:bg-red-600 dark:text-white">Needs Improvement</Badge>
    }
  }

  const metricsData = [
    {
      category: "Accuracy Metrics",
      metrics: [
        {
          name: "Top-1 Accuracy",
          value: formatPercentage(metrics.top1_accuracy),
          badge: getScoreBadge(metrics.top1_accuracy, { good: 0.8, fair: 0.6 }),
          description: "Percentage of correct top predictions"
        },
        {
          name: "Top-5 Accuracy",
          value: formatPercentage(metrics.top5_accuracy),
          badge: getScoreBadge(metrics.top5_accuracy, { good: 0.9, fair: 0.8 }),
          description: "Percentage of correct predictions in top 5"
        }
      ]
    },
    {
      category: "Precision, Recall & F1",
      metrics: [
        {
          name: "Precision (Weighted)",
          value: formatPercentage(metrics.precision_weighted),
          badge: getScoreBadge(metrics.precision_weighted, { good: 0.8, fair: 0.6 }),
          description: "Weighted average precision across classes"
        },
        {
          name: "Recall (Weighted)",
          value: formatPercentage(metrics.recall_weighted),
          badge: getScoreBadge(metrics.recall_weighted, { good: 0.8, fair: 0.6 }),
          description: "Weighted average recall across classes"
        },
        {
          name: "F1-Score (Weighted)",
          value: formatPercentage(metrics.f1_weighted),
          badge: getScoreBadge(metrics.f1_weighted, { good: 0.8, fair: 0.6 }),
          description: "Weighted harmonic mean of precision and recall"
        },
        {
          name: "F1-Score (Macro)",
          value: formatPercentage(metrics.f1_macro),
          badge: getScoreBadge(metrics.f1_macro, { good: 0.7, fair: 0.5 }),
          description: "Unweighted average F1 across classes"
        }
      ]
    },
    {
      category: "Advanced Metrics",
      metrics: [
        {
          name: "Mean Average Precision (mAP)",
          value: formatPercentage(metrics.map),
          badge: getScoreBadge(metrics.map, { good: 0.8, fair: 0.6 }),
          description: "Average precision across all classes"
        },
        {
          name: "Cross-Domain Drop",
          value: formatPercentage(metrics.cross_domain_drop),
          badge: metrics.cross_domain_drop <= 0.2 ? 
            <Badge className="bg-green-500 text-white dark:bg-green-600 dark:text-white">Low</Badge> :
            metrics.cross_domain_drop <= 0.4 ?
            <Badge className="bg-yellow-500 text-white dark:bg-yellow-600 dark:text-white">Medium</Badge> :
            <Badge className="bg-red-500 text-white dark:bg-red-600 dark:text-white">High</Badge>,
          description: "Performance drop across different domains",
          icon: metrics.cross_domain_drop <= 0.2 ? TrendingUp : TrendingDown
        },
        {
          name: "Expected Calibration Error",
          value: formatNumber(metrics.ece),
          badge: metrics.ece <= 0.1 ? 
            <Badge className="bg-green-500 text-white dark:bg-green-600 dark:text-white">Well Calibrated</Badge> :
            <Badge className="bg-yellow-500 text-white dark:bg-yellow-600 dark:text-white">Fair</Badge>,
          description: "Measure of prediction confidence calibration"
        }
      ]
    }
  ]

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Evaluation Metrics
        </CardTitle>
        <div className="flex gap-4 text-sm text-muted-foreground">
          <span>Samples: {metrics.num_samples}</span>
          <span>Classes: {metrics.num_classes}</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {metricsData.map((category, categoryIndex) => (
            <div key={categoryIndex} className="space-y-3">
              <h3 className="font-semibold text-sm text-muted-foreground uppercase tracking-wide">
                {category.category}
              </h3>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Metric</TableHead>
                    <TableHead>Value</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="hidden md:table-cell">Description</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {category.metrics.map((metric, metricIndex) => {
                    const Icon = metric.icon
                    return (
                      <TableRow key={metricIndex}>
                        <TableCell className="font-medium">
                          <div className="flex items-center gap-2">
                            {Icon && <Icon className="h-4 w-4" />}
                            {metric.name}
                          </div>
                        </TableCell>
                        <TableCell className="font-mono">
                          {metric.value}
                        </TableCell>
                        <TableCell>
                          {metric.badge}
                        </TableCell>
                        <TableCell className="hidden md:table-cell text-sm text-muted-foreground">
                          {metric.description}
                        </TableCell>
                      </TableRow>
                    )
                  })}
                </TableBody>
              </Table>
            </div>
          ))}
        </div>

        {/* Per-Class Metrics - Expandable */}
        {metrics.per_class_metrics && Object.keys(metrics.per_class_metrics).length > 0 && (
          <div className="mt-6 border-t pt-6">
            <Button
              variant="outline"
              onClick={() => setShowPerClass(!showPerClass)}
              className="w-full justify-between"
            >
              <span className="font-semibold">Per-Class Metrics ({Object.keys(metrics.per_class_metrics).length} classes)</span>
              {showPerClass ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
            
            {showPerClass && (
              <div className="mt-4 max-h-96 overflow-y-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Class</TableHead>
                      <TableHead>Precision</TableHead>
                      <TableHead>Recall</TableHead>
                      <TableHead>F1-Score</TableHead>
                      <TableHead>Samples</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(metrics.per_class_metrics)
                      .sort(([, a], [, b]) => b.f1 - a.f1)
                      .map(([className, classMetrics]) => (
                        <TableRow key={className}>
                          <TableCell className="font-medium">{className}</TableCell>
                          <TableCell className="font-mono">{formatPercentage(classMetrics.precision)}</TableCell>
                          <TableCell className="font-mono">{formatPercentage(classMetrics.recall)}</TableCell>
                          <TableCell className="font-mono">
                            <span className={cn(
                              "px-2 py-1 rounded",
                              classMetrics.f1 >= 0.8 ? "bg-gray-200 text-gray-800 dark:bg-gray-800 dark:text-gray-200" :
                              classMetrics.f1 >= 0.6 ? "bg-gray-300 text-gray-800 dark:bg-gray-700 dark:text-gray-200" :
                              "bg-gray-400 text-gray-800 dark:bg-gray-600 dark:text-gray-100"
                            )}>
                              {formatPercentage(classMetrics.f1)}
                            </span>
                          </TableCell>
                          <TableCell>{classMetrics.samples}</TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        )}

        {/* Domain Performance - Expandable */}
        {metrics.domain_performance && Object.keys(metrics.domain_performance).length > 0 && (
          <div className="mt-6 border-t pt-6">
            <Button
              variant="outline"
              onClick={() => setShowDomains(!showDomains)}
              className="w-full justify-between"
            >
              <span className="font-semibold">Domain Performance ({Object.keys(metrics.domain_performance).length} domains)</span>
              {showDomains ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
            
            {showDomains && (
              <div className="mt-4">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Domain</TableHead>
                      <TableHead>Accuracy</TableHead>
                      <TableHead>Samples</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {Object.entries(metrics.domain_performance)
                      .sort(([, a], [, b]) => b.accuracy - a.accuracy)
                      .map(([domain, perf]) => (
                        <TableRow key={domain}>
                          <TableCell className="font-medium">{domain}</TableCell>
                          <TableCell className="font-mono">{formatPercentage(perf.accuracy)}</TableCell>
                          <TableCell>{perf.samples}</TableCell>
                          <TableCell>{getScoreBadge(perf.accuracy, { good: 0.8, fair: 0.6 })}</TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
