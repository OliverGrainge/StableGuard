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
import { ImageUpload } from "@/components/shared/ImageUpload"
import { useCreateHorse } from "@/hooks/useHorses"

interface HorseFormProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function HorseForm({ open, onOpenChange }: HorseFormProps) {
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [image, setImage] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const createMutation = useCreateHorse()

  const reset = () => {
    setName("")
    setDescription("")
    setImage(null)
    setPreview(null)
    setError(null)
  }

  const handleSubmit = () => {
    if (!name.trim() || !image) return
    setError(null)
    createMutation.mutate(
      { name: name.trim(), description: description.trim() || undefined, image },
      {
        onSuccess: () => {
          reset()
          onOpenChange(false)
        },
        onError: (err) => {
          setError(err.message)
        },
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
          <DialogTitle>Register Horse</DialogTitle>
          <DialogDescription>Add a new horse with a reference image for identification.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="horse-name">Name</Label>
            <Input
              id="horse-name"
              placeholder="e.g. Kenny"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="horse-desc">Description (optional)</Label>
            <Textarea
              id="horse-desc"
              placeholder="Markings, temperament, etc."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label>Reference Image</Label>
            <ImageUpload
              preview={preview}
              onFileSelect={(f) => {
                setImage(f)
                setPreview(URL.createObjectURL(f))
              }}
            />
          </div>

          {error && <p className="text-sm text-destructive">{error}</p>}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!name.trim() || !image || createMutation.isPending}>
            {createMutation.isPending ? "Registering..." : "Register"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
