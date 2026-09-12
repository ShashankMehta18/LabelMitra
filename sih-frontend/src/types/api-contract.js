/*
FRONTEND <-> BACKEND DAY 1 CONTRACT

Request:
POST /scan
Content-Type: multipart/form-data

Fields:
- establishment_name: string
- location: string
- inspector_name: string
- photos: repeated file field (JPG/JPEG/PNG/PDF)
- photo_types: repeated string field
- photo_indexes: repeated string field

Expected success response (example shape):
{
  "inspection_id": "INS-001",
  "status": "success",
  "compliance_score": 82,
  "declarations": [
    {
      "field": "mrp",
      "value": "₹120",
      "status": "present",
      "confidence": 0.98,
      "evidence": {
        "photo_index": 1,
        "bbox": [120, 340, 280, 390]
      }
    }
  ],
  "violations": [
    {
      "field": "consumer_care",
      "status": "potential_non_compliance",
      "reason": "..."
    }
  ]
}

Error response:
{
  "detail": "Human-readable error message"
}

Loading states:
idle -> sending -> success OR error

NOTE:
The example response is only an API contract placeholder.
Backend should return the real computed values.
*/