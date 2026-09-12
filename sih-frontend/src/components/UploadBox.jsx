import { useRef, useState } from "react";

const ACCEPT = ["image/jpeg", "image/png", "application/pdf"];
const MAX_MB = 20;

export default function UploadBox({ onFiles }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState("");

  const process = (fileList) => {
    const files = Array.from(fileList || []);
    const invalid = files.find((f) => !ACCEPT.includes(f.type) || f.size > MAX_MB * 1024 * 1024);
    if (invalid) {
      setError("Only JPG, JPEG, PNG or PDF files up to 20 MB each are allowed.");
      return;
    }
    setError("");
    onFiles(files);
  };

  return (
    <div
      className={`drop-zone ${dragging ? "dragging" : ""}`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); process(e.dataTransfer.files); }}
      onClick={() => inputRef.current?.click()}
    >
      <input ref={inputRef} hidden type="file" multiple accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
        onChange={(e) => { process(e.target.files); e.target.value = ""; }} />
      <div className="upload-icon">↑</div>
      <h3>Add product evidence</h3>
      <p>Drag & drop files here or <b>choose files</b></p>
      <small>JPG, JPEG, PNG or PDF • Max 20 MB per file • Add as many photos as needed</small>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
