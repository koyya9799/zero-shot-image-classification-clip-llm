'use client'

import { Card, CardContent } from "@/components/ui/card"
import { CheckCircle2, Loader2, XCircle, Circle } from "lucide-react"
import { cn } from "@/lib/utils"

export type StepStatus = 'pending' | 'in-progress' | 'completed' | 'error'

export interface ProcessStep {
  id: string
  label: string
  description?: string
  status: StepStatus
  errorMessage?: string
}

interface ClassificationProgressProps {
  steps: ProcessStep[]
  currentStepIndex: number
  transactionId?: string
}

export default function ClassificationProgress({ 
  steps, 
  currentStepIndex,
  transactionId 
}: ClassificationProgressProps) {
  const completedSteps = steps.filter(s => s.status === 'completed').length
  const totalSteps = steps.length

  return (
    <Card className="h-3/4 shadow-lg border border-blue-300 dark:border-blue-700 bg-linear-to-br from-blue-50/50 to-purple-50/50 dark:from-blue-950/20 dark:to-purple-950/20">
      <CardContent className="pt-4 pb-4 px-6">
        <div className="space-y-3">
          {/* Header with overall progress */}
          <div className="text-center space-y-1">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              Processing Classification
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              {completedSteps} of {totalSteps} Steps Completed
            </p>
            {transactionId && (
              <p className="text-xs text-gray-500 dark:text-gray-500 font-mono">
                Session ID: {transactionId}
              </p>
            )}
          </div>

          {/* Progress Steps */}
          <div className="relative">
            {/* Progress Line */}
            <div className="absolute top-6 left-0 right-0 h-1 bg-blue-200 dark:bg-blue-900/50 mx-12">
              <div 
                className="h-full bg-linear-to-r from-blue-500 to-purple-500 transition-all duration-500 ease-out"
                style={{ 
                  width: `${totalSteps > 1 ? (completedSteps / (totalSteps - 1)) * 100 : 0}%` 
                }}
              />
            </div>

            {/* Steps */}
            <div className="relative grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
              {steps.map((step, index) => (
                <div key={step.id} className="flex flex-col items-center text-center">
                  {/* Step Icon */}
                  <div className={cn(
                    "relative z-10 w-12 h-12 rounded-full flex items-center justify-center border transition-all duration-300 shadow-lg",
                    step.status === 'completed' && "bg-black border-black dark:bg-white dark:border-white",
                    step.status === 'in-progress' && "bg-gray-600 border-gray-600 animate-pulse dark:bg-gray-400 dark:border-gray-400",
                    step.status === 'error' && "bg-black border-black dark:bg-white dark:border-white",
                    step.status === 'pending' && "bg-gray-300 dark:bg-gray-700 border-gray-300 dark:border-gray-700"
                  )}>
                    {step.status === 'completed' && (
                      <CheckCircle2 className="w-7 h-7 text-white" />
                    )}
                    {step.status === 'in-progress' && (
                      <Loader2 className="w-7 h-7 text-white animate-spin" />
                    )}
                    {step.status === 'error' && (
                      <XCircle className="w-7 h-7 text-white" />
                    )}
                    {step.status === 'pending' && (
                      <Circle className="w-7 h-7 text-gray-500 dark:text-gray-400" />
                    )}
                  </div>

                  {/* Step Label */}
                  <div className="mt-2 space-y-1">
                    <h3 className={cn(
                      "font-semibold text-sm",
                      step.status === 'completed' && "text-green-600 dark:text-green-400",
                      step.status === 'in-progress' && "text-blue-600 dark:text-blue-400",
                      step.status === 'error' && "text-red-600 dark:text-red-400",
                      step.status === 'pending' && "text-gray-500 dark:text-gray-400"
                    )}>
                      {step.label}
                    </h3>
                    {step.status === 'error' && step.errorMessage && (
                      <p className="text-xs text-red-600 dark:text-red-400 font-medium">
                        {step.errorMessage}
                      </p>
                    )}
                  </div>

                  {/* Status Badge */}
                  <div className="mt-1">
                    {step.status === 'completed' && (
                      <span className="text-xs px-2 py-1 rounded-full bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 font-medium">
                        ✓ Complete
                      </span>
                    )}
                    {step.status === 'in-progress' && (
                      <span className="text-xs px-2 py-1 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 font-medium animate-pulse">
                        ⟳ Processing...
                      </span>
                    )}
                    {step.status === 'error' && (
                      <span className="text-xs px-2 py-1 rounded-full bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 font-medium">
                        ✗ Failed
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </CardContent>
    </Card>
  )
}
