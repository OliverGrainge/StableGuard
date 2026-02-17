import { useState } from "react"
import { Link } from "react-router-dom"
import { Trash2 } from "lucide-react"
import type { Horse } from "@/api/types"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ConfirmDialog } from "@/components/shared/ConfirmDialog"
import { useDeleteHorse } from "@/hooks/useHorses"
import { imageUrl } from "@/lib/images"

interface HorseCardProps {
  horse: Horse
}

export function HorseCard({ horse }: HorseCardProps) {
  const [confirmOpen, setConfirmOpen] = useState(false)
  const deleteMutation = useDeleteHorse()

  return (
    <>
      <Card className="overflow-hidden group">
        <Link to={`/horses/${horse.id}`}>
          <div className="aspect-[4/3] overflow-hidden bg-muted">
            <img
              src={imageUrl(horse.reference_image_path)}
              alt={horse.name}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
            />
          </div>
        </Link>
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="min-w-0">
              <Link to={`/horses/${horse.id}`} className="font-semibold hover:underline">
                {horse.name}
              </Link>
              {horse.description && (
                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{horse.description}</p>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0 text-muted-foreground hover:text-destructive"
              onClick={() => setConfirmOpen(true)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title={`Delete ${horse.name}?`}
        description="This will remove the horse and unlink all its detections. This action cannot be undone."
        onConfirm={() => {
          deleteMutation.mutate(horse.id, {
            onSuccess: () => setConfirmOpen(false),
          })
        }}
        loading={deleteMutation.isPending}
      />
    </>
  )
}
