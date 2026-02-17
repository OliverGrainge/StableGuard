import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createLocation, deleteLocation, listLocations } from "@/api/locations"

export function useLocations() {
  return useQuery({ queryKey: ["locations"], queryFn: listLocations })
}

export function useCreateLocation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createLocation,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["locations"] }) },
  })
}

export function useDeleteLocation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteLocation,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["locations"] }) },
  })
}
