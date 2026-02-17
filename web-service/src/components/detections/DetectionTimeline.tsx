import type { Detection } from "@/api/types"
import { Badge } from "@/components/ui/badge"
import { ConfidenceBadge } from "@/components/shared/ConfidenceBadge"
import { imageUrl } from "@/lib/images"

interface DetectionTimelineProps {
  detections: Detection[]
}

function groupByDate(detections: Detection[]): Map<string, Detection[]> {
  const groups = new Map<string, Detection[]>()
  for (const d of detections) {
    const date = new Date(d.timestamp).toLocaleDateString()
    const existing = groups.get(date)
    if (existing) {
      existing.push(d)
    } else {
      groups.set(date, [d])
    }
  }
  return groups
}

export function DetectionTimeline({ detections }: DetectionTimelineProps) {
  if (!detections.length) {
    return <p className="text-sm text-muted-foreground py-4">No detections recorded yet.</p>
  }

  const grouped = groupByDate(detections)

  return (
    <div className="space-y-6">
      {Array.from(grouped.entries()).map(([date, items]) => (
        <div key={date}>
          <h3 className="text-sm font-semibold text-muted-foreground mb-3">{date}</h3>
          <div className="space-y-3">
            {items.map((d) => (
              <div key={d.id} className="flex items-center gap-3 rounded-lg border p-3">
                <img
                  src={imageUrl(d.image_path)}
                  alt=""
                  className="h-12 w-12 rounded object-cover bg-muted shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary">{d.action}</Badge>
                    <ConfidenceBadge confidence={d.confidence} />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">
                    {new Date(d.timestamp).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}
