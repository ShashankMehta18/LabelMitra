import { useEffect, useState } from "react";

const stages = [
  "Preparing inspection evidence",
  "Analyzing product declarations",
  "Checking compliance indicators",
  "Preparing inspection result"
];

export default function LoadingState() {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => setStage((current) => Math.min(current + 1, stages.length - 1)), 1400);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="loading-card" aria-live="polite">
      <div className="loading-head">
        <div className="spinner" />
        <div>
          <strong>{stages[stage]}</strong>
          <p>LabelMitra is processing the submitted evidence.</p>
        </div>
      </div>
      <div className="stage-dots">
        {stages.map((item, index) => <span key={item} className={index <= stage ? "done" : ""}></span>)}
      </div>
    </div>
  );
}
