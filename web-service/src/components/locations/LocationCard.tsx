import { useState } from "react"
import { MapPin, Trash2 } from "lucide-react"
import type { Location } from "@/api/types"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ConfirmDialog } from "@/components/shared/ConfirmDialog"
import { useDeleteLocation } from "@/hooks/useLocations"

interface LocationCardProps {
  location: Location
}

export function LocationCard({ location }: LocationCardProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const deleteMutation = useDeleteLocation()

  return (
    <>
      <Card>
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <div className="rounded-lg bg-muted p-2">
                <MapPin className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <p className="font-semibold">{location.name}</p>
                {location.description && (
                  <p className="text-sm text-muted-foreground mt-1">{location.description}</p>
                )}
              </div>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0 text-muted-foreground hover:text-destructive"
              onClick={() => {
                setError(null)
                setConfirmOpen(true)
              }}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
          {error && <p className="text-sm text-destructive mt-2">{error}</p>}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title={`Delete ${location.name}?`}
        description="This location will be permanently removed. Locations with existing detections cannot be deleted."
        onConfirm={() => {
          deleteMutation.mutate(location.id, {
            onSuccess: () => setConfirmOpen(false),
            onError: (err) => {
              setConfirmOpen(false)
              setError(err.message)
            },
          })
        }}
        loading={deleteMutation.isPending}
      />
    </>
  )
}
