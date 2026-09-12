const TYPES = [
  "Front", "Back", "Left Side", "Right Side", "Top", "Bottom",
  "Close-up / Label", "Barcode / QR", "Other"
];

export default function PhotoCard({ photo, index, onType, onRemove }) {
  return (
    <div className="photo-card">
      <button type="button" className="remove-btn" onClick={() => onRemove(index)} aria-label="Remove photo">×</button>
      {photo.preview ? (
        <img src={photo.preview} className="photo-preview" alt={`Product evidence ${index + 1}`} />
      ) : (
        <div className="pdf-preview"><span>PDF</span><small>Document</small></div>
      )}
      <div className="photo-info">
        <div className="photo-label"><strong>Evidence {index + 1}</strong><span>{photo.file.type === "application/pdf" ? "PDF" : "Image"}</span></div>
        <select value={photo.type} onChange={(e) => onType(index, e.target.value)}>
          {TYPES.map((type) => <option key={type}>{type}</option>)}
        </select>
        <small title={photo.file.name}>{photo.file.name}</small>
      </div>
    </div>
  );
}
