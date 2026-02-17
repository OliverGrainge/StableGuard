/**
 * Convert a DB image path to a URL served by the backend's /uploads mount.
 * - New records store relative paths like "horses/abc.jpg" → "/uploads/horses/abc.jpg"
 * - Legacy absolute paths contain "uploads/" → strip prefix up to "uploads/"
 */
export function imageUrl(dbPath: string): string {
  if (!dbPath) return ""
  const idx = dbPath.indexOf("uploads/")
  if (idx !== -1) {
    return "/" + dbPath.slice(idx)
  }
  return `/uploads/${dbPath}`
}
