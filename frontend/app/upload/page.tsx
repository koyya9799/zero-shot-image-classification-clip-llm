'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import ImageUploadCard from "@/components/ImageUploadCard"
import ClassificationProgress, { ProcessStep, StepStatus } from "@/components/ClassificationProgress"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Upload, ArrowLeft, Sparkles, Image as ImageIcon, Tags, Loader2, X } from "lucide-react"
import Link from "next/link"
import type { ClassificationResult } from "@/types"
import { apiClient } from "@/lib/api"

export default function UploadPage() {
  const [selectedImage, setSelectedImage] = useState<File | null>(null)
  const [imagePreview, setImagePreview] = useState<string | null>(null)
  const [labels, setLabels] = useState<string[]>([])
  const [newLabel, setNewLabel] = useState('')
  const [results, setResults] = useState<ClassificationResult | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isPredicting, setIsPredicting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isCancelled, setIsCancelled] = useState(false)

  // Progress tracking
  const [showProgress, setShowProgress] = useState(false)
  const [processSteps, setProcessSteps] = useState<ProcessStep[]>([])
  const [currentStepIndex, setCurrentStepIndex] = useState(0)
  const [sessionId, setSessionId] = useState<string>('')

  // Helper function to update step status
  const updateStepStatus = (stepId: string, status: StepStatus, errorMessage?: string) => {
    setProcessSteps(prevSteps =>
      prevSteps.map(step =>
        step.id === stepId
          ? { ...step, status, errorMessage }
          : step
      )
    )
  }

  // Initialize progress steps
  const initializeProgressSteps = () => {
    const steps: ProcessStep[] = [
      {
        id: 'health-check',
        label: 'Backend Check',
        description: 'Verifying backend connection',
        status: 'pending'
      },
      {
        id: 'detect-objects',
        label: 'Domain Detection',
        description: 'Auto-detecting image domain & model routing',
        status: 'pending'
      },
      {
        id: 'analyze-image',
        label: 'CLIP & LLM Analysis',
        description: 'MedCLIP for medical, ViT-H/14 for others',
        status: 'pending'
      },
      {
        id: 'generate-results',
        label: 'Results Ready',
        description: 'Finalizing predictions',
        status: 'pending'
      }
    ]
    setProcessSteps(steps)
    setCurrentStepIndex(0)
    setSessionId(`CLS-${Date.now()}`)
    setShowProgress(true)
  }

  const handleImageSelect = (file: File) => {
    setSelectedImage(file)
    const reader = new FileReader()
    reader.onload = (e) => {
      setImagePreview(e.target?.result as string)
    }
    reader.readAsDataURL(file)
    setResults(null)
    setError(null)
    setLabels([])
    // Don't auto-classify on upload - wait for button click
  }

  const handleClearImage = () => {
    setSelectedImage(null)
    setImagePreview(null)
    setLabels([])
    setResults(null)
    setError(null)
    setShowProgress(false)
    setProcessSteps([])
  }

  const checkBackendHealth = async (): Promise<boolean> => {
    try {
      await apiClient.healthCheck()
      return true
    } catch (error) {
      console.error('Backend health check failed:', error)
      return false
    }
  }

  const handleStartClassification = async () => {
    if (!selectedImage) {
      setError('Please select an image first')
      return
    }

    // Initialize progress tracking
    initializeProgressSteps()
    setError(null)
    setResults(null)
    setIsCancelled(false)

    // Start classification with progress
    await handleAutoClassify(selectedImage)
  }

  const handleStopClassification = () => {
    setIsCancelled(true)
    setIsPredicting(false)
    setShowProgress(false)
    setError('Classification cancelled by user')
  }

  const handleAutoClassify = async (imageFile: File) => {
    setIsPredicting(true)
    setLabels([])

    try {
      // Step 1: Backend Health Check
      setCurrentStepIndex(0)
      updateStepStatus('health-check', 'in-progress')

      const backendHealthy = await checkBackendHealth()
      if (!backendHealthy) {
        updateStepStatus('health-check', 'error', 'Backend not responding')
        setShowProgress(false)
        return
      }

      if (isCancelled) return

      updateStepStatus('health-check', 'completed')
      await new Promise(resolve => setTimeout(resolve, 300)) // Brief pause for visual feedback

      if (isCancelled) return

      // Step 2: Domain Detection & Model Routing
      setCurrentStepIndex(1)
      updateStepStatus('detect-objects', 'in-progress')
      await new Promise(resolve => setTimeout(resolve, 500))
      
      if (isCancelled) return
      
      updateStepStatus('detect-objects', 'completed')
      await new Promise(resolve => setTimeout(resolve, 300))

      if (isCancelled) return

      // Step 3: Analyze Image with Hybrid Model (MedCLIP for medical, ViT-H/14 for others)
      setCurrentStepIndex(2)
      updateStepStatus('analyze-image', 'in-progress')

      const result = await apiClient.classifyImage(imageFile)

      if (isCancelled) return

      const normalizedResult = {
        ...result,
        label: result.prediction || result.label || 'Unknown',
        confidence: result.confidence ?? result.confidence_score ?? 0,
        candidates: result.top_matches?.map((m: any) => ({ label: m.label, score: m.score })) || result.candidates || []
      }

      updateStepStatus('analyze-image', 'completed')
      await new Promise(resolve => setTimeout(resolve, 300))

      if (isCancelled) return

      // Step 4: Generate Results
      setCurrentStepIndex(3)
      updateStepStatus('generate-results', 'in-progress')

      // Extract detected labels from results
      const detectedLabels = normalizedResult.candidates
        .filter(c => c.score > 0.01)
        .map(c => c.label)
        .filter(l => l && l.trim())

      setLabels(detectedLabels)

      await new Promise(resolve => setTimeout(resolve, 500))
      updateStepStatus('generate-results', 'completed')

      // Wait a moment to show all steps complete
      await new Promise(resolve => setTimeout(resolve, 800))

      // Hide progress and show results
      setShowProgress(false)
      setResults(normalizedResult)

    } catch (error) {
      console.error('Auto-classification failed:', error)

      // Mark current step as error
      const currentStep = processSteps[currentStepIndex]
      if (currentStep) {
        updateStepStatus(
          currentStep.id,
          'error',
          error instanceof Error ? error.message : 'Classification failed'
        )
      }

      setError(
        error instanceof Error
          ? error.message
          : 'Auto-classification failed. Please ensure the backend is running.'
      )

      // Keep progress visible to show error
      setTimeout(() => setShowProgress(false), 3000)
    } finally {
      setIsPredicting(false)
    }
  }

  const handleAddLabel = () => {
    const trimmed = newLabel.trim()
    if (trimmed && !labels.includes(trimmed)) {
      setLabels([...labels, trimmed])
      setNewLabel('')
    }
  }

  const handleRemoveLabel = (label: string) => {
    setLabels(labels.filter(l => l !== label))
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      handleAddLabel()
    }
  }

  const handleClassify = async () => {
    if (!selectedImage) {
      setError('Please select an image')
      return
    }

    // Check if backend is running before proceeding
    const backendHealthy = await checkBackendHealth()
    if (!backendHealthy) {
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      // Classify with custom labels if provided, otherwise auto-detect
      const classifyWithLabels = labels.length > 0 ? labels.join(', ') : undefined
      const result = await apiClient.classifyImage(selectedImage, classifyWithLabels)
      setResults(result)
    } catch (error) {
      console.error('Classification failed:', error)
      setError(
        error instanceof Error
          ? error.message
          : 'Classification failed. Please make sure the backend is running.'
      )
    } finally {
      setIsLoading(false)
    }
  }

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.7) return { label: 'High', color: 'bg-gray-800 dark:bg-gray-100 text-white dark:text-black' }
    if (confidence >= 0.4) return { label: 'Medium', color: 'bg-gray-600 dark:bg-gray-300 text-white dark:text-black' }
    return { label: 'Low', color: 'bg-gray-400 dark:bg-gray-500 text-white dark:text-black' }
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-3 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/home">
            <Button size="sm" className="rounded-lg bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-200">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Home
            </Button>
          </Link>
          <div className="flex items-center gap-3">
            <div className="bg-gray-200 dark:bg-gray-800 p-2 rounded-xl">
              <Upload className="h-6 w-6 text-black dark:text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-black dark:text-white">Upload & Classify</h1>
              <p className="text-sm text-black dark:text-white">Zero-shot image classification with CLIP & LLM</p>
            </div>
          </div>
        </div>
      </div>

      {/* Upload and Classification Section */}
      <div className="space-y-4">
        <div className={`grid gap-4 items-stretch ${showProgress ? 'lg:grid-cols-2' : 'grid-cols-1'}`}>
          {/* Combined Upload and Classification Card */}
          <Card className="h-3/4 shadow-md border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-950">
            <CardContent className="h-full py-6 flex flex-col justify-center items-center">
              {!selectedImage ? (
                // Before upload - Full card upload area
                <div className="h-full w-full">
                  <ImageUploadCard
                    onImageUpload={handleImageSelect}
                    onClear={handleClearImage}
                    selectedImage={selectedImage}
                    imagePreview={imagePreview}
                  />
                </div>
              ) : (
                // After upload - Split into upload area and button side-by-side
                <div className="w-full h-full flex flex-col lg:flex-row items-center justify-center gap-6 lg:gap-8 px-4 py-6 overflow-hidden">
                  {/* Upload Area */}
                  <div className="w-full max-w-60 shrink-0 mx-auto lg:mx-0">
                    <ImageUploadCard
                      onImageUpload={handleImageSelect}
                      onClear={handleClearImage}
                      selectedImage={selectedImage}
                      imagePreview={imagePreview}
                    />
                  </div>

                  {/* Classification Buttons */}
                  <div className="flex flex-col items-center justify-center gap-3">
                    {!isPredicting ? (
                      <Button
                        onClick={handleStartClassification}
                        className="w-64 h-14 text-base font-semibold bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-200 shadow-lg hover:shadow-xl transition-all"
                      >
                        <Sparkles className="h-5 w-5 mr-2" />
                        <span>Start Classification</span>
                      </Button>
                    ) : (
                      <>
                        <Button
                          disabled
                          className="w-64 h-14 text-base font-semibold bg-black dark:bg-white text-white dark:text-black opacity-70 shadow-lg"
                        >
                          <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                          <span>Classifying...</span>
                        </Button>
                        <Button
                          onClick={handleStopClassification}
                          variant="outline"
                          className="w-64 h-14 text-base font-semibold border-2 border-red-500 dark:border-red-600 text-red-600 dark:text-red-500 hover:bg-red-50 dark:hover:bg-red-950 hover:text-red-700 dark:hover:text-red-400 shadow-lg hover:shadow-xl transition-all"
                        >
                          <X className="h-5 w-5 mr-2" />
                          <span>Stop</span>
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Progress Indicator */}
          {showProgress && (
            <ClassificationProgress
              steps={processSteps}
              currentStepIndex={currentStepIndex}
              transactionId={sessionId}
            />
          )}
        </div>

        {/* Error Display */}
        {error && (
          <Card className="shadow-md border border-gray-300 dark:border-gray-700">
            <CardContent className="pt-6">
              <div className="bg-gray-100 dark:bg-gray-900/50 border border-gray-300 dark:border-gray-700 rounded-lg p-4">
                <p className="text-sm text-gray-900 dark:text-gray-100 flex items-center gap-2">
                  <X className="h-4 w-4" />
                  {error}
                </p>
              </div>
            </CardContent>
          </Card>
        )}

      </div>

      {/* Classification Results - Only show when results are ready */}
      {results && (
        <Card className="shadow-md">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-black dark:text-white" />
              Classification Results
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-8">
              {/* Top Row - Image Preview (Full Width) - Hidden */}
              {imagePreview && (
                <div className="w-full hidden">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                    <ImageIcon className="h-4 w-4" />
                    Classified Image
                  </h3>
                  <div className="relative rounded-xl overflow-hidden border border-gray-300 dark:border-gray-700 shadow-lg bg-gray-100 dark:bg-gray-900/30">
                    <img
                      src={imagePreview}
                      alt="Uploaded"
                      className="w-full h-auto max-h-96 object-contain p-4"
                    />
                  </div>
                </div>
              )}

              {/* Main Content Grid */}
              <div className="grid lg:grid-cols-3 gap-6">
                {/* Left Column - Top Prediction & Domain */}
                <div className="lg:col-span-1 space-y-4">
                  {/* Top Prediction */}
                  <div className="bg-gray-100 dark:bg-gray-900/30 rounded-xl p-5 border border-gray-300 dark:border-gray-700 shadow-md">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-1 uppercase tracking-wide">
                          Top Prediction
                        </p>
                        <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 capitalize">
                          {results.prediction}
                        </h3>
                      </div>
                      {/* Badge removed as requested */}
                    </div>
                    {/* <div className="mt-4">
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-gray-600 dark:text-gray-400">Confidence Score</span>
                        <span className="font-bold text-gray-900 dark:text-gray-100">
                          {((results.confidence ?? 0) * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-300 dark:bg-gray-700 rounded-full h-3">
                        <div
                          className={`h-3 rounded-full transition-all duration-300 ${getConfidenceBadge(results.confidence ?? 0).color}`}
                          style={{ width: `${(results.confidence ?? 0) * 100}%` }}
                        ></div>
                      </div>
                    </div> */}
                  </div>

                  {/* Domain Info */}
                  <div className="bg-gray-100 dark:bg-gray-900/30 rounded-xl p-4 border border-gray-300 dark:border-gray-700 space-y-3">
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <ImageIcon className="h-4 w-4 text-gray-700 dark:text-gray-300" />
                        <span className="text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide">
                          Image Domain
                        </span>
                      </div>
                      <Badge className="capitalize bg-gray-800 dark:bg-gray-200 text-white dark:text-black border border-gray-700 dark:border-gray-300">
                        {results.domain}
                      </Badge>
                    </div>
                  </div>
                </div>

                {/* Middle Column - Candidates & Objects */}
                <div className="lg:col-span-1 space-y-4">
                  {/* Top Candidates */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2 uppercase tracking-wide">
                      <Tags className="h-4 w-4 text-gray-700 dark:text-gray-300" />
                      Top Predictions
                    </h4>
                    <div className="space-y-2">
                      {results.top_predictions?.slice(0, 5).map((candidate, idx) => {
                        const confidencePercent = (candidate.score * 100).toFixed(1)
                        const badge = getConfidenceBadge(candidate.score)

                        return (
                          <div
                            key={idx}
                            className="flex items-center justify-between p-3 bg-gray-100 dark:bg-gray-900/40 rounded-lg border border-gray-300 dark:border-gray-700 hover:shadow-md transition-shadow"
                          >
                            <div className="flex items-center gap-2 flex-1">
                              <span className="text-xs font-bold text-gray-400 dark:text-gray-500 w-6">
                                #{idx + 1}
                              </span>
                              <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 capitalize">
                                {candidate.label}
                              </span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="text-right">
                                <div className="text-sm font-bold text-gray-700 dark:text-gray-300">
                                  {confidencePercent}%
                                </div>
                              </div>
                              {/* Badge removed as requested */}
                            </div>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  {/* Objects List */}
                  {results.objects && results.objects.length > 0 && (
                    <div className="space-y-3">
                      <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2 uppercase tracking-wide">
                        <Tags className="h-4 w-4 text-gray-700 dark:text-gray-300" />
                        Detected Objects
                      </h4>
                      <div className="flex flex-wrap gap-2">
                        {results.objects.map((obj, idx) => (
                          <Badge
                            key={idx}
                            className="bg-gray-700 dark:bg-gray-300 text-white dark:text-black border border-gray-600 dark:border-gray-400 hover:bg-gray-600 dark:hover:bg-gray-200 capitalize"
                          >
                            {obj.name} {obj.score > 0 && `(${(obj.score * 100).toFixed(0)}%)`}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Right Column - Caption, Explanation, Narrative, Validation */}
                <div className="lg:col-span-1 space-y-4">
                  {/* Caption */}
                  <div className="space-y-2">
                    <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2 uppercase tracking-wide">
                      <ImageIcon className="h-4 w-4 text-black dark:text-white" />
                      Caption
                    </h4>
                    <p className="text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-900/20 px-4 py-3 rounded-lg text-sm leading-relaxed italic border border-gray-300 dark:border-gray-700">
                      "{results.caption}"
                    </p>
                  </div>

                  {/* LLM Explanation - Hidden */}
                  <div className="space-y-2 hidden">
                    <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2 uppercase tracking-wide">
                      LLM Reasoning
                    </h4>
                    <p className="text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-900/20 px-4 py-3 rounded-lg text-sm leading-relaxed border border-gray-300 dark:border-gray-700">
                      {results.explanation}
                    </p>
                  </div>

                  {/* Explanation */}
                  {results.explanation && (
                    <div className="space-y-2">
                      <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2 uppercase tracking-wide">
                        Explanation
                      </h4>
                      <p className="text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-900/20 px-4 py-3 rounded-lg text-sm leading-relaxed border border-gray-300 dark:border-gray-700">
                        {results.explanation}
                      </p>
                    </div>
                  )}

                  {/* Validation Scores - Hidden */}
                  {results.validation && (
                    <div className="space-y-3 hidden">
                      <h4 className="text-sm font-bold text-gray-900 dark:text-gray-100 flex items-center gap-2 uppercase tracking-wide">
                        <Sparkles className="h-4 w-4 text-gray-600 dark:text-gray-400" />
                        Validation
                      </h4>
                      <div className="grid grid-cols-2 gap-2">
                        <div className="bg-linear-to-br from-green-100 to-green-50 dark:from-green-900/30 dark:to-green-900/20 p-3 rounded-lg border border-green-300 dark:border-green-700">
                          <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Domain Match</p>
                          <p className="text-lg font-bold text-gray-700 dark:text-gray-300">
                            {(results.validation.domain_similarity * 100).toFixed(1)}%
                          </p>
                        </div>
                        <div className="bg-linear-to-br from-red-100 to-red-50 dark:from-red-900/30 dark:to-red-900/20 p-3 rounded-lg border border-red-300 dark:border-red-700">
                          <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">Caption Match</p>
                          <p className="text-lg font-bold text-gray-700 dark:text-gray-300">
                            {(results.validation.caption_similarity * 100).toFixed(1)}%
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}