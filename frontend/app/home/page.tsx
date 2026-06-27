import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Upload, BarChart3, Zap, Target, Info } from "lucide-react"
import Link from "next/link"

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-10 space-y-12 max-w-7xl">
      {/* Hero Section */}
      <div className="text-center space-y-5">
        <div className="flex items-center justify-center gap-3">
          <h1 className="text-5xl font-bold text-black dark:text-white">
            Domain-Adaptive Zero-Shot Image Classification via CLIP and Large Language Models
          </h1>
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        <Card className="shadow-md hover:shadow-lg transition-all duration-300 border border-black dark:border-white bg-white dark:bg-black hover:border-gray-800 dark:hover:border-gray-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl text-black dark:text-white">
              <Upload className="h-6 w-6 text-black dark:text-white" />
              Upload & Classify
            </CardTitle>
            <CardDescription className="text-base text-gray-800 dark:text-gray-200">
              Upload images and get instant zero-shot classification results with domain-adaptive tuning
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-2 mb-6">
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-black dark:bg-white rounded-full"></span>
                CLIP-based visual embeddings
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-black dark:bg-white rounded-full"></span>
                Custom class labels
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-black dark:bg-white rounded-full"></span>
                Domain detection
              </li>
              <li className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-black dark:bg-white rounded-full"></span>
                Auto-tuned predictions
              </li>
            </ul>
            <Button asChild className="w-full rounded-lg shadow-sm hover:shadow-md transition-all bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-100">
              <Link href="/upload">
                Start Classifying
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="shadow-md hover:shadow-lg transition-all duration-300 border border-black dark:border-white bg-white dark:bg-black hover:border-gray-800 dark:hover:border-gray-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-xl text-black dark:text-white">
              LLM-Powered Explanations
            </CardTitle>
            <CardDescription className="text-base text-gray-800 dark:text-gray-200">
              Intelligent analysis with natural language reasoning and domain-aware insights
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ul className="text-sm text-gray-800 dark:text-gray-200 space-y-2 mb-6">
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 bg-black dark:bg-white rounded-full"></span>
                Automatic image captioning
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 bg-gray-600 dark:bg-gray-400 rounded-full"></span>
                Domain-specific model routing
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 bg-gray-600 dark:bg-gray-400 rounded-full"></span>
                Detailed reasoning explanations
              </li>
              <li className="flex items-center gap-2">
                <span className="w-2 h-2 bg-gray-600 dark:bg-gray-400 rounded-full"></span>
                Confidence and validation scores
              </li>
            </ul>
            <Button className="w-full rounded-lg bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-200" disabled>
              Adaptive & Contextual
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Key Features */}
      <Card className="shadow-md border border-black dark:border-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-black dark:text-white">
            <Zap className="h-5 w-5" />
            Key Features
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                <h3 className="font-semibold text-black dark:text-white">Hybrid Model Selection</h3>
              </div>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Intelligently routes to MedCLIP for medical images or ViT-H/14 for general domain classification
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Zap className="h-4 w-4" />
                <h3 className="font-semibold text-black dark:text-white">Automatic Domain Detection</h3>
              </div>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Detects image domain (medical, natural, etc.) and applies domain-specific model routing
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <h3 className="font-semibold text-black dark:text-white">Image Captioning</h3>
              </div>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                BLIP-based automatic caption generation for visual understanding and detailed descriptions
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                <h3 className="font-semibold text-black dark:text-white">LLM-Enhanced Reasoning</h3>
              </div>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                 generates detailed natural language explanations for predictions and reasoning chains
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Target className="h-4 w-4" />
                <h3 className="font-semibold text-black dark:text-white">Adaptive Score Tuning</h3>
              </div>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Auto-learns domain-specific confidence adjustments from feedback for improved accuracy over time
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Info className="h-4 w-4" />
                <h3 className="font-semibold text-black dark:text-white">Evaluation Metrics</h3>
              </div>
              <p className="text-sm text-gray-800 dark:text-gray-200">
                Comprehensive validation scores and performance metrics for benchmarking predictions
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Start */}
      <Card className="shadow-md border border-black dark:border-white">
        <CardHeader>
          <CardTitle className="text-black dark:text-white">Quick Start Guide</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-black dark:text-white mb-3">Step-by-Step Workflow:</h3>
              <ol className="list-decimal list-inside space-y-3 text-sm text-gray-800 dark:text-gray-200">
                <li><span className="font-medium">Upload Image</span> - Navigate to Upload & Classify and select your image (JPG, PNG, GIF)</li>
                <li><span className="font-medium">Optional Classes</span> -  use auto-detection for zero-shot classification</li>
                <li><span className="font-medium">Start Classification</span> - Click "Start Classification" to begin the adaptive pipeline</li>
                <li><span className="font-medium">Automatic Domain Detection</span> - System analyzes and detects the image domain (medical, natural, etc.)</li>
                <li><span className="font-medium">Model Routing</span> - Automatically selects MedCLIP for medical or ViT-H/14 for general domains</li>
                <li><span className="font-medium">Visual Analysis</span> - Generates image caption via BLIP and extracts visual embeddings via CLIP</li>
                <li><span className="font-medium">Predictions</span> - Gets top-K predictions with confidence scores and adaptive tuning</li>
                <li><span className="font-medium">LLM Reasoning</span> - generates detailed explanations for the predictions</li>
                <li><span className="font-medium">View Results</span> - See comprehensive results with validation metrics and domain insights</li>
              </ol>
            </div>

            {/* <div className="bg-gray-50 dark:bg-gray-900/30 p-4 rounded-lg border border-gray-300 dark:border-gray-700"> 
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <span className="font-semibold">💡 Tip:</span> The system works best with clear, well-lit images. Medical images will be processed with specialized models for higher accuracy.
              </p>
             </div> */}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
