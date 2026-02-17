import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { analyzeDetection, listDetections, getTimeline } from "@/api/detections"

export function useDetections(params?: { horseId?: number; locationId?: number }) {
  return useQuery({
    queryKey: ["detections", params],
    queryFn: () => listDetections(params),
  })
}

export function useTimeline(horseId: number) {
  return useQuery({
    queryKey: ["timeline", horseId],
    queryFn: () => getTimeline(horseId),
  })
}

export function useAnalyze() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: analyzeDetection,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["detections"] })
      qc.invalidateQueries({ queryKey: ["horses"] })
    },
  })
}
