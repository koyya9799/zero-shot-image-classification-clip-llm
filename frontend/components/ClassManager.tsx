'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Plus, Tag, Loader2, CheckCircle, XCircle, RefreshCw } from "lucide-react"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

const DOMAIN_OPTIONS = [
  { value: 'natural', label: 'Natural Photos', description: 'Realistic photographs' },
  { value: 'medical', label: 'Medical Images', description: 'X-rays, scans, etc.' },
  { value: 'anime', label: 'Anime/Cartoon', description: 'Anime or cartoon style' },
  { value: 'sketch', label: 'Sketches', description: 'Line art, drawings' },
  { value: 'satellite', label: 'Satellite/Aerial', description: 'Top-down imagery' },
  { value: 'unknown', label: 'Unknown', description: 'Auto-detect domain' },
]

export default function ClassManager() {
  const [classes, setClasses] = useState<string[]>([])
  const [newClass, setNewClass] = useState('')
  const [selectedDomain, setSelectedDomain] = useState('natural')
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingClasses, setIsLoadingClasses] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  const fetchClasses = async () => {
    setIsLoadingClasses(true)
    try {
      const response = await fetch(`${BACKEND_URL}/api/classes`)
      if (response.ok) {
        const data = await response.json()
        setClasses(data.classes || [])
      }
    } catch (error) {
      console.error('Failed to fetch classes:', error)
    } finally {
      setIsLoadingClasses(false)
    }
  }

  useEffect(() => {
    fetchClasses()
  }, [])

  const handleAddClass = async () => {
    if (!newClass.trim()) {
      setMessage({ type: 'error', text: 'Please enter a class name' })
      return
    }

    setIsLoading(true)
    setMessage(null)

    try {
      const formData = new FormData()
      formData.append('label', newClass.trim())
      formData.append('domain', selectedDomain)

      const response = await fetch(`${BACKEND_URL}/api/add-class`, {
        method: 'POST',
        body: formData,
      })

      if (response.ok) {
        const data = await response.json()
        setMessage({ type: 'success', text: `Added "${newClass}" successfully!` })
        setNewClass('')
        await fetchClasses()
      } else {
        const error = await response.json()
        setMessage({ type: 'error', text: error.error || 'Failed to add class' })
      }
    } catch (error) {
      console.error('Error adding class:', error)
      setMessage({ type: 'error', text: 'Failed to add class. Is the backend running?' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !isLoading) {
      handleAddClass()
    }
  }

  return (
    <Card className="shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Tag className="h-5 w-5 text-purple-600 dark:text-purple-400" />
          Class Manager
        </CardTitle>
        <CardDescription>
          Add classes for zero-shot classification
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Classes */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label className="text-sm font-medium">
              Current Classes ({classes.length})
            </Label>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchClasses}
              disabled={isLoadingClasses}
            >
              <RefreshCw className={`h-4 w-4 ${isLoadingClasses ? 'animate-spin' : ''}`} />
            </Button>
          </div>
          <div className="flex flex-wrap gap-2 p-3 bg-blue-50 dark:bg-blue-950/30 rounded-lg min-h-15">
            {isLoadingClasses ? (
              <div className="w-full flex items-center justify-center py-4">
                <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
              </div>
            ) : classes.length === 0 ? (
              <p className="text-sm text-gray-400 w-full text-center py-2">
                No classes added yet. Add your first class below!
              </p>
            ) : (
              classes.map((cls) => (
                <Badge key={cls} variant="secondary" className="px-3 py-1">
                  {cls}
                </Badge>
              ))
            )}
          </div>
        </div>

        {/* Add New Class */}
        <div className="space-y-3">
          <Label htmlFor="newClass">Add New Class</Label>
          <div className="flex gap-2">
            <Input
              id="newClass"
              placeholder="e.g., cat, dog, car..."
              value={newClass}
              onChange={(e) => setNewClass(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="flex-1"
            />
          </div>

          {/* Domain Selection */}
          <div>
            <Label className="text-sm mb-2 block">Domain</Label>
            <div className="grid grid-cols-2 gap-2">
              {DOMAIN_OPTIONS.map((domain) => (
                <button
                  key={domain.value}
                  onClick={() => setSelectedDomain(domain.value)}
                  disabled={isLoading}
                  className={`p-3 text-left rounded-lg border transition-all ${
                    selectedDomain === domain.value
                      ? 'border-blue-500 dark:border-blue-400 bg-blue-100 dark:bg-blue-900/40'
                      : 'border-blue-200 dark:border-blue-800 hover:border-blue-400'
                  } ${isLoading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  <div className="font-medium text-sm">{domain.label}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400">
                    {domain.description}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <Button
            onClick={handleAddClass}
            disabled={isLoading || !newClass.trim()}
            className="w-full"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Adding...
              </>
            ) : (
              <>
                <Plus className="h-4 w-4 mr-2" />
                Add Class
              </>
            )}
          </Button>
        </div>

        {/* Message */}
        {message && (
          <div
            className={`flex items-center gap-2 p-3 rounded-lg ${
              message.type === 'success'
                ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300'
                : 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300'
            }`}
          >
            {message.type === 'success' ? (
              <CheckCircle className="h-4 w-4" />
            ) : (
              <XCircle className="h-4 w-4" />
            )}
            <p className="text-sm">{message.text}</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
