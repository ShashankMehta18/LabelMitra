import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import UploadBox from "../components/UploadBox";
import PhotoCard from "../components/PhotoCard";
import { sendScan } from "../services/api";

const WORKFLOW = [
  ["01", "Inspection", "Set inspection context"],
  ["02", "Evidence", "Capture package views"],
  ["03", "AI analysis", "Extract & verify"],
  ["04", "Report", "Review findings"],
];

const ANALYSIS_STAGES = [
  "Images uploaded",
  "Image quality checked",
  "Extracting label information",
  "Checking Legal Metrology requirements",
  "Preparing inspection result",
];

export default function Scan() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);

  const [stream, setStream] = useState(null);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [facing, setFacing] = useState("environment");
  const [photos, setPhotos] = useState([]);

  const [establishment, setEstablishment] = useState("");
  const [location, setLocation] = useState("");
  const [inspector, setInspector] = useState("");
  const [inspectionType, setInspectionType] = useState("Routine Inspection");

  const [busy, setBusy] = useState(false);
  const [analysisStage, setAnalysisStage] = useState(0);
  const [message, setMessage] = useState("");

  const addFiles = (files) => {
    const next = Array.from(files || []).map((file) => ({
      file,
      preview: file.type.startsWith("image/") ? URL.createObjectURL(file) : null,
      type: "Other",
    }));
    setPhotos((old) => [...old, ...next]);
    setMessage("");
  };

  const removePhoto = (index) => {
    setPhotos((old) => {
      const copy = [...old];
      if (copy[index]?.preview) URL.revokeObjectURL(copy[index].preview);
      copy.splice(index, 1);
      return copy;
    });
  };

  const changeType = (index, type) => {
    setPhotos((old) =>
      old.map((photo, i) => (i === index ? { ...photo, type } : photo))
    );
  };

  const startCamera = async () => {
    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera not supported");
      }

      stream?.getTracks().forEach((track) => track.stop());

      const newStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: facing } },
        audio: false,
      });

      setStream(newStream);
      setCameraOpen(true);
      setMessage("");
    } catch {
      setMessage(
        "Camera access could not be started. Please allow camera permission and use LabelMitra on localhost or HTTPS."
      );
    }
  };

  useEffect(() => {
    if (videoRef.current && stream) videoRef.current.srcObject = stream;
  }, [stream]);

  useEffect(() => {
    return () => stream?.getTracks().forEach((track) => track.stop());
  }, [stream]);

  const stopCamera = () => {
    stream?.getTracks().forEach((track) => track.stop());
    setStream(null);
    setCameraOpen(false);
  };

  const switchCamera = async () => {
    const nextFacing = facing === "environment" ? "user" : "environment";
    setFacing(nextFacing);

    stream?.getTracks().forEach((track) => track.stop());
    setStream(null);
    setCameraOpen(false);

    try {
      const newStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: nextFacing } },
        audio: false,
      });
      setStream(newStream);
      setCameraOpen(true);
    } catch {
      setMessage("Unable to switch camera.");
    }
  };

  const capture = () => {
    const video = videoRef.current;
    if (!video?.videoWidth) return;

    const canvas = canvasRef.current;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        if (!blob) return;

        const file = new File(
          [blob],
          `labelmitra-camera-${Date.now()}.jpg`,
          { type: "image/jpeg" }
        );

        setPhotos((old) => [
          ...old,
          {
            file,
            preview: URL.createObjectURL(blob),
            type: "Other",
          },
        ]);
      },
      "image/jpeg",
      0.92
    );
  };

  const detailsComplete = Boolean(
    establishment.trim() && location.trim() && inspector.trim()
  );

  const evidenceComplete = photos.length >= 2;
  const canAnalyze = detailsComplete && evidenceComplete;
  const readiness = Math.min(100, photos.length * 50);

  const openFilePicker = () => fileInputRef.current?.click();

  const submit = async () => {
    if (!canAnalyze || busy) return;

    setBusy(true);
    setAnalysisStage(0);
    setMessage("");

    const timer = window.setInterval(() => {
      setAnalysisStage((current) =>
        Math.min(current + 1, ANALYSIS_STAGES.length - 1)
      );
    }, 850);

    try {
      const response = await sendScan({
        establishment,
        location,
        inspector,
        inspectionType,
        photos,
      });

      window.clearInterval(timer);
      setAnalysisStage(ANALYSIS_STAGES.length - 1);

      sessionStorage.setItem("scanResult", JSON.stringify(response));

      window.setTimeout(() => navigate("/result"), 550);
    } catch (error) {
      window.clearInterval(timer);
      setBusy(false);
      setMessage(
        error?.message ||
          "LabelMitra could not connect to the inspection backend."
      );
    }
  };

  return (
    <div className="inspection-page">
      <div className="inspection-hero">
        <div>
          <div className="inspection-kicker">
            <span className="kicker-dot" />
            LABELMITRA / INSPECTION WORKSPACE
          </div>

          <h1>
            Turn package evidence into a <em>traceable inspection.</em>
          </h1>

          <p>
            Capture the commodity from the angles you need, label each piece
            of evidence, then send the complete case to the inspection service.
          </p>
        </div>

        <div className="hero-meta">
          <span>CASE STATUS</span>
          <strong>{busy ? "ANALYSING" : "DRAFT"}</strong>
          <small>New inspection</small>
        </div>
      </div>

      <div className="workflow">
        {WORKFLOW.map(([number, title, subtitle], index) => {
          const completed =
            index === 0
              ? detailsComplete
              : index === 1
              ? evidenceComplete
              : false;

          const active =
            index === 0
              ? !detailsComplete
              : index === 1
              ? detailsComplete && !evidenceComplete
              : canAnalyze && index === 2;

          return (
            <div className="workflow-group" key={number}>
              <div
                className={`workflow-step ${completed ? "complete" : ""} ${
                  active ? "active" : ""
                }`}
              >
                <div className="workflow-number">
                  {completed ? "✓" : number}
                </div>

                <div>
                  <strong>{title}</strong>
                  <span>{subtitle}</span>
                </div>
              </div>

              {index < WORKFLOW.length - 1 && (
                <div className={`workflow-line ${completed ? "filled" : ""}`} />
              )}
            </div>
          );
        })}
      </div>

      <section className="inspection-panel details-panel">
        <div className="panel-heading">
          <div className="panel-title">
            <span className="panel-index">01</span>

            <div>
              <h2>Inspection context</h2>
              <p>
                Give the case enough context to make the evidence traceable.
              </p>
            </div>
          </div>

          {detailsComplete && (
            <span className="completion-badge">✓ Ready</span>
          )}
        </div>

        <div className="inspection-form">
          <label>
            Establishment name
            <input
              value={establishment}
              onChange={(e) => setEstablishment(e.target.value)}
              placeholder="e.g. ABC General Store"
            />
          </label>

          <label>
            Inspection location
            <input
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="City, market or address"
            />
          </label>

          <label>
            Inspector name
            <input
              value={inspector}
              onChange={(e) => setInspector(e.target.value)}
              placeholder="Enter inspector name"
            />
          </label>

          <label>
            Inspection type
            <select
              value={inspectionType}
              onChange={(e) => setInspectionType(e.target.value)}
            >
              <option>Routine Inspection</option>
              <option>Complaint-based Inspection</option>
              <option>Market Surveillance</option>
              <option>Follow-up Inspection</option>
            </select>
          </label>
        </div>
      </section>

      <section className="inspection-panel evidence-panel">
        <div className="panel-heading">
          <div className="panel-title">
            <span className="panel-index">02</span>

            <div>
              <h2>Package evidence</h2>
              <p>
                Use as many photographs as necessary. More evidence can be
                added at any time.
              </p>
            </div>
          </div>

          <div className="evidence-counter">
            <strong>{String(photos.length).padStart(2, "0")}</strong>
            <span>evidence items</span>
          </div>
        </div>

        {!cameraOpen ? (
          <div className="capture-options">
            <button className="camera-card" onClick={startCamera}>
              <div className="capture-icon">
                <span>⌾</span>
              </div>

              <div>
                <strong>Capture with camera</strong>
                <span>Use a live camera for package evidence</span>
              </div>

              <b>↗</b>
            </button>

            <div className="capture-divider">
              <span>OR</span>
            </div>

            <div className="upload-shell">
              <UploadBox onFiles={addFiles} />
            </div>
          </div>
        ) : (
          <div className="camera-workspace">
            <div className="camera-preview">
              <video ref={videoRef} autoPlay playsInline />

              <div className="camera-overlay">
                <div className="camera-corner top-left" />
                <div className="camera-corner top-right" />
                <div className="camera-corner bottom-left" />
                <div className="camera-corner bottom-right" />
                <span>ALIGN PACKAGE WITHIN FRAME</span>
              </div>

              <span className="camera-live">
                <i /> LIVE CAMERA
              </span>
            </div>

            <div className="camera-toolbar">
              <button onClick={switchCamera}>↻ Switch camera</button>

              <button
                className="camera-shutter"
                onClick={capture}
                aria-label="Capture photo"
              >
                <span />
              </button>

              <button onClick={stopCamera}>Close camera</button>
            </div>
          </div>
        )}

        <canvas ref={canvasRef} hidden />

        {photos.length > 0 && (
          <div className="evidence-list">
            <div className="evidence-list-header">
              <div>
                <strong>Evidence library</strong>
                <span>
                  Assign a view to each image so the analysis has useful
                  context.
                </span>
              </div>

              <button className="add-evidence-btn" onClick={openFilePicker}>
                + Add more
              </button>
            </div>

            <div className="hidden-picker">
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".jpg,.jpeg,.png,.pdf,image/jpeg,image/png,application/pdf"
                onChange={(e) => {
                  addFiles(e.target.files);
                  e.target.value = "";
                }}
              />
            </div>

            <div className="photo-grid">
              {photos.map((photo, index) => (
                <PhotoCard
                  key={`${photo.file.name}-${index}`}
                  photo={photo}
                  index={index}
                  onType={changeType}
                  onRemove={removePhoto}
                />
              ))}
            </div>
          </div>
        )}

        <div className={`readiness ${evidenceComplete ? "ready" : ""}`}>
          <div className="readiness-copy">
            <div className="readiness-icon">
              {evidenceComplete ? "✓" : "!"}
            </div>

            <div>
              <strong>
                {evidenceComplete
                  ? "Evidence threshold reached"
                  : "Two evidence items recommended"}
              </strong>

              <span>
                {evidenceComplete
                  ? "Front and back views are recommended; add more views whenever the package requires them."
                  : "Add at least two pieces of evidence before starting the inspection analysis."}
              </span>
            </div>
          </div>

          <div className="readiness-progress">
            <div className="readiness-progress-top">
              <span>Evidence readiness</span>
              <strong>{readiness}%</strong>
            </div>

            <div className="readiness-track">
              <div style={{ width: `${readiness}%` }} />
            </div>
          </div>
        </div>

        {message && (
          <div className="inspection-error">
            <div>!</div>
            <span>
              <strong>Unable to continue</strong>
              {message}
            </span>
          </div>
        )}

        {busy ? (
          <div className="analysis-panel">
            <div className="analysis-header">
              <div className="analysis-orb">
                <span />
              </div>

              <div>
                <span className="analysis-eyebrow">LABELMITRA AI</span>
                <h3>Building your inspection result</h3>
                <p>Evidence is being processed in sequence.</p>
              </div>
            </div>

            <div className="analysis-stages">
              {ANALYSIS_STAGES.map((stage, index) => {
                const completed = index < analysisStage;
                const active = index === analysisStage;

                return (
                  <div
                    className={`analysis-stage ${
                      completed ? "completed" : ""
                    } ${active ? "active" : ""}`}
                    key={stage}
                  >
                    <div className="stage-marker">
                      {completed ? "✓" : active ? <span /> : index + 1}
                    </div>

                    <div className="stage-content">
                      <strong>{stage}</strong>
                      <small>
                        {completed
                          ? "Completed"
                          : active
                          ? "In progress"
                          : "Waiting"}
                      </small>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="analysis-progress">
              <div
                style={{
                  width: `${
                    ((analysisStage + 1) / ANALYSIS_STAGES.length) * 100
                  }%`,
                }}
              />
            </div>

            <div className="analysis-footer">
              <span>AI-assisted inspection pipeline</span>
              <strong>
                {Math.round(
                  ((analysisStage + 1) / ANALYSIS_STAGES.length) * 100
                )}
                %
              </strong>
            </div>
          </div>
        ) : (
          <div className="inspection-action">
            <div className="action-copy">
              <span className="action-eyebrow">FINAL CHECK</span>

              <strong>
                {canAnalyze
                  ? "Case is ready for analysis"
                  : "Complete the required evidence first"}
              </strong>

              <span>
                LabelMitra will send the inspection context and captured
                evidence to the inspection service.
              </span>
            </div>

            <button
              className="analyze-btn"
              disabled={!canAnalyze}
              onClick={submit}
            >
              <span>Start AI inspection</span>
              <b>→</b>
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
