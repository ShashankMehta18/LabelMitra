# SIH Frontend — Day 1

React + Vite frontend for the Legal Metrology packaged-commodity inspection project.

## Day 1 coverage

- React/Vite application
- Routes/pages: Home, Scan, Result
- Product label upload: JPG/JPEG/PNG/PDF
- Multiple files
- Drag & drop
- File type and size validation (20 MB/file)
- Live camera capture
- 6 or more product photos in the UI
- Minimum 2 photos before submission
- User selects the type of every photo
- Loading and error states
- Basic result page placeholders
- Frontend API contract for `POST /scan`

## Run

```bash
npm install
npm run dev
```

Open the Vite URL, normally `http://localhost:5173`.

For camera access, allow browser camera permission. Camera works on localhost or HTTPS.

## Backend connection

Default backend:
`http://localhost:8000`

You can change it with:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

The frontend sends:

- `establishment_name`
- `location`
- `inspector_name`
- repeated `photos`
- repeated `photo_types`
- repeated `photo_indexes`

Endpoint:

`POST /scan`

See `src/types/api-contract.js` for the expected response contract.

## Team handoff

Frontend teammate owns the UI and sends the request.
Backend teammate owns OCR, extraction, Legal Metrology rules, violations, score and database.

Once the backend teammate gives the final endpoint/response JSON, update `src/services/api.js` and map the response fields in `src/pages/Result.jsx`.
