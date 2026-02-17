import { apiFetch } from "./client"
import type { Location } from "./types"

export function listLocations() {
  return apiFetch<Location[]>("/api/locations")
}

export function createLocation(data: { name: string; description?: string }) {
  return apiFetch<Location>("/api/locations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  })
}

export function deleteLocation(id: number) {
  return apiFetch<void>(`/api/locations/${id}`, { method: "DELETE" })
}
