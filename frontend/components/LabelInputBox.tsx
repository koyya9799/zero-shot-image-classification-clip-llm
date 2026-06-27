"use client"

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Tags, Plus, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface LabelInputBoxProps {
  labels: string[]
  onLabelsChange: (labels: string[]) => void
  disabled?: boolean
  className?: string
  placeholder?: string
  maxLabels?: number
}

export default function LabelInputBox({
  labels,
  onLabelsChange,
  disabled = false,
  className,
  placeholder = "Enter class labels (e.g., dog, cat, bird)",
  maxLabels = 20
}: LabelInputBoxProps) {
  const [inputValue, setInputValue] = useState('')
  const [suggestions] = useState([
    'dog', 'cat', 'bird', 'car', 'tree', 'house', 'person', 'flower', 
    'computer', 'phone', 'book', 'chair', 'table', 'bicycle', 'airplane',
    'boat', 'horse', 'cow', 'sheep', 'elephant'
  ])

  const addLabel = (label: string) => {
    const trimmedLabel = label.trim().toLowerCase()
    if (trimmedLabel && !labels.includes(trimmedLabel) && labels.length < maxLabels) {
      onLabelsChange([...labels, trimmedLabel])
    }
    setInputValue('')
  }

  const removeLabel = (indexToRemove: number) => {
    onLabelsChange(labels.filter((_, index) => index !== indexToRemove))
  }

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addLabel(inputValue)
    } else if (e.key === 'Backspace' && inputValue === '' && labels.length > 0) {
      removeLabel(labels.length - 1)
    }
  }

  const handleSuggestionClick = (suggestion: string) => {
    addLabel(suggestion)
  }

  const availableSuggestions = suggestions.filter(
    suggestion => !labels.includes(suggestion) && 
    suggestion.toLowerCase().includes(inputValue.toLowerCase())
  ).slice(0, 8)

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Tags className="h-5 w-5" />
          Class Labels
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Label chips */}
        {labels.length > 0 && (
          <div className="flex flex-wrap gap-2">
            {labels.map((label, index) => (
              <div
                key={index}
                className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary rounded-md text-sm"
              >
                <span>{label}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-4 w-4 p-0 hover:bg-destructive hover:text-destructive-foreground"
                  onClick={() => removeLabel(index)}
                  disabled={disabled}
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        )}

        {/* Input */}
        <div className="space-y-2">
          <div className="flex gap-2">
            <Input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleInputKeyDown}
              placeholder={placeholder}
              disabled={disabled || labels.length >= maxLabels}
              className="flex-1"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={() => addLabel(inputValue)}
              disabled={disabled || !inputValue.trim() || labels.length >= maxLabels}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          
          {labels.length >= maxLabels && (
            <p className="text-xs text-muted-foreground">
              Maximum {maxLabels} labels reached
            </p>
          )}
        </div>

        {/* Suggestions */}
        {inputValue && availableSuggestions.length > 0 && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground font-medium">Suggestions:</p>
            <div className="flex flex-wrap gap-2">
              {availableSuggestions.map((suggestion) => (
                <Button
                  key={suggestion}
                  variant="outline"
                  size="sm"
                  className="text-xs"
                  onClick={() => handleSuggestionClick(suggestion)}
                  disabled={disabled}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Quick presets */}
        {labels.length === 0 && !inputValue && (
          <div className="space-y-2">
            <p className="text-xs text-muted-foreground font-medium">Quick presets:</p>
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => onLabelsChange(['dog', 'cat', 'bird', 'fish'])}
                disabled={disabled}
                className="text-xs justify-start"
              >
                Animals
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onLabelsChange(['car', 'truck', 'bicycle', 'motorcycle'])}
                disabled={disabled}
                className="text-xs justify-start"
              >
                Vehicles
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onLabelsChange(['tree', 'flower', 'grass', 'mountain'])}
                disabled={disabled}
                className="text-xs justify-start"
              >
                Nature
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => onLabelsChange(['house', 'building', 'bridge', 'castle'])}
                disabled={disabled}
                className="text-xs justify-start"
              >
                Architecture
              </Button>
            </div>
          </div>
        )}

        <p className="text-xs text-muted-foreground">
          Press Enter or comma to add labels. {labels.length}/{maxLabels} labels added.
        </p>
      </CardContent>
    </Card>
  )
}
