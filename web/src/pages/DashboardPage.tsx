import { Link } from "react-router-dom"
import { PawPrint, MapPin, ScanSearch, Eye } from "lucide-react"
import { useHorses } from "@/hooks/useHorses"
import { useLocations } from "@/hooks/useLocations"
import { useDetections } from "@/hooks/useDetections"
import { StatCard } from "@/components/shared/StatCard"
import { ConfidenceBadge } from "@/components/shared/ConfidenceBadge"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { imageUrl } from "@/lib/images"

export function DashboardPage() {
  const horses = useHorses()
  const locations = useLocations()
  const detections = useDetections()

  const matched = detections.data?.filter((d) => d.horse_id !== null).length ?? 0

  if (horses.isLoading || locations.isLoading || detections.isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Link to="/horses">
          <StatCard title="Horses" value={horses.data?.length ?? 0} icon={PawPrint} />
        </Link>
        <Link to="/locations">
          <StatCard title="Locations" value={locations.data?.length ?? 0} icon={MapPin} />
        </Link>
        <StatCard title="Detections" value={detections.data?.length ?? 0} icon={ScanSearch} />
        <StatCard title="Matched" value={matched} icon={Eye} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          {!detections.data?.length ? (
            <p className="text-sm text-muted-foreground">No detections yet. Go to the Analyzer to get started.</p>
          ) : (
            <div className="space-y-3">
              {detections.data.slice(0, 10).map((d) => (
                <div key={d.id} className="flex items-center gap-3">
                  <img
                    src={imageUrl(d.image_path)}
                    alt=""
                    className="h-10 w-10 rounded object-cover bg-muted"
                  />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">
                      {d.horse_id ? (
                        <Link to={`/horses/${d.horse_id}`} className="hover:underline">
                          Detection #{d.id}
                          {d.horse_scores?.[0] && (
                            <span className="text-muted-foreground font-normal"> — {d.horse_scores.sort((a, b) => b.probability - a.probability)[0].horse_name}</span>
                          )}
                        </Link>
                      ) : (
                        `Detection #${d.id}`
                      )}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(d.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <Badge variant="secondary">{d.action}</Badge>
                  <ConfidenceBadge confidence={d.confidence} />
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
