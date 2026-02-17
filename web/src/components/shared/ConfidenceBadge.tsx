import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

interface ConfidenceBadgeProps {
  confidence: number
  className?: string
}

export function ConfidenceBadge({ confidence, className }: ConfidenceBadgeProps) {
  const pct = Math.round(confidence * 100)
  const color =
    confidence > 0.7
      ? "bg-green-100 text-green-800 border-green-200"
      : confidence >= 0.4
        ? "bg-yellow-100 text-yellow-800 border-yellow-200"
        : "bg-red-100 text-red-800 border-red-200"

  return (
    <Badge variant="outline" className={cn(color, className)}>
      {pct}%
    </Badge>
  )
}
