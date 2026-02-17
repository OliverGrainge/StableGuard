import { useState } from "react"
import { Plus, MapPin } from "lucide-react"
import { useLocations } from "@/hooks/useLocations"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/shared/EmptyState"
import { LocationCard } from "@/components/locations/LocationCard"
import { LocationForm } from "@/components/locations/LocationForm"

export function LocationsPage() {
  const [formOpen, setFormOpen] = useState(false)
  const { data: locations, isLoading } = useLocations()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Locations</h1>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="h-4 w-4" />
          Add Location
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          {Array.from({ length: 2 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
      ) : !locations?.length ? (
        <EmptyState
          icon={MapPin}
          title="No locations added"
          description="Add a camera location to start monitoring."
        >
          <Button onClick={() => setFormOpen(true)}>
            <Plus className="h-4 w-4" />
            Add Location
          </Button>
        </EmptyState>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {locations.map((loc) => (
            <LocationCard key={loc.id} location={loc} />
          ))}
        </div>
      )}

      <LocationForm open={formOpen} onOpenChange={setFormOpen} />
    </div>
  )
}
