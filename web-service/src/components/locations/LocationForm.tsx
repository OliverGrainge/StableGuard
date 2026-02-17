import { useState } from "react"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { useCreateLocation } from "@/hooks/useLocations"

interface LocationFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function LocationForm({ open, onOpenChange }: LocationFormProps) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [error, setError] = useState<string | null>(null)
  const createMutation = useCreateLocation()

  const reset = () => {
    setName("")
    setDescription("")
    setError(null)
  }

  const handleSubmit = () => {
    if (!name.trim()) return
    setError(null)
    createMutation.mutate(
      { name: name.trim(), description: description.trim() || undefined },
      {
        onSuccess: () => {
          reset()
          onOpenChange(false)
        },
        onError: (err) => setError(err.message),
      }
    )
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) reset()
        onOpenChange(v)
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Add Location</DialogTitle>
          <DialogDescription>Add a camera location for monitoring.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="loc-name">Name</Label>
            <Input
              id="loc-name"
              placeholder="e.g. North Paddock"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="loc-desc">Description (optional)</Label>
            <Textarea
              id="loc-desc"
              placeholder="Camera placement details..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || createMutation.isPending}>
            {createMutation.isPending ? "Adding..." : "Add Location"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
