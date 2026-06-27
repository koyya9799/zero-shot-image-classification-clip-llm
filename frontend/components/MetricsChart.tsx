"use client"

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { BarChart3, Target, Layers } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { EvaluationMetrics } from '@/types'

interface MetricsChartProps {
  metrics?: EvaluationMetrics
  loading?: boolean
  className?: string
}

export default function MetricsChart({
  metrics,
  loading = false,
  className
}: MetricsChartProps) {
  if (loading) {
    return (
      <Card className={cn("w-full", className)}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5 animate-pulse" />
            Loading Chart...
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 bg-muted rounded animate-pulse" />
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
            Metrics Chart
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80 flex items-center justify-center text-muted-foreground">
            No data available for chart
          </div>
        </CardContent>
      </Card>
    )
  }

  // Prepare data for the chart
  const chartData = [
    {
      name: 'Top-1 Acc',
      value: metrics.top1_accuracy * 100,
      color: '#3b82f6'
    },
    {
      name: 'Top-5 Acc',
      value: metrics.top5_accuracy * 100,
      color: '#8b5cf6'
    },
    {
      name: 'Precision',
      value: metrics.precision_weighted * 100,
      color: '#ec4899'
    },
    {
      name: 'Recall',
      value: metrics.recall_weighted * 100,
      color: '#f59e0b'
    },
    {
      name: 'F1 (Weighted)',
      value: metrics.f1_weighted * 100,
      color: '#10b981'
    },
    {
      name: 'F1 (Macro)',
      value: metrics.f1_macro * 100,
      color: '#06b6d4'
    },
    {
      name: 'mAP',
      value: metrics.map * 100,
      color: '#6366f1'
    }
  ]

  // Additional metrics (inverted scale for better visualization)
  const additionalMetrics = [
    {
      name: 'Domain Robustness',
      value: (1 - metrics.cross_domain_drop) * 100,
      description: '100% - Cross-domain Drop'
    },
    {
      name: 'Calibration Quality',
      value: Math.max(0, (1 - metrics.ece) * 100),
      description: '100% - Expected Calibration Error'
    }
  ]

  const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: Array<{ value: number; color: string }>; label?: string }) => {
    if (active && payload && payload.length) {
      const data = payload[0]
      return (
        <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
          <p className="font-medium">{label}</p>
          <p className="text-primary">
            <span className="inline-block w-3 h-3 rounded mr-2" 
                  style={{ backgroundColor: data.color }} />
            {data.value.toFixed(1)}%
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Main Metrics Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Performance Metrics Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis 
                  dataKey="name" 
                  stroke="hsl(var(--foreground))"
                  tick={{ fontSize: 12 }}
                  angle={-45}
                  textAnchor="end"
                  height={60}
                />
                <YAxis 
                  stroke="hsl(var(--foreground))"
                  tick={{ fontSize: 12 }}
                  domain={[0, 100]}
                  label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar 
                  dataKey="value" 
                  fill="hsl(var(--primary))"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Domain Performance Chart */}
      {metrics.domain_performance && Object.keys(metrics.domain_performance).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Layers className="h-5 w-5" />
              Performance by Domain
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart 
                  data={Object.entries(metrics.domain_performance).map(([domain, perf]) => ({
                    name: domain,
                    accuracy: perf.accuracy * 100,
                    samples: perf.samples
                  }))}
                  margin={{ top: 20, right: 30, left: 20, bottom: 40 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis 
                    dataKey="name" 
                    stroke="hsl(var(--foreground))"
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis 
                    stroke="hsl(var(--foreground))"
                    tick={{ fontSize: 12 }}
                    domain={[0, 100]}
                    label={{ value: 'Accuracy (%)', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip 
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-background border border-border rounded-lg p-3 shadow-lg">
                            <p className="font-medium">{payload[0].payload.name}</p>
                            <p className="text-primary">Accuracy: {payload[0].value?.toFixed(1)}%</p>
                            <p className="text-sm text-muted-foreground">Samples: {payload[0].payload.samples}</p>
                          </div>
                        )
                      }
                      return null
                    }}
                  />
                  <Bar dataKey="accuracy" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Per-Class Performance - Top/Bottom Classes */}
      {metrics.per_class_metrics && Object.keys(metrics.per_class_metrics).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              Top & Bottom Performing Classes
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              {/* Top 5 Classes */}
              <div>
                <h4 className="font-medium mb-3 text-gray-700 dark:text-gray-300">Top 5 Classes (by F1)</h4>
                <div className="space-y-2">
                  {Object.entries(metrics.per_class_metrics)
                    .sort(([, a], [, b]) => b.f1 - a.f1)
                    .slice(0, 5)
                    .map(([className, classMetrics], idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span className="font-medium truncate">{className}</span>
                          <span className="text-gray-700 dark:text-gray-300">{(classMetrics.f1 * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div 
                            className="h-2 rounded-full bg-green-500 dark:bg-green-400"
                            style={{ width: `${classMetrics.f1 * 100}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>P: {(classMetrics.precision * 100).toFixed(1)}%</span>
                          <span>R: {(classMetrics.recall * 100).toFixed(1)}%</span>
                          <span>{classMetrics.samples} samples</span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>

              {/* Bottom 5 Classes */}
              <div>
                <h4 className="font-medium mb-3 text-gray-700 dark:text-gray-300">Bottom 5 Classes (by F1)</h4>
                <div className="space-y-2">
                  {Object.entries(metrics.per_class_metrics)
                    .sort(([, a], [, b]) => a.f1 - b.f1)
                    .slice(0, 5)
                    .map(([className, classMetrics], idx) => (
                      <div key={idx} className="space-y-1">
                        <div className="flex justify-between text-sm">
                          <span className="font-medium truncate">{className}</span>
                          <span className="text-gray-700 dark:text-gray-300">{(classMetrics.f1 * 100).toFixed(1)}%</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div 
                            className="h-2 rounded-full bg-red-500 dark:bg-red-400"
                            style={{ width: `${classMetrics.f1 * 100}%` }}
                          />
                        </div>
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>P: {(classMetrics.precision * 100).toFixed(1)}%</span>
                          <span>R: {(classMetrics.recall * 100).toFixed(1)}%</span>
                          <span>{classMetrics.samples} samples</span>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Additional Metrics */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-5 w-5" />
            Robustness & Calibration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {additionalMetrics.map((metric, index) => {
              const percentage = metric.value
              const getColor = (value: number) => {
                if (value >= 80) return 'bg-green-500 dark:bg-green-400'
                if (value >= 60) return 'bg-yellow-500 dark:bg-yellow-400'
                return 'bg-red-500 dark:bg-red-400'
              }

              return (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium">{metric.name}</span>
                    <span className="text-sm text-muted-foreground">
                      {percentage.toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-muted rounded-full h-3">
                    <div 
                      className={cn("h-3 rounded-full transition-all", getColor(percentage))}
                      style={{ width: `${Math.min(100, Math.max(0, percentage))}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {metric.description}
                  </p>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Stats</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {(metrics.top1_accuracy * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">Top-1 Accuracy</div>
            </div>
            
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-2xl font-bold text-gray-800 dark:text-gray-200">
                {(metrics.f1_weighted * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">F1-Score</div>
            </div>
            
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-2xl font-bold text-gray-700 dark:text-gray-300">
                {(metrics.map * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">mAP</div>
            </div>
            
            <div className="text-center p-4 bg-muted rounded-lg">
              <div className="text-2xl font-bold text-gray-600 dark:text-gray-400">
                {((1 - metrics.cross_domain_drop) * 100).toFixed(1)}%
              </div>
              <div className="text-sm text-muted-foreground">Domain Robustness</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
