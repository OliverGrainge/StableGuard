# StableGuard Web

React frontend for StableGuard — manage horses, locations, and analyze images via the backend API.

## Prerequisites

- **Node.js** (v18+)
- **Backend running** — the web app proxies `/api`, `/uploads`, and `/health` to `http://localhost:8000`. Start the backend first:

  ```bash
  cd ../api-service
  uv sync
  uv run uvicorn app.main:app --reload
  ```

## Quick Start

```bash
# Install dependencies
npm install

# Start the dev server (http://localhost:5173)
npm run dev
```

## Optional Python Environment (uv)

```bash
# Create/refresh the project virtual environment from pyproject.toml
uv sync

# Or sync directly from requirements.txt
uv pip sync requirements.txt --python .venv/bin/python --allow-empty-requirements
```

## Scripts

| Command     | Description                               |
|-------------|-------------------------------------------|
| `npm run dev`    | Start dev server with hot reload           |
| `npm run build`  | Production build (output in `dist/`)       |
| `npm run preview`| Serve the production build locally        |
| `npm run lint`   | Run ESLint                                |

## Tech Stack

- **React 19** + TypeScript
- **Vite** — dev server and build
- **Tailwind CSS v4**
- **shadcn/ui** (Radix primitives)
- **TanStack Query** — data fetching
- **React Router** — routing

## Project Structure

```
src/
├── api/          # API client and types
├── components/   # React components
├── hooks/        # React Query hooks
├── lib/          # Utilities
└── pages/        # Route pages
```
