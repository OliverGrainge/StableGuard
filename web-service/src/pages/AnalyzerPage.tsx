import { useState } from "react"
import type { AnalyzeResponse } from "@/api/types"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AnalyzerForm } from "@/components/detections/AnalyzerForm"
import { AnalysisResult } from "@/components/detections/AnalysisResult"

export function AnalyzerPage() {
  const [result, setResult] = useState<AnalyzeResponse | null>(null)

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Image Analyzer</h1>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Upload & Analyze</CardTitle>
          </CardHeader>
          <CardContent>
            <AnalyzerForm onResult={setResult} />
          </CardContent>
        </Card>

        <div>
          {result ? (
            <AnalysisResult result={result} />
          ) : (
            <Card className="h-full flex items-center justify-center">
              <CardContent className="text-center py-12">
                <p className="text-muted-foreground">
                  Select a location, upload an image, and click Analyze to see results here.
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
