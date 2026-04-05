import { useEffect, useRef } from "react";
import { Icon } from "../components/Icon";

const DIR_LABELS = {
  "en-es": "Inglés → Español",
  "es-en": "Español → Inglés",
};

const AGENTS = [
  {
    icon: "scan",
    name: "Agente Extractor",
    desc: "Lee y analiza cada palabra, incluso documentos escaneados",
    color: "from-blue-500 to-blue-600",
    shadow: "shadow-blue-200",
  },
  {
    icon: "globe",
    name: "Agente Traductor",
    desc: "Traduce con glosarios especializados por área",
    color: "from-violet-500 to-violet-600",
    shadow: "shadow-violet-200",
  },
  {
    icon: "shield",
    name: "Agente Revisor",
    desc: "Verifica en 7 dimensiones: terminología, exactitud, estilo y más",
    color: "from-amber-500 to-amber-600",
    shadow: "shadow-amber-200",
  },
  {
    icon: "pen",
    name: "Traductor Público",
    desc: "Profesional matriculado certifica con firma, sello y timbre",
    color: "from-emerald-500 to-emerald-600",
    shadow: "shadow-emerald-200",
  },
];

const TESTIMONIALS = [
  { text: "Subí un contrato de 25 páginas al mediodía y al otro día estaba certificado arriba de mi escritorio.", name: "Agustín P.", role: "Comercio exterior", initials: "AP" },
  { text: "Necesitaba la partida de nacimiento traducida para la ciudadanía italiana. En 24 horas la tenía en casa.", name: "Lucía M.", role: "Trámite de ciudadanía", initials: "LM" },
  { text: "Tradujimos los estatutos de la sociedad para un inversor extranjero. Impecable y rápido.", name: "Martín R.", role: "Abogado, Estudio Rocha & Asoc.", initials: "MR" },
  { text: "Los balances auditados de la empresa traducidos con la terminología contable perfecta. Impresionante.", name: "Carolina S.", role: "Contadora, estudio contable", initials: "CS" },
  { text: "Apostillé un poder notarial y necesitaba la traducción urgente. Me salvaron el trámite.", name: "Federico B.", role: "Despachante de aduana", initials: "FB" },
  { text: "Necesitaba traducir un manual técnico de 80 páginas. Lo tuve en 48 horas, sin un solo error técnico.", name: "Gonzalo D.", role: "Ingeniero, planta industrial", initials: "GD" },
  { text: "Mis clientes del exterior necesitan contratos en español. Ahora les resuelvo en el día.", name: "Diego A.", role: "Inmobiliaria Punta del Este", initials: "DA" },
  { text: "Traduje la historia clínica completa de mi hijo para un tratamiento en el exterior. Todo perfecto.", name: "Valeria G.", role: "Particular", initials: "VG" },
  { text: "El seguimiento en tiempo real es genial. Ves cómo avanza tu traducción paso a paso.", name: "Sebastián L.", role: "Gerente de operaciones", initials: "SL" },
  { text: "Pasé de esperar 10 días a tener todo en 24 horas. No vuelvo al traductor de antes.", name: "Paula T.", role: "Asistente legal", initials: "PT" },
];

const PARTIDA_OPTIONS = [
  { v: "partida_nacimiento", l: "Nacimiento", icon: "user" },
  { v: "partida_matrimonio", l: "Matrimonio", icon: "file" },
  { v: "partida_defuncion", l: "Defunción", icon: "pen" },
];

/* Marquee – infinite horizontal scroll */
function TestimonialMarquee() {
  const trackRef = useRef(null);

  useEffect(() => {
    const track = trackRef.current;
    if (!track) return;
    let frame;
    let pos = 0;
    const speed = 0.4; // px per frame
    const step = () => {
      pos -= speed;
      // reset when first set scrolls out
      const half = track.scrollWidth / 2;
      if (Math.abs(pos) >= half) pos = 0;
      track.style.transform = `translateX(${pos}px)`;
      frame = requestAnimationFrame(step);
    };
    frame = requestAnimationFrame(step);
    return () => cancelAnimationFrame(frame);
  }, []);

  const cards = TESTIMONIALS.map((t, i) => (
    <div
      key={i}
      className="flex-shrink-0 w-72 bg-white rounded-2xl border border-slate-100 p-5 shadow-sm"
    >
      <p className="text-[13px] text-slate-600 leading-relaxed italic mb-3">
        "{t.text}"
      </p>
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center text-white text-[10px] font-bold flex-shrink-0">
          {t.initials}
        </div>
        <div>
          <p className="text-xs font-bold text-brand-900">{t.name}</p>
          <p className="text-[10px] text-slate-400">{t.role}</p>
        </div>
      </div>
    </div>
  ));

  return (
    <div className="overflow-hidden -mx-5 md:-mx-8">
      <div ref={trackRef} className="flex gap-4 will-change-transform" style={{ width: "max-content" }}>
        {cards}
        {/* duplicate for seamless loop */}
        {cards.map((c, i) => <div key={`dup-${i}`}>{c}</div>)}
      </div>
    </div>
  );
}

export const StepUpload = ({
  file,
  drag,
  analyzing,
  words,
  wordMethod,
  detectedPages,
  detectedNotes,
  dir,
  docType,
  total,
  rate,
  includes,
  onFile,
  setDir,
  setDocType,
  setDrag,
  setWords,
  pages,
  setPages,
}) => {
  const isPartida = docType.startsWith("partida_");

  return (
    <div className="pt-4 md:pt-8">

      {/* ── ABOVE THE FOLD: Hero + CTA ─────────────────────────── */}
      <div className="md:grid md:grid-cols-2 md:gap-10 md:items-center max-w-5xl mx-auto">

        {/* Left: copy */}
        <div className="text-center md:text-left">
          <div className="inline-flex items-center gap-1.5 bg-brand-900 text-white px-4 py-1.5 rounded-full mb-4 text-[10px] font-bold uppercase tracking-widest">
            <Icon name="zap" size={11} color="#fbbf24" strokeWidth={2.5} />
            Traducción Agéntica
          </div>
          <h1 className="text-[1.75rem] md:text-[2.8rem] font-extrabold text-brand-900 tracking-tight leading-[1.08]">
            Tu traducción certificada
            <br />
            <span className="gradient-brand bg-clip-text text-transparent">
              lista mañana
            </span>
          </h1>
          <p className="text-sm md:text-base text-slate-500 mt-3 leading-relaxed max-w-md mx-auto md:mx-0">
            Subí tu documento y recibilo con validez legal en tu domicilio.
            Sin ir a ningún lado. Sin esperar semanas.
          </p>

          {/* Trust row */}
          <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 mt-4">
            {[
              { icon: "shield", text: "Validez legal plena" },
              { icon: "zap", text: "Timbres incluidos" },
              { icon: "truck", text: "A domicilio gratis" },
            ].map((b, i) => (
              <div key={i} className="flex items-center gap-1.5 bg-accent-50 text-accent-600 px-2.5 py-1 rounded-full">
                <Icon name={b.icon} size={12} strokeWidth={2.2} />
                <span className="text-[11px] font-semibold">{b.text}</span>
              </div>
            ))}
          </div>

          {/* Price anchor */}
          <p className="mt-4 text-xs text-slate-400">
            Desde <span className="text-brand-900 font-extrabold text-sm">$3.5</span> UYU por palabra — todo incluido
          </p>
        </div>

        {/* Right: CTA card — dropzone */}
        <div className="mt-6 md:mt-0">
          <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xl shadow-slate-200/40 overflow-hidden">
            <div className="p-5">
              <div
                onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
                onDragLeave={() => setDrag(false)}
                onDrop={onFile}
                onClick={() => document.getElementById("fi").click()}
                className={`relative rounded-xl p-5 md:p-6 text-center cursor-pointer transition-all duration-300 border-2 group ${
                  drag
                    ? "border-brand-400 bg-brand-50 scale-[1.01]"
                    : file
                      ? "border-accent-300 bg-accent-50/30"
                      : "border-dashed border-slate-200 hover:border-brand-300 hover:bg-brand-50/20"
                }`}
              >
                <input
                  id="fi"
                  type="file"
                  accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.tiff"
                  className="hidden"
                  onChange={(e) => onFile({ preventDefault: () => {}, target: e.target })}
                />

                {file && !analyzing && words > 0 ? (
                  <div className="text-left">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-5 h-5 rounded-full bg-accent-500 flex items-center justify-center">
                        <Icon name="check" size={12} color="white" strokeWidth={3} />
                      </div>
                      <span className="text-xs font-bold text-accent-700 uppercase tracking-wider">Documento analizado</span>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-3">
                        <Icon name="file" size={15} color="#64748b" strokeWidth={1.8} />
                        <span className="text-sm font-semibold text-brand-900 truncate">{file.name}</span>
                        <span className="text-[10px] text-slate-300 ml-auto flex-shrink-0 hover:text-slate-500">Cambiar</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <Icon name="globe" size={15} color="#2563eb" strokeWidth={1.8} />
                        <span className="text-sm text-slate-600">{DIR_LABELS[dir]}</span>
                        <button onClick={(e) => { e.stopPropagation(); setDir(dir === "en-es" ? "es-en" : "en-es"); }} className="text-[10px] text-brand-500 font-semibold hover:text-brand-700 ml-1">Cambiar</button>
                      </div>
                      <div className="flex items-center gap-3">
                        <Icon name="layers" size={15} color="#64748b" strokeWidth={1.8} />
                        <span className="text-sm text-slate-600">
                          {words.toLocaleString()} palabras{detectedPages && ` · ${detectedPages} páginas`}
                          {wordMethod === "ocr" && <span className="text-[10px] text-brand-400 ml-1">(OCR)</span>}
                        </span>
                      </div>
                      {detectedNotes && (
                        <div className="flex items-start gap-3">
                          <Icon name="info" size={15} color="#94a3b8" strokeWidth={1.8} />
                          <span className="text-[11px] text-slate-400 leading-relaxed">{detectedNotes}</span>
                        </div>
                      )}
                    </div>
                  </div>
                ) : file && analyzing ? (
                  <div className="py-1">
                    <div className="flex items-center justify-center gap-3">
                      <div className="w-10 h-10 rounded-xl gradient-brand flex items-center justify-center animate-pulse">
                        <Icon name="scan" size={20} color="white" strokeWidth={2} />
                      </div>
                      <div className="text-left">
                        <p className="text-sm font-bold text-brand-900">Agente analizando...</p>
                        <p className="text-xs text-slate-400">Contando palabras y detectando idioma</p>
                      </div>
                    </div>
                  </div>
                ) : file && wordMethod === null ? (
                  <div className="flex items-center gap-3 text-left">
                    <div className="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center flex-shrink-0">
                      <Icon name="file" size={20} color="#f59e0b" strokeWidth={2} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-bold text-brand-900 text-sm truncate">{file.name}</p>
                      <p className="text-xs text-amber-500 mt-0.5">Ingresá la cantidad de palabras</p>
                    </div>
                    <span className="text-[10px] text-slate-300">Cambiar</span>
                  </div>
                ) : (
                  <>
                    <div className="w-14 h-14 gradient-brand rounded-2xl flex items-center justify-center mx-auto mb-3 shadow-lg shadow-brand-200 group-hover:scale-105 transition-transform">
                      <Icon name="upload" size={26} color="white" strokeWidth={2} />
                    </div>
                    <p className="font-bold text-brand-900 text-base">Subí tu documento</p>
                    <p className="text-xs text-slate-400 mt-1">PDF, Word o imagen escaneada</p>
                  </>
                )}
              </div>

              {file && !analyzing && wordMethod === null && (
                <div className="flex items-center gap-2 mt-3">
                  <label className="text-xs text-slate-500">Palabras:</label>
                  <input type="number" min={1} value={words || ""} onChange={(e) => setWords(Number(e.target.value) || 0)} className="w-28 px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" placeholder="Cantidad" />
                </div>
              )}
              {file && !analyzing && (
                <div className="flex items-center gap-2 mt-3">
                  <label className="text-xs text-slate-500 whitespace-nowrap">Páginas:</label>
                  <input type="text" value={pages} onChange={(e) => setPages(e.target.value)} className="flex-1 px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" placeholder="Todas (o ej: 1-5, 10-15)" />
                </div>
              )}
            </div>

            {/* Quote bar */}
            {file && !analyzing && words > 0 && !isPartida && (
              <div className="bg-gradient-to-r from-brand-900 to-brand-700 px-5 py-4 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-[10px] font-semibold text-brand-300 uppercase tracking-widest mb-0.5">Cotización</p>
                    <p className="text-2xl font-extrabold tracking-tight">${total.toLocaleString()} <span className="text-sm font-bold text-brand-300">UYU</span></p>
                  </div>
                  <div className="text-right">
                    <p className="text-[11px] text-brand-300">{words.toLocaleString()} pal. × ${rate}</p>
                    <p className="text-[11px] font-bold text-white">Todo incluido</p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* spacer */}
          <div className="mt-1" />
        </div>
      </div>

      {/* Includes — single line */}
      {includes && (
        <div className="mt-6 flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
          {includes.slice(1).map((item, i) => (
            <span key={i} className="flex items-center gap-1 text-[11px] text-slate-400">
              <Icon name="check" size={10} color="#22c55e" strokeWidth={3} />
              {item}
            </span>
          ))}
        </div>
      )}

      {/* ── TESTIMONIALS MARQUEE ─────────────────────────── */}
      <div className="mt-14 md:mt-20">
        <h2 className="text-center text-xs font-bold text-slate-300 uppercase tracking-widest mb-6">
          Clientes que confían en Humara
        </h2>
        <TestimonialMarquee />
      </div>

      {/* ── COMPARATIVA ─────────────────────────── */}
      <div className="mt-14 md:mt-20 max-w-xl mx-auto">
        <h2 className="text-center text-xs font-bold text-slate-300 uppercase tracking-widest mb-6">
          Humara vs. traductor tradicional
        </h2>
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
          <div className="grid grid-cols-3 text-center text-xs font-bold border-b border-slate-100">
            <div className="py-3 text-slate-400" />
            <div className="py-3 text-slate-400">Tradicional</div>
            <div className="py-3 text-brand-600 bg-brand-50/50">Humara</div>
          </div>
          {[
            ["Entrega", "5–10 días", "24 horas"],
            ["Precio / palabra", "$8\u201315", "$3.5"],
            ["Ir a oficina", "Sí", "100% online"],
            ["Timbres", "Aparte", "Incluidos"],
            ["Envío", "Retirás vos", "A domicilio"],
            ["Seguimiento", "Teléfono", "Tiempo real"],
          ].map(([label, trad, humara], i) => (
            <div key={i} className={`grid grid-cols-3 text-center ${i % 2 === 0 ? "bg-slate-50/50" : "bg-white"}`}>
              <div className="py-2.5 px-3 text-left text-[11px] text-slate-500 font-medium">{label}</div>
              <div className="py-2.5 text-slate-400 text-[11px]">{trad}</div>
              <div className="py-2.5 text-brand-900 font-bold text-[11px] bg-brand-50/30">{humara}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── AGENTS ─────────────────────────── */}
      <div className="mt-14 md:mt-20 max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h2 className="text-xs font-bold text-slate-300 uppercase tracking-widest mb-2">
            Sistema de Traducción Agéntica
          </h2>
          <p className="text-lg md:text-xl font-extrabold text-brand-900">
            4 agentes especializados en cada documento
          </p>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {AGENTS.map((a, i) => (
            <div key={i} className="relative">
              <div className="bg-white rounded-2xl border border-slate-100 p-4 text-center shadow-sm hover:shadow-lg transition-all hover:-translate-y-0.5">
                <div className={`w-11 h-11 rounded-xl bg-gradient-to-br ${a.color} flex items-center justify-center mx-auto mb-3 shadow-md ${a.shadow}`}>
                  <Icon name={a.icon} size={18} color="white" strokeWidth={2} />
                </div>
                <p className="text-xs font-extrabold text-brand-900 mb-1">{a.name}</p>
                <p className="text-[10px] text-slate-400 leading-relaxed">{a.desc}</p>
              </div>
              {i < 3 && (
                <div className="hidden md:block absolute top-1/2 -right-2.5 transform -translate-y-1/2 text-slate-200 z-10">
                  <Icon name="arrow" size={12} strokeWidth={2.5} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ── PARTIDAS — info, precio fijo ─────────────────────────── */}
      <div className="mt-14 md:mt-20 max-w-xl mx-auto">
        <div className="bg-gradient-to-br from-brand-50 to-white rounded-2xl border border-brand-100 p-6">
          <h3 className="text-base font-extrabold text-brand-900 text-center mb-1">
            Partidas y certificados civiles
          </h3>
          <p className="text-xs text-slate-400 text-center mb-4">
            Precio fijo, todo incluido. Subí tu partida arriba y te cotizamos al instante.
          </p>
          <div className="grid grid-cols-3 gap-3">
            {[
              { icon: "user", name: "Nacimiento", price: "Desde $2.000" },
              { icon: "file", name: "Matrimonio", price: "Desde $2.000" },
              { icon: "pen", name: "Defunción", price: "Desde $2.000" },
            ].map((o, i) => (
              <div key={i} className="bg-white rounded-xl border border-slate-100 p-3 text-center shadow-sm">
                <div className="w-8 h-8 rounded-lg bg-brand-50 flex items-center justify-center mx-auto mb-1.5">
                  <Icon name={o.icon} size={14} color="#2563eb" strokeWidth={1.8} />
                </div>
                <p className="text-xs font-bold text-brand-900">{o.name}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">{o.price}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── ESPECIALIDADES ─────────────────────────── */}
      <div className="mt-10 mb-8 max-w-2xl mx-auto">
        <h2 className="text-center text-xs font-bold text-slate-300 uppercase tracking-widest mb-6">
          Especializaciones
        </h2>
        <div className="grid grid-cols-5 gap-3">
          {[
            { icon: "shield", name: "Jurídico", desc: "Contratos, poderes" },
            { icon: "layers", name: "Comercial", desc: "Balances, actas" },
            { icon: "settings", name: "Técnico", desc: "Manuales, patentes" },
            { icon: "user", name: "Civil", desc: "Certificados" },
            { icon: "file", name: "Medicina", desc: "Historias clínicas" },
          ].map((s, i) => (
            <div key={i} className="bg-white border border-slate-100 rounded-xl p-3 text-center shadow-sm hover:shadow-md transition-shadow">
              <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center mx-auto mb-1.5">
                <Icon name={s.icon} size={15} color="#1e293b" strokeWidth={1.8} />
              </div>
              <p className="text-[11px] font-bold text-brand-900">{s.name}</p>
              <p className="text-[9px] text-slate-400 mt-0.5">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
