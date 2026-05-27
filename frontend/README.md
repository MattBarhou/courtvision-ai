# CourtVision AI Frontend

Next.js frontend for the CourtVision AI backend.

## Stack

- Next.js 16
- React 19
- Mantine

## Run locally

Start the backend first from `backend/`:

```powershell
uvicorn app.main:app --reload
```

Then start the frontend from `frontend/`:

```powershell
npm run dev
```

The UI uses `http://127.0.0.1:8000` by default for API requests. If you want a different backend URL, set:

```powershell
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## Features

- Single game winner predictions
- Season standings simulation
- Championship probability view
- Backend health visibility
