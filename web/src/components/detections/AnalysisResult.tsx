import { useState } from "react"
import { ChevronDown, ChevronUp } from "lucide-react"
import type { AnalyzeResponse } from "@/api/types"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ConfidenceBadge } from "@/components/shared/ConfidenceBadge"
import { imageUrl } from "@/lib/images"

interface AnalysisResultProps {
  result: AnalyzeResponse
}

export function AnalysisResult({ result }: AnalysisResultProps) {
  const [rawOpen, setRawOpen] = useState(false)

  const sortedScores = [...(result.horse_scores ?? [])].sort(
    (a, b) => b.probability - a.probability
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Analysis Result</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <img
          src={imageUrl(result.image_path)}
          alt="Analyzed"
          className="w-full max-h-64 object-contain rounded-lg bg-muted"
        />

        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-muted-foreground">Action</p>
            <Badge variant="secondary">{result.action}</Badge>
          </div>
          <div>
            <p className="text-muted-foreground">Confidence</p>
            <ConfidenceBadge confidence={result.confidence} />
          </div>
          <div>
            <p className="text-muted-foreground">Status</p>
            <Badge variant={result.kept ? "default" : "destructive"}>
              {result.kept ? "Kept" : "Discarded"}
            </Badge>
          </div>
        </div>

        {sortedScores.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium">Horse Identification</p>
            {sortedScores.map((score) => {
              const pct = Math.round(score.probability * 100)
              const isBest = score.horse_id === result.horse_id && result.horse_id !== null
              return (
                <div key={score.horse_name} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className={isBest ? "font-semibold" : ""}>
                      {score.horse_name}
                      {isBest && (
                        <Badge variant="default" className="ml-2 text-[10px] px-1.5 py-0">
                          Best match
                        </Badge>
                      )}
                    </span>
                    <span className="text-muted-foreground tabular-nums">{pct}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-muted overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${isBest ? "bg-primary" : "bg-muted-foreground/30"}`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {sortedScores.length === 0 && (
          <div className="text-sm">
            <p className="text-muted-foreground">Horse</p>
            <p className="font-semibold">{result.horse_name ?? "Unknown"}</p>
          </div>
        )}

        {result.raw_vlm_response && (
          <div>
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-between"
              onClick={() => setRawOpen(!rawOpen)}
            >
              Raw VLM Response
              {rawOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
            {rawOpen && (
              <pre className="mt-2 rounded-md bg-muted p-3 text-xs overflow-x-auto whitespace-pre-wrap">
                {result.raw_vlm_response}
              </pre>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
