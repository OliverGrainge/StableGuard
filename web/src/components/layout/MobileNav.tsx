import { NavLink } from "react-router-dom"
import { LayoutDashboard, PawPrint, MapPin, ScanSearch, Shield } from "lucide-react"
import { cn } from "@/lib/utils"

const links = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard },
  { to: "/horses", label: "Horses", icon: PawPrint },
  { to: "/locations", label: "Locations", icon: MapPin },
  { to: "/analyzer", label: "Analyzer", icon: ScanSearch },
]

export function MobileNav() {
  return (
    <header className="md:hidden flex items-center justify-between border-b px-4 py-3">
      <div className="flex items-center gap-2">
        <Shield className="h-5 w-5 text-primary" />
        <span className="font-bold">StableGuard</span>
      </div>
      <nav className="flex gap-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "p-2 rounded-md",
                isActive ? "bg-accent" : "hover:bg-accent/50"
              )
            }
            title={label}
          >
            <Icon className="h-4 w-4" />
          </NavLink>
        ))}
      </nav>
    </header>
  )
}
