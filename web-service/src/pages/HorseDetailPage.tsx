import { useParams, useNavigate } from "react-router-dom"
import { ArrowLeft, Calendar } from "lucide-react"
import { useHorse } from "@/hooks/useHorses"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Separator } from "@/components/ui/separator"
import { DetectionTimeline } from "@/components/detections/DetectionTimeline"
import { imageUrl } from "@/lib/images"

export function HorseDetailPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data, isLoading } = useHorse(Number(id))

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="flex gap-6">
          <Skeleton className="h-64 w-64 rounded-xl" />
          <div className="space-y-3 flex-1">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-4 w-full" />
          </div>
        </div>
      </div>
    )
  }

  if (!data) {
    return <p className="text-muted-foreground">Horse not found.</p>
  }

  const { horse, recent_detections } = data

  return (
    <div className="space-y-6">
      <Button variant="ghost" size="sm" onClick={() => navigate("/horses")}>
        <ArrowLeft className="h-4 w-4" />
        Back to Horses
      </Button>

      <div className="flex flex-col md:flex-row gap-6">
        <div className="shrink-0">
          <img
            src={imageUrl(horse.reference_image_path)}
            alt={horse.name}
            className="h-64 w-64 rounded-xl object-cover bg-muted"
          />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold">{horse.name}</h1>
          {horse.description && (
            <p className="text-muted-foreground">{horse.description}</p>
          )}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar className="h-4 w-4" />
            Registered {new Date(horse.created_at).toLocaleDateString()}
          </div>
        </div>
      </div>

      <Separator />

      <div>
        <h2 className="text-lg font-semibold mb-4">Detection Timeline</h2>
        <DetectionTimeline detections={recent_detections} />
      </div>
    </div>
  )
}
