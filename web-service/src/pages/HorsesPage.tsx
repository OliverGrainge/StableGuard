import { useState } from "react"
import { Plus, PawPrint } from "lucide-react"
import { useHorses } from "@/hooks/useHorses"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/shared/EmptyState"
import { HorseCard } from "@/components/horses/HorseCard"
import { HorseForm } from "@/components/horses/HorseForm"

export function HorsesPage() {
  const [formOpen, setFormOpen] = useState(false)
  const { data: horses, isLoading } = useHorses()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Horses</h1>
        <Button onClick={() => setFormOpen(true)}>
          <Plus className="h-4 w-4" />
          Register Horse
        </Button>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-64 rounded-xl" />
          ))}
        </div>
      ) : !horses?.length ? (
        <EmptyState
          icon={PawPrint}
          title="No horses registered"
          description="Register your first horse to start monitoring."
        >
          <Button onClick={() => setFormOpen(true)}>
            <Plus className="h-4 w-4" />
            Register Horse
          </Button>
        </EmptyState>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {horses.map((horse) => (
            <HorseCard key={horse.id} horse={horse} />
          ))}
        </div>
      )}

      <HorseForm open={formOpen} onOpenChange={setFormOpen} />
    </div>
  )
}
