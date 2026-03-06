import { useState, useCallback, useEffect } from "react";
import { Routes, Route } from "react-router-dom";
import { supabase } from "./lib/supabase";
import { countWords } from "./lib/wordCount";
import {
  PRICING,
  DELIVERY_TIERS,
  PARTIDA_PRICING,
  INCLUDES,
  getDeliveryHours,
  calcTotal,
} from "./constants";
import { Navbar } from "./components/Navbar";
import { Stepper } from "./components/Stepper";
import { BottomBar } from "./components/BottomBar";
import { StepUpload } from "./steps/StepUpload";
import { StepPlan } from "./steps/StepPlan";
import { StepDelivery } from "./steps/StepDelivery";
import { StepConfirm } from "./steps/StepConfirm";
import { StepDone } from "./steps/StepDone";
import { OrderStatus } from "./pages/OrderStatus";
import { FAQ } from "./pages/FAQ";
import { About } from "./pages/About";
import { Admin } from "./pages/Admin";

function Wizard() {
  const [step, setStep] = useState(0);
  const [file, setFile] = useState(null);
  const [drag, setDrag] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [dir, setDir] = useState("en-es");
  const [docType, setDocType] = useState("general");
  const [tier, setTier] = useState("standard");
  const [words, setWords] = useState(0);
  const [wordMethod, setWordMethod] = useState(null);
  const [express, setExpress] = useState(false);
  const [pages, setPages] = useState("");
  const [f, sf] = useState({
    name: "",
    email: "",
    phone: "",
    address: "",
    city: "",
    zip: "",
  });
  const [done, setDone] = useState(false);
  const [orderId, setOrderId] = useState(null);

  // Config from Supabase (loaded on mount, fallback to constants)
  const [config, setConfig] = useState(null);

  useEffect(() => {
    supabase
      .from("config")
      .select("key, value")
      .then(({ data }) => {
        if (data?.length) {
          const cfg = Object.fromEntries(data.map((r) => [r.key, r.value]));
          setConfig(cfg);
        }
      });
  }, []);

  // Resolved pricing values (config overrides constants)
  const pricePerWord = config?.price_per_word ?? PRICING.price_per_word;
  const pricePerWordExpress =
    config?.price_per_word_express ?? PRICING.price_per_word_express;
  const partidaPricing = config?.partida_pricing ?? PARTIDA_PRICING;
  const deliveryTiers = config?.delivery_tiers
    ? Object.values(config.delivery_tiers).map((t) => ({
        max_words: t.max_words ?? Infinity,
        hours: t.hours,
      }))
    : DELIVERY_TIERS;
  const includes = config?.includes ?? INCLUDES;

  // Calculate total
  const isPartida = docType === "partida_nacimiento";
  const total = isPartida
    ? partidaPricing[tier]?.price ?? 2500
    : calcTotal(words, express);
  const deliveryHours = isPartida
    ? partidaPricing[tier]?.hours ?? 24
    : express
      ? Math.max(0, getDeliveryHours(words, deliveryTiers) - 24)
      : getDeliveryHours(words, deliveryTiers);
  const rate = express ? pricePerWordExpress : pricePerWord;

  const doCountWords = useCallback(async (f, p = "") => {
    setAnalyzing(true);
    const result = await countWords(f, p);
    if (result) {
      setWords(result.words);
      setWordMethod(result.method);
    } else {
      setWords(0);
      setWordMethod(null);
    }
    setAnalyzing(false);
  }, []);

  const onFile = useCallback(
    (e) => {
      e.preventDefault();
      setDrag(false);
      const fi = e.dataTransfer?.files?.[0] || e.target?.files?.[0];
      if (fi) {
        setFile(fi);
        doCountWords(fi, pages);
      }
    },
    [doCountWords, pages]
  );

  // Re-count words when pages change (debounced)
  useEffect(() => {
    if (!file || !pages) {
      if (file && !pages && wordMethod) doCountWords(file, "");
      return;
    }
    const t = setTimeout(() => doCountWords(file, pages), 600);
    return () => clearTimeout(t);
  }, [pages]); // eslint-disable-line react-hooks/exhaustive-deps

  const up = (k, v) => sf((p) => ({ ...p, [k]: v }));

  const canNext = () => {
    if (step === 0) return !!file && !analyzing && (isPartida || words > 0);
    if (step === 1) return true;
    if (step === 2) return f.name && f.email && f.address && f.city;
    return true;
  };

  const handleReset = () => {
    setDone(false);
    setStep(0);
    setFile(null);
    setWords(0);
    setWordMethod(null);
    setExpress(false);
    setTier("standard");
    setDocType("general");
    setPages("");
    sf({ name: "", email: "", phone: "", address: "", city: "", zip: "" });
  };

  const handlePay = async () => {
    const {
      data: { user },
    } = await supabase.auth.getUser();
    const filePath = user
      ? `${user.id}/${crypto.randomUUID()}/input${file.name.substring(file.name.lastIndexOf("."))}`
      : null;

    if (filePath) {
      await supabase.storage.from("documents").upload(filePath, file);
    }

    const orderData = {
      user_id: user?.id || null,
      file_name: file.name,
      file_path: filePath || "",
      word_count: isPartida ? 0 : words,
      direction: dir,
      doc_type: docType,
      tier,
      price_per_word: isPartida ? null : rate,
      total_uyu: total,
      delivery_hours: deliveryHours,
      delivery_name: f.name,
      delivery_email: f.email,
      delivery_phone: f.phone || null,
      delivery_address: f.address,
      delivery_city: f.city,
      delivery_zip: f.zip || null,
      pages: pages || null,
      status: "pending_payment",
    };

    const { data: order, error } = await supabase
      .from("orders")
      .insert(orderData)
      .select("id")
      .single();

    if (error) {
      console.error("Error creating order:", error);
      setDone(true);
      return;
    }

    setOrderId(order.id);

    try {
      const { data: checkoutData, error: fnError } =
        await supabase.functions.invoke("create-checkout", {
          body: { order_id: order.id },
        });

      if (!fnError && checkoutData?.init_point) {
        window.location.href = checkoutData.init_point;
        return;
      }
    } catch {
      // Edge function not available yet
    }

    setDone(true);
  };

  if (done) {
    return (
      <StepDone
        file={file}
        dir={dir}
        words={words}
        docType={docType}
        tier={tier}
        deliveryHours={deliveryHours}
        f={f}
        total={total}
        orderId={orderId}
        onReset={handleReset}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white flex flex-col">
      <Navbar />
      <div
        className={`flex-1 mx-auto w-full px-5 md:px-8 ${step === 0 ? "max-w-5xl" : "max-w-2xl"}`}
      >
        {step > 0 && <Stepper step={step} />}
        <div className="pb-32">
          {step === 0 && (
            <StepUpload
              file={file}
              drag={drag}
              analyzing={analyzing}
              words={words}
              wordMethod={wordMethod}
              dir={dir}
              docType={docType}
              total={total}
              rate={rate}
              includes={includes}
              onFile={onFile}
              setDir={setDir}
              setDocType={setDocType}
              setDrag={setDrag}
              setWords={setWords}
              pages={pages}
              setPages={setPages}
            />
          )}
          {step === 1 && (
            <StepPlan
              docType={docType}
              tier={tier}
              setTier={setTier}
              express={express}
              setExpress={setExpress}
              words={words}
              total={total}
              deliveryHours={deliveryHours}
              rate={rate}
              pricePerWord={pricePerWord}
              pricePerWordExpress={pricePerWordExpress}
              partidaPricing={partidaPricing}
              deliveryTiers={deliveryTiers}
              file={file}
              dir={dir}
            />
          )}
          {step === 2 && (
            <StepDelivery
              f={f}
              up={up}
              words={words}
              docType={docType}
              tier={tier}
              deliveryHours={deliveryHours}
              total={total}
              dir={dir}
            />
          )}
          {step === 3 && (
            <StepConfirm
              file={file}
              dir={dir}
              words={words}
              docType={docType}
              tier={tier}
              deliveryHours={deliveryHours}
              f={f}
              total={total}
              rate={rate}
              onPay={handlePay}
            />
          )}
        </div>
      </div>
      <BottomBar
        step={step}
        canNext={canNext()}
        onBack={() => setStep(step - 1)}
        onNext={() => canNext() && setStep(step + 1)}
        total={total}
        file={file}
        analyzing={analyzing}
      />
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Wizard />} />
      <Route path="/order/:id" element={<OrderStatus />} />
      <Route path="/faq" element={<FAQ />} />
      <Route path="/about" element={<About />} />
      <Route path="/admin" element={<Admin />} />
    </Routes>
  );
}
