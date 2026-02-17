import { apiFetch } from "./client"
import type { Horse, HorseDetail } from "./types"

export function listHorses() {
  return apiFetch<Horse[]>("/api/horses")
}

export function getHorse(id: number) {
  return apiFetch<HorseDetail>(`/api/horses/${id}`)
}

export function createHorse(data: { name: string; description?: string; image: File }) {
  const form = new FormData()
  form.append("name", data.name)
  if (data.description) form.append("description", data.description)
  form.append("image", data.image)
  return apiFetch<Horse>("/api/horses", { method: "POST", body: form })
}

export function deleteHorse(id: number) {
  return apiFetch<void>(`/api/horses/${id}`, { method: "DELETE" })
}
