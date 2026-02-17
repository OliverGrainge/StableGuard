import { BrowserRouter, Routes, Route } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { AppShell } from "@/components/layout/AppShell"
import { DashboardPage } from "@/pages/DashboardPage"
import { HorsesPage } from "@/pages/HorsesPage"
import { HorseDetailPage } from "@/pages/HorseDetailPage"
import { LocationsPage } from "@/pages/LocationsPage"
import { AnalyzerPage } from "@/pages/AnalyzerPage"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<DashboardPage />} />
            <Route path="horses" element={<HorsesPage />} />
            <Route path="horses/:id" element={<HorseDetailPage />} />
            <Route path="locations" element={<LocationsPage />} />
            <Route path="analyzer" element={<AnalyzerPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
