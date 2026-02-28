import { useState, useCallback } from "react";
import { PRICING } from "./constants";
import { Navbar } from "./components/Navbar";
import { Stepper } from "./components/Stepper";
import { BottomBar } from "./components/BottomBar";
import { StepUpload } from "./steps/StepUpload";
import { StepPlan } from "./steps/StepPlan";
import { StepDelivery } from "./steps/StepDelivery";
import { StepConfirm } from "./steps/StepConfirm";
import { StepDone } from "./steps/StepDone";

export default function App() {
  const [step, setStep] = useState(0);
  const [file, setFile] = useState(null);
  const [drag, setDrag] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [dir, setDir] = useState("en-es");
  const [plan, setPlan] = useState("standard");
  const [pages, setPages] = useState(1);
  const [f, sf] = useState({ name: "", email: "", phone: "", address: "", city: "", zip: "" });
  const [done, setDone] = useState(false);

  const countPages = useCallback(async (file) => {
    setAnalyzing(true);
    try {
      if (file.type === "application/pdf") {
        const buf = await file.arrayBuffer();
        const t = new TextDecoder("latin1").decode(new Uint8Array(buf));
        const m = t.match(/\/Type\s*\/Page[^s]/g);
        if (m?.length) { setPages(m.length); setAnalyzing(false); return; }
      }
      if (file.type.startsWith("image/")) { setPages(1); setAnalyzing(false); return; }
      setPages(Math.max(1, Math.ceil(file.size / (file.name.match(/\.docx?$/) ? 5000 : 3000))));
    } catch { setPages(Math.max(1, Math.ceil(file.size / 3000))); }
    setAnalyzing(false);
  }, []);

  const onFile = useCallback((e) => {
    e.preventDefault(); setDrag(false);
    const fi = e.dataTransfer?.files?.[0] || e.target?.files?.[0];
    if (fi) { setFile(fi); countPages(fi); }
  }, [countPages]);

  const total = (pages * PRICING[plan].price).toFixed(2);
  const up = (k, v) => sf(p => ({ ...p, [k]: v }));

  const canNext = () => {
    if (step === 0) return !!file && !analyzing;
    if (step === 1) return true;
    if (step === 2) return f.name && f.email && f.address && f.city;
    return true;
  };

  const handleReset = () => {
    setDone(false);
    setStep(0);
    setFile(null);
    sf({ name: "", email: "", phone: "", address: "", city: "", zip: "" });
  };

  if (done) {
    return <StepDone file={file} dir={dir} pages={pages} plan={plan} f={f} total={total} onReset={handleReset} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white flex flex-col">
      <Navbar />
      <div className={`flex-1 mx-auto w-full px-5 md:px-8 ${step === 0 ? "max-w-5xl" : "max-w-2xl"}`}>
        {step > 0 && <Stepper step={step} />}
        <div className="pb-32">
          {step === 0 && <StepUpload file={file} drag={drag} analyzing={analyzing} pages={pages} dir={dir} plan={plan} total={total} onFile={onFile} setDir={setDir} setPlan={setPlan} setDrag={setDrag} />}
          {step === 1 && <StepPlan plan={plan} setPlan={setPlan} pages={pages} total={total} file={file} dir={dir} />}
          {step === 2 && <StepDelivery f={f} up={up} pages={pages} plan={plan} total={total} dir={dir} />}
          {step === 3 && <StepConfirm file={file} dir={dir} pages={pages} plan={plan} f={f} total={total} onPay={() => setDone(true)} />}
        </div>
      </div>
      <BottomBar step={step} canNext={canNext()} onBack={() => setStep(step - 1)} onNext={() => canNext() && setStep(step + 1)} total={total} file={file} analyzing={analyzing} />
    </div>
  );
}
