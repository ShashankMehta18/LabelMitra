import { useEffect, useRef, useState } from "react";

const stages = ["Images uploaded", "Image quality checked", "Reading nutrition & ingredients", "Analysing useful nutrients", "Checking potential concerns"];

export default function Quality() {
  const [files,setFiles]=useState([]); const [busy,setBusy]=useState(false); const [stage,setStage]=useState(-1);
  const [cameraOpen,setCameraOpen]=useState(false); const [cameraError,setCameraError]=useState("");
  const videoRef=useRef(null); const streamRef=useRef(null);
  useEffect(()=>()=>files.forEach(x=>x.preview&&URL.revokeObjectURL(x.preview)),[files]);
  const addFiles=list=>setFiles(old=>[...old,...Array.from(list||[]).filter(f=>f.type.startsWith("image/")).map(file=>({file,preview:URL.createObjectURL(file)}))]);
  const remove=i=>setFiles(old=>{const x=old[i]; if(x?.preview)URL.revokeObjectURL(x.preview); return old.filter((_,n)=>n!==i)});
  const openCamera=async()=>{
    setCameraError("");
    try{
      const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:{ideal:"environment"}},audio:false});
      streamRef.current=stream; setCameraOpen(true);
      requestAnimationFrame(()=>{if(videoRef.current){videoRef.current.srcObject=stream; videoRef.current.play().catch(()=>{});}});
    }catch(err){ setCameraError("Camera access was unavailable. Please allow camera permission or use the upload option."); }
  };
  const closeCamera=()=>{
    if(streamRef.current){streamRef.current.getTracks().forEach(t=>t.stop()); streamRef.current=null;}
    if(videoRef.current) videoRef.current.srcObject=null;
    setCameraOpen(false); setCameraError("");
  };
  useEffect(()=>()=>{if(streamRef.current)streamRef.current.getTracks().forEach(t=>t.stop());},[]);
  const capturePhoto=()=>{
    const video=videoRef.current; if(!video||!video.videoWidth)return;
    const canvas=document.createElement("canvas"); canvas.width=video.videoWidth; canvas.height=video.videoHeight;
    canvas.getContext("2d").drawImage(video,0,0,canvas.width,canvas.height);
    canvas.toBlob(blob=>{
      if(!blob)return;
      const file=new File([blob],`food-camera-${new Date().toISOString().replace(/[:.]/g,"-")}.jpg`,{type:"image/jpeg"});
      setFiles(old=>[...old,{file,preview:URL.createObjectURL(file)}]);
      closeCamera();
    },"image/jpeg",0.92);
  };
  const analyse=()=>{if(!files.length||busy)return; setBusy(true);setStage(0); let i=0; const timer=setInterval(()=>{i++;if(i>=stages.length){clearInterval(timer);setBusy(false);setStage(stages.length-1)}else setStage(i)},700)};
  return <div className="page food-page">
    <section className="food-hero">
      <div><div className="food-kicker">CONSUMER • AI FOOD INTELLIGENCE</div><h1>Know what you eat.<br/><em>Before you eat it.</em></h1><p>Turn a food label into a simple view of its nutrition, ingredients, useful nutrients and potential health concerns.</p><button className="food-primary" onClick={()=>document.getElementById("food-upload")?.scrollIntoView({behavior:"smooth"})}>Analyse a food product <b>→</b></button></div>
      <div className="food-profile"><span>FOOD PROFILE</span><strong>{files.length?"Ready to analyse":"Awaiting scan"}</strong><div><i>Nutrition</i><i>Ingredients</i><i>Concerns</i></div></div>
    </section>
    <div className="food-benefits"><div><b>○</b><strong>Nutrition</strong><span>See what the numbers actually mean.</span></div><div><b>⌁</b><strong>Ingredients</strong><span>Understand the listed ingredients.</span></div><div><b>!</b><strong>Health signals</strong><span>Spot potential nutritional concerns.</span></div><div><b>✦</b><strong>Better choice</strong><span>Get a simple label-based assessment.</span></div></div>
    <section className="food-card" id="food-upload"><div className="food-section-head"><div><span className="food-step">01</span><div><h2>Scan your food label</h2><p>Upload clear package photos so the system can read nutrition and ingredient information.</p></div></div><span className="food-count">{String(files.length).padStart(2,"0")} images</span></div>
      <div className="food-capture-row">
        <button type="button" className="food-camera-card" onClick={openCamera}>
          <span className="food-camera-icon">⌾</span><span><strong>Use live camera</strong><small>Capture the food label directly</small></span><b>↗</b>
        </button>
        <span className="food-or">OR</span>
        <label className="food-drop"><input type="file" accept="image/jpeg,image/png" multiple onChange={e=>addFiles(e.target.files)}/><span className="food-upload-icon">↑</span><strong>Drop your food label here</strong><span>or choose JPG / PNG images from your device</span></label>
      </div>
      {files.length>0&&<div className="food-preview-grid">{files.map((x,i)=><div className="food-preview" key={i}><img src={x.preview}/><button onClick={()=>remove(i)}>×</button><span>{x.file.name}</span></div>)}</div>}
      <div className="food-action"><div><strong>{files.length?`${files.length} image${files.length>1?"s":""} ready for analysis`:"Add at least one clear food-label image"}</strong><span>Results will be based on information visible in the uploaded label.</span></div><button className="food-analyse-btn" disabled={!files.length||busy} onClick={analyse}>{busy?"Analysing…":"Analyse with Food Intelligence →"}</button></div>
    </section>
    {cameraOpen&&<div className="camera-modal-backdrop" onClick={closeCamera}>
      <div className="camera-modal" onClick={e=>e.stopPropagation()}>
        <div className="camera-modal-head"><div><span>LIVE FOOD LABEL SCAN</span><h2>Capture food label</h2></div><button onClick={closeCamera} aria-label="Close">×</button></div>
        <div className="camera-frame"><video ref={videoRef} playsInline muted autoPlay/><div className="camera-guide"><span>Position the nutrition or ingredient panel inside the frame</span></div></div>
        {cameraError&&<p className="camera-error">{cameraError}</p>}
        <div className="camera-modal-actions"><button className="camera-cancel" onClick={closeCamera}>Cancel</button><button className="camera-capture" onClick={capturePhoto}>Capture photo <b>●</b></button></div>
      </div>
    </div>}
    {busy&&<section className="food-analysis"><div className="food-analysis-title"><span>AI FOOD ANALYSIS</span><h2>Reading your food label</h2><p>Preparing label-based insights. No health diagnosis is made from the scan.</p></div><div className="food-stages">{stages.map((s,i)=><div className={i<=stage?"done":""} key={s}><b>{i<stage?"✓":i===stage?"•":String(i+1).padStart(2,"0")}</b><span>{s}</span></div>)}</div></section>}
    <section className="food-card food-output"><div className="food-section-head"><div><span className="food-step">02</span><div><h2>What the analysis will show</h2><p>The backend can populate these sections after the food-analysis service is connected.</p></div></div></div><div className="food-output-grid"><article><span>01</span><strong>Nutrition snapshot</strong><p>Calories, protein, carbohydrates, fats, sugar, sodium and other declared values.</p></article><article><span>02</span><strong>Useful nutrients</strong><p>Identify vitamins, minerals, fibre, protein and other beneficial nutrients listed on the label.</p></article><article><span>03</span><strong>Potential concerns</strong><p>Flag label-based signals such as high sugar, sodium, saturated fat or relevant additives for review.</p></article><article><span>04</span><strong>Simple food assessment</strong><p>Summarise what the label suggests and what a consumer may want to check before choosing the product.</p></article></div></section>
  </div>;
}
