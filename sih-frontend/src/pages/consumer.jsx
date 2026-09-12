import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { sendConsumerScan } from "../services/api";

const stages = [
  "Image uploaded",
  "Checking image quality",
  "Reading ingredients & nutrition",
  "Analysing label information",
  "Preparing food insights",
];

export default function Consumer() {
  const navigate = useNavigate();

  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState("");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState(-1);
  const [error, setError] = useState("");

  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState("");

  const videoRef = useRef(null);
  const streamRef = useRef(null);

  useEffect(() => {
    return () => {
      if (preview) URL.revokeObjectURL(preview);

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, [preview]);

  function selectFile(selectedFile) {
    if (!selectedFile) return;

    const allowed = [
      "image/jpeg",
      "image/png",
      "image/webp",
    ];

    if (!allowed.includes(selectedFile.type)) {
      setError("Please upload a JPG, PNG or WEBP image.");
      return;
    }

    if (selectedFile.size > 10 * 1024 * 1024) {
      setError("Image must be smaller than 10 MB.");
      return;
    }

    if (preview) {
      URL.revokeObjectURL(preview);
    }

    setFile(selectedFile);
    setPreview(URL.createObjectURL(selectedFile));
    setError("");
    setStage(-1);
  }

  function handleFileChange(event) {
    selectFile(event.target.files?.[0]);
    event.target.value = "";
  }

  function handleDrop(event) {
    event.preventDefault();
    setDragging(false);
    selectFile(event.dataTransfer.files?.[0]);
  }

  async function openCamera() {
    setCameraError("");

    try {
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error("Camera is not supported.");
      }

      const stream =
        await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: {
              ideal: "environment",
            },
          },
          audio: false,
        });

      streamRef.current = stream;
      setCameraOpen(true);

      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => {});
        }
      }, 100);
    } catch {
      setCameraError(
        "Camera access unavailable. Allow camera permission or use upload."
      );
    }
  }

  function closeCamera() {
    if (streamRef.current) {
      streamRef.current
        .getTracks()
        .forEach((track) => track.stop());

      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setCameraOpen(false);
    setCameraError("");
  }

  function capturePhoto() {
    const video = videoRef.current;

    if (!video || !video.videoWidth) return;

    const canvas = document.createElement("canvas");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext("2d");

    context.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height
    );

    canvas.toBlob(
      (blob) => {
        if (!blob) return;

        const capturedFile = new File(
          [blob],
          `LabelMitra-${Date.now()}.jpg`,
          {
            type: "image/jpeg",
          }
        );

        selectFile(capturedFile);
        closeCamera();
      },
      "image/jpeg",
      0.92
    );
  }

  async function analyseProduct() {
    if (!file || loading) {
      setError("Please upload a product label first.");
      return;
    }

    setLoading(true);
    setError("");
    setStage(0);

    let currentStage = 0;

    const timer = setInterval(() => {
      currentStage += 1;

      setStage(
        Math.min(
          currentStage,
          stages.length - 1
        )
      );

      if (currentStage >= stages.length - 1) {
        clearInterval(timer);
      }
    }, 700);

    try {
      const result = await sendConsumerScan(file);

      clearInterval(timer);

      setStage(stages.length - 1);

      sessionStorage.setItem(
        "consumerResult",
        JSON.stringify(result)
      );

      sessionStorage.setItem(
        "consumerFileName",
        file.name
      );

      setTimeout(() => {
        navigate("/consumer/result");
      }, 400);
    } catch (err) {
      clearInterval(timer);

      setLoading(false);
      setStage(-1);

      setError(
        err?.message ||
          "LabelMitra could not connect to Consumer AI."
      );
    }
  }

  return (
    <div className="page food-page">

      {/* HERO */}
      <section className="food-hero">

        <div>
          <div className="food-kicker">
            CONSUMER • AI FOOD INTELLIGENCE
          </div>

          <h1>
            Know what you eat.
            <br />
            <em>Before you eat it.</em>
          </h1>

          <p>
            Turn a food label into a simple view of its
            nutrition, ingredients, potential concerns
            and useful alternatives.
          </p>

          <button
            className="food-primary"
            onClick={() =>
              document
                .getElementById("food-upload")
                ?.scrollIntoView({
                  behavior: "smooth",
                })
            }
          >
            Analyse a food product
            <b>→</b>
          </button>
        </div>

        <div className="food-profile">
          <span>FOOD PROFILE</span>

          <strong>
            {file
              ? "Ready to analyse"
              : "Awaiting scan"}
          </strong>

          <div>
            <i>Nutrition</i>
            <i>Ingredients</i>
            <i>Insights</i>
          </div>
        </div>

      </section>


      {/* BENEFITS */}
      <div className="food-benefits">

        <div>
          <b>○</b>
          <strong>Nutrition</strong>
          <span>
            See the nutrition values visible on the label.
          </span>
        </div>

        <div>
          <b>⌁</b>
          <strong>Ingredients</strong>
          <span>
            Extract the ingredients from the package.
          </span>
        </div>

        <div>
          <b>!</b>
          <strong>Health signals</strong>
          <span>
            Highlight factors worth paying attention to.
          </span>
        </div>

        <div>
          <b>✦</b>
          <strong>Better choice</strong>
          <span>
            Get a simple label-based assessment.
          </span>
        </div>

      </div>


      {/* UPLOAD */}
      <section
        className="food-card"
        id="food-upload"
      >

        <div className="food-section-head">

          <div>
            <span className="food-step">
              01
            </span>

            <div>
              <h2>
                Scan your food label
              </h2>

              <p>
                Upload a clear package photo so
                LabelMitra can read the visible
                nutrition and ingredient information.
              </p>
            </div>
          </div>

          <span className="food-count">
            {file ? "01 image" : "00 images"}
          </span>

        </div>


        {/* CAMERA + DROP */}
        <div className="food-capture-row">

          <button
            type="button"
            className="food-camera-card"
            onClick={openCamera}
            disabled={loading}
          >
            <span className="food-camera-icon">
              ⌾
            </span>

            <span>
              <strong>
                Use live camera
              </strong>

              <small>
                Capture the food label directly
              </small>
            </span>

            <b>↗</b>
          </button>


          <span className="food-or">
            OR
          </span>


          <label
            className={`food-drop ${
              dragging ? "dragging" : ""
            }`}
            onDragOver={(event) => {
              event.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() =>
              setDragging(false)
            }
            onDrop={handleDrop}
          >

            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={handleFileChange}
              disabled={loading}
            />

            <span className="food-upload-icon">
              ↑
            </span>

            <strong>
              Drop your food label here
            </strong>

            <span>
              or choose JPG / PNG / WEBP images
              from your device
            </span>

          </label>

        </div>


        {/* PREVIEW */}
        {file && preview && (
          <div className="food-preview-grid">

            <div className="food-preview">

              <img
                src={preview}
                alt="Selected food label"
              />

              {!loading && (
                <button
                  type="button"
                  onClick={() => {
                    if (preview) {
                      URL.revokeObjectURL(
                        preview
                      );
                    }

                    setFile(null);
                    setPreview("");
                    setError("");
                    setStage(-1);
                  }}
                >
                  ×
                </button>
              )}

              <span>
                {file.name}
              </span>

            </div>

          </div>
        )}


        {/* ERROR */}
        {error && (
          <div className="consumer-inline-error">
            ⚠ {error}
          </div>
        )}


        {/* ACTION */}
        <div className="food-action">

          <div>

            <strong>
              {file
                ? "1 image ready for analysis"
                : "Add a clear food-label image"}
            </strong>

            <span>
              Results are based only on information
              visible in the uploaded label.
            </span>

          </div>

          <button
            className="food-analyse-btn"
            disabled={!file || loading}
            onClick={analyseProduct}
          >
            {loading
              ? "Analysing…"
              : "Analyse with Food Intelligence →"}
          </button>

        </div>

      </section>


      {/* ANALYSIS PROGRESS */}
      {loading && (
        <section className="food-analysis">

          <div className="food-analysis-title">

            <span>
              LABELMITRA AI ANALYSIS
            </span>

            <h2>
              Reading your food label
            </h2>

            <p>
              Extracting information from the visible
              product label.
            </p>

          </div>


          <div className="food-stages">

            {stages.map((item, index) => (

              <div
                key={item}
                className={
                  index <= stage
                    ? "done"
                    : ""
                }
              >

                <b>
                  {index < stage
                    ? "✓"
                    : index === stage
                    ? "•"
                    : String(index + 1).padStart(
                        2,
                        "0"
                      )}
                </b>

                <span>
                  {item}
                </span>

              </div>

            ))}

          </div>

        </section>
      )}


      {/* WHAT WE SHOW */}
      <section className="food-card food-output">

        <div className="food-section-head">

          <div>

            <span className="food-step">
              02
            </span>

            <div>

              <h2>
                What the analysis will show
              </h2>

              <p>
                LabelMitra converts the visible
                food label into an explainable
                consumer profile.
              </p>

            </div>

          </div>

        </div>


        <div className="food-output-grid">

          <article>

            <span>01</span>

            <strong>
              Nutrition snapshot
            </strong>

            <p>
              Calories, protein, carbohydrates,
              fats, sugar, fibre, sodium and
              other declared values.
            </p>

          </article>


          <article>

            <span>02</span>

            <strong>
              Ingredients
            </strong>

            <p>
              Extract the ingredient list and
              display it in a cleaner format.
            </p>

          </article>


          <article>

            <span>03</span>

            <strong>
              Potential concerns
            </strong>

            <p>
              Highlight label-based factors
              consumers may want to pay attention to.
            </p>

          </article>


          <article>

            <span>04</span>

            <strong>
              Simple food assessment
            </strong>

            <p>
              Give a general label-based assessment
              with reasons and alternative choices.
            </p>

          </article>

        </div>

      </section>


      {/* CAMERA MODAL */}
      {cameraOpen && (

        <div
          className="camera-modal-backdrop"
          onClick={closeCamera}
        >

          <div
            className="camera-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <div className="camera-modal-head">

              <div>

                <span>
                  LIVE FOOD LABEL SCAN
                </span>

                <h2>
                  Capture food label
                </h2>

              </div>

              <button
                type="button"
                onClick={closeCamera}
              >
                ×
              </button>

            </div>


            <div className="camera-frame">

              <video
                ref={videoRef}
                playsInline
                muted
                autoPlay
              />

              <div className="camera-guide">

                <span>
                  Position the nutrition or
                  ingredient panel inside the frame
                </span>

              </div>

            </div>


            {cameraError && (
              <p className="camera-error">
                {cameraError}
              </p>
            )}


            <div className="camera-modal-actions">

              <button
                className="camera-cancel"
                onClick={closeCamera}
              >
                Cancel
              </button>

              <button
                className="camera-capture"
                onClick={capturePhoto}
              >
                Capture photo
                <b>●</b>
              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}