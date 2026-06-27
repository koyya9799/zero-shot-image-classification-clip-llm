'use client'

import { useState, useRef } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import MetricsChart from '@/components/MetricsChart'
import MetricsTable from '@/components/MetricsTable'
import { Upload, FileText, Trash2, Play, Download, FileUp, AlertCircle, CheckCircle2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { EvaluationMetrics } from '@/types'

interface FileWithLabel {
  file: File
  label: string
  status?: 'pending' | 'processing' | 'success' | 'error'
}

export default function EvaluatePage() {
  const [files, setFiles] = useState<FileWithLabel[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [metrics, setMetrics] = useState<EvaluationMetrics | null>(null)
  const [error, setError] = useState<string>('')
  const [success, setSuccess] = useState<string>('')
  const fileInputRef = useRef<HTMLInputElement>(null)
  const csvInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || [])
    const newFiles = selectedFiles.map(file => ({
      file,
      label: '',
      status: 'pending' as const
    }))
    setFiles(prev => [...prev, ...newFiles])
    setError('')
    setSuccess('')
  }

  const handleCSVImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (event) => {
      try {
        const text = event.target?.result as string
        const lines = text.split('\n').filter(line => line.trim())
        
        // Parse CSV: filename,label
        const labelMap = new Map<string, string>()
        lines.forEach((line, idx) => {
          if (idx === 0 && line.toLowerCase().includes('filename')) return // Skip header
          const [filename, label] = line.split(',').map(s => s.trim())
          if (filename && label) {
            labelMap.set(filename, label)
          }
        })

        // Apply labels to matching files
        setFiles(prev => prev.map(f => {
          const label = labelMap.get(f.file.name)
          return label ? { ...f, label } : f
        }))

        setSuccess(`Imported labels for ${labelMap.size} files`)
        setTimeout(() => setSuccess(''), 3000)
      } catch (err) {
        setError('Failed to parse CSV file. Expected format: filename,label')
      }
    }
    reader.readAsText(file)
    
    if (csvInputRef.current) {
      csvInputRef.current.value = ''
    }
  }

  const handleLabelChange = (index: number, label: string) => {
    setFiles(prev => prev.map((f, i) => 
      i === index ? { ...f, label } : f
    ))
  }

  const handleRemoveFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index))
  }

  const handleClearAll = () => {
    setFiles([])
    setMetrics(null)
    setError('')
    setSuccess('')
    setProgress(0)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleEvaluate = async () => {
    // Validation
    if (files.length === 0) {
      setError('Please upload at least one image')
      return
    }

    const unlabeled = files.filter(f => !f.label.trim())
    if (unlabeled.length > 0) {
      setError(`${unlabeled.length} file(s) missing labels. Please label all images.`)
      return
    }

    setIsLoading(true)
    setError('')
    setSuccess('')
    setProgress(0)

    // Update file statuses to processing
    setFiles(prev => prev.map(f => ({ ...f, status: 'processing' as const })))

    try {
      const formData = new FormData()
      
      // Add files
      files.forEach(({ file }) => {
        formData.append('files', file)
      })
      
      // Add labels
      files.forEach(({ label }) => {
        formData.append('labels', label.trim().toLowerCase())
      })

      setProgress(30)

      const response = await fetch('/api/evaluate', {
        method: 'POST',
        body: formData
      })

      setProgress(80)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || `Evaluation failed: ${response.status}`)
      }

      const data = await response.json()
      
      setProgress(100)

      if (data.status === 'ok' && data.metrics) {
        setMetrics(data.metrics)
        setFiles(prev => prev.map(f => ({ ...f, status: 'success' as const })))
        setSuccess(`Successfully evaluated ${files.length} images`)
        setTimeout(() => setSuccess(''), 3000)
      } else {
        throw new Error('Invalid response format')
      }
    } catch (err) {
      console.error('Evaluation error:', err)
      setError(err instanceof Error ? err.message : 'Failed to evaluate model')
      setFiles(prev => prev.map(f => ({ ...f, status: 'error' as const })))
    } finally {
      setIsLoading(false)
      setTimeout(() => setProgress(0), 1000)
    }
  }

  const handleDownloadResults = () => {
    if (!metrics) return

    const results = {
      timestamp: new Date().toISOString(),
      num_samples: files.length,
      metrics,
      files: files.map(f => ({
        filename: f.file.name,
        label: f.label
      }))
    }

    const blob = new Blob([JSON.stringify(results, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `evaluation_results_${Date.now()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Model Evaluation</h1>
          <p className="text-muted-foreground mt-2">
            Upload a test dataset to evaluate CLIP model performance
          </p>
        </div>
        {metrics && (
          <Button onClick={handleDownloadResults} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            Download Results
          </Button>
        )}
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Upload Test Dataset
          </CardTitle>
          <CardDescription>
            Upload images with their ground truth labels to evaluate model accuracy
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Input */}
          <div className="flex gap-4">
            <div className="flex-1">
              <Input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleFileSelect}
                className="cursor-pointer"
              />
            </div>
            <div>
              <Input
                ref={csvInputRef}
                type="file"
                accept=".csv"
                onChange={handleCSVImport}
                className="hidden"
                id="csv-upload"
              />
              <Button 
                onClick={() => csvInputRef.current?.click()} 
                variant="outline"
                title="Import labels from CSV (format: filename,label)"
              >
                <FileUp className="h-4 w-4 mr-2" />
                Import CSV
              </Button>
            </div>
            {files.length > 0 && (
              <Button onClick={handleClearAll} variant="outline" size="icon">
                <Trash2 className="h-4 w-4" />
              </Button>
            )}
          </div>

          {/* Success/Error Messages */}
          {success && (
            <div className="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 text-green-800 dark:text-green-200 px-4 py-3 rounded-lg flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" />
              {success}
            </div>
          )}
          
          {error && (
            <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 px-4 py-3 rounded-lg flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              {error}
            </div>
          )}

          {/* Progress Bar */}
          {isLoading && progress > 0 && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Processing...</span>
                <span className="font-medium">{progress}%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-primary transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          {/* File List */}
          {files.length > 0 && (
            <div className="space-y-3 max-h-96 overflow-y-auto border rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  {files.length} image{files.length !== 1 ? 's' : ''} uploaded
                </span>
                <Badge variant="secondary">
                  {files.filter(f => f.label.trim()).length}/{files.length} labeled
                </Badge>
              </div>
              
              {files.map((item, index) => (
                <div key={index} className="flex items-center gap-3 p-3 bg-muted rounded-lg">
                  {/* Status Indicator */}
                  <div className="flex-shrink-0">
                    {item.status === 'success' && (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                    {item.status === 'error' && (
                      <AlertCircle className="h-5 w-5 text-red-500" />
                    )}
                    {item.status === 'processing' && (
                      <div className="animate-spin h-5 w-5 border border-primary border-t-transparent rounded-full" />
                    )}
                    {(!item.status || item.status === 'pending') && (
                      <div className="h-5 w-5 rounded-full border border-muted-foreground" />
                    )}
                  </div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{item.file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(item.file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                  
                  <div className="flex-1">
                    <Label htmlFor={`label-${index}`} className="sr-only">
                      Ground truth label
                    </Label>
                    <Input
                      id={`label-${index}`}
                      type="text"
                      placeholder="Ground truth label"
                      value={item.label}
                      onChange={(e) => handleLabelChange(index, e.target.value)}
                      className="h-9"
                      disabled={isLoading}
                    />
                  </div>
                  
                  <Button
                    onClick={() => handleRemoveFile(index)}
                    variant="ghost"
                    size="icon"
                    className="h-9 w-9"
                    disabled={isLoading}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-destructive/10 text-destructive px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          {/* Evaluate Button */}
          <Button 
            onClick={handleEvaluate} 
            disabled={isLoading || files.length === 0}
            className="w-full"
            size="lg"
          >
            {isLoading ? (
              <>
                <div className="animate-spin h-4 w-4 border border-current border-t-transparent rounded-full mr-2" />
                Evaluating {files.length} images...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Evaluate Model
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Results Section */}
      {(isLoading || metrics) && (
        <>
          {/* Metrics Table */}
          <MetricsTable metrics={metrics || undefined} loading={isLoading} />

          {/* Metrics Charts */}
          <MetricsChart metrics={metrics || undefined} loading={isLoading} />

          {/* Per-Class Metrics */}
          {metrics?.per_class_metrics && (
            <Card>
              <CardHeader>
                <CardTitle>Per-Class Performance</CardTitle>
                <CardDescription>
                  Detailed metrics for each class in the test dataset
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {Object.entries(metrics.per_class_metrics)
                    .sort(([, a], [, b]) => b.f1 - a.f1)
                    .map(([className, classMetrics]) => (
                      <div key={className} className="border rounded-lg p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <h4 className="font-semibold capitalize">{className}</h4>
                          <Badge variant="secondary">
                            {classMetrics.samples} sample{classMetrics.samples !== 1 ? 's' : ''}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          <div>
                            <span className="text-muted-foreground">Precision:</span>
                            <span className="ml-2 font-medium">
                              {(classMetrics.precision * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">Recall:</span>
                            <span className="ml-2 font-medium">
                              {(classMetrics.recall * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div>
                            <span className="text-muted-foreground">F1-Score:</span>
                            <span className="ml-2 font-medium">
                              {(classMetrics.f1 * 100).toFixed(1)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Domain Performance */}
          {metrics?.domain_performance && Object.keys(metrics.domain_performance).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Domain-Specific Performance</CardTitle>
                <CardDescription>
                  Performance breakdown across different domains
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(metrics.domain_performance).map(([domain, stats]) => (
                    <div key={domain} className="border rounded-lg p-4">
                      <h4 className="font-semibold capitalize mb-2">{domain}</h4>
                      <div className="space-y-1 text-sm">
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Accuracy:</span>
                          <span className="font-medium">
                            {(stats.accuracy * 100).toFixed(1)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Samples:</span>
                          <span className="font-medium">{stats.samples}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
