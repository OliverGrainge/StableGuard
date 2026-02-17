import { useCallback, useState } from "react"
import { Upload } from "lucide-react"
import { cn } from "@/lib/utils"

interface ImageUploadProps {
  onFileSelect: (file: File) => void
  preview?: string | null
  className?: string
}

export function ImageUpload({ onFileSelect, preview, className }: ImageUploadProps) {
  const [dragOver, setDragOver] = useState(false)

  const handleFile = useCallback(
    (file: File) => {
      if (file.type.startsWith("image/")) {
        onFileSelect(file)
      }
    },
    [onFileSelect]
  )

  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-6 transition-colors cursor-pointer",
        dragOver ? "border-primary bg-primary/5" : "border-muted-foreground/25 hover:border-primary/50",
        className
      )}
      onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        const file = e.dataTransfer.files[0]
        if (file) handleFile(file)
      }}
      onClick={() => {
        const input = document.createElement("input")
        input.type = "file"
        input.accept = "image/*"
        input.onchange = () => {
          const file = input.files?.[0]
          if (file) handleFile(file)
        }
        input.click()
      }}
    >
      {preview ? (
        <img src={preview} alt="Preview" className="max-h-48 rounded-md object-contain" />
      ) : (
        <>
          <Upload className="h-8 w-8 text-muted-foreground mb-2" />
          <p className="text-sm text-muted-foreground">Drop an image here or click to browse</p>
        </>
      )}
    </div>
  )
}
