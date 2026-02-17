import { NavLink } from "react-router-dom"
import { LayoutDashboard, PawPrint, MapPin, ScanSearch, Shield } from "lucide-react"
import { cn } from "@/lib/utils"

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/horses", label: "Horses", icon: PawPrint },
  { to: "/locations", label: "Locations", icon: MapPin },
  { to: "/analyzer", label: "Analyzer", icon: ScanSearch },
]

export function Sidebar() {
  return (
    <aside className="hidden md:flex w-60 flex-col border-r bg-sidebar">
      <div className="flex items-center gap-2 px-6 py-5 border-b">
        <Shield className="h-6 w-6 text-primary" />
        <span className="font-bold text-lg">StableGuard</span>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
