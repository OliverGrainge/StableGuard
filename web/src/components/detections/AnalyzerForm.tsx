import { useState } from "react"
import { ScanSearch } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { ImageUpload } from "@/components/shared/ImageUpload"
import { useLocations } from "@/hooks/useLocations"
import { useAnalyze } from "@/hooks/useDetections"
import type { AnalyzeResponse } from "@/api/types"

interface AnalyzerFormProps {
  onResult: (result: AnalyzeResponse) => void
}

export function AnalyzerForm({ onResult }: AnalyzerFormProps) {
  const [locationId, setLocationId] = useState<string>("")
  const [image, setImage] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const { data: locations } = useLocations()
  const analyzeMutation = useAnalyze()

  const handleAnalyze = () => {
    if (!locationId || !image) return
    setError(null)
    analyzeMutation.mutate(
      { locationId: Number(locationId), image },
      {
        onSuccess: (result) => {
          onResult(result)
          setImage(null)
          setPreview(null)
        },
        onError: (err) => setError(err.message),
      }
    )
  }

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label>Location</Label>
        <Select value={locationId} onValueChange={setLocationId}>
          <SelectTrigger>
            <SelectValue placeholder="Select a location" />
          </SelectTrigger>
          <SelectContent>
            {locations?.map((loc) => (
              <SelectItem key={loc.id} value={String(loc.id)}>
                {loc.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <Label>Image</Label>
        <ImageUpload
          preview={preview}
          onFileSelect={(f) => {
            setImage(f)
            setPreview(URL.createObjectURL(f))
          }}
        />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      <Button
        className="w-full"
        onClick={handleAnalyze}
        disabled={!locationId || !image || analyzeMutation.isPending}
      >
        <ScanSearch className="h-4 w-4" />
        {analyzeMutation.isPending ? "Analyzing..." : "Analyze Image"}
      </Button>
    </div>
  )
}
