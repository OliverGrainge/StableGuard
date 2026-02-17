import { apiFetch } from "./client"
import type { AnalyzeResponse, Detection } from "./types"

export function analyzeDetection(data: { locationId: number; image: File }) {
  const form = new FormData()
  form.append("image", data.image)
  return apiFetch<AnalyzeResponse>(
    `/api/detections/analyze?location_id=${data.locationId}`,
    { method: "POST", body: form }
  )
}

export function listDetections(params?: { horseId?: number; locationId?: number }) {
  const search = new URLSearchParams()
  if (params?.horseId) search.set("horse_id", String(params.horseId))
  if (params?.locationId) search.set("location_id", String(params.locationId))
  const qs = search.toString()
  return apiFetch<Detection[]>(`/api/detections${qs ? `?${qs}` : ""}`)
}

export function getTimeline(horseId: number) {
  return apiFetch<Detection[]>(`/api/detections/${horseId}/timeline`)
}
