import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { createHorse, deleteHorse, getHorse, listHorses } from "@/api/horses"

export function useHorses() {
  return useQuery({ queryKey: ["horses"], queryFn: listHorses })
}

export function useHorse(id: number) {
  return useQuery({ queryKey: ["horses", id], queryFn: () => getHorse(id) })
}

export function useCreateHorse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: createHorse,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["horses"] }) },
  })
}

export function useDeleteHorse() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: deleteHorse,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["horses"] }) },
  })
}
