import { Icon } from "../components/Icon";
import { Spinner } from "../components/Spinner";
import { PRICING } from "../constants";

const STEPS = [
  { icon: "upload", label: "Subí", sub: "tu documento" },
  { icon: "zap", label: "Cotización", sub: "instantánea" },
  { icon: "cpu", label: "IA traduce", sub: "y verifica" },
  { icon: "pen", label: "Certificación", sub: "traductor público" },
  { icon: "truck", label: "Recibí", sub: "en tu domicilio" },
];

export const StepUpload = ({ file, drag, analyzing, pages, dir, plan, total, onFile, setDir, setPlan, setDrag }) => (
  <div className="pt-12 md:pt-20">
    {/* Two-column layout on desktop */}
    <div className="md:grid md:grid-cols-2 md:gap-16 md:items-center">

      {/* Left: Hero */}
      <div>
        <h1 className="text-2xl md:text-[2.75rem] font-extrabold text-brand-900 tracking-tight leading-[1.1]">
          Traducciones con <span className="gradient-brand bg-clip-text text-transparent">agentes IA</span> validadas y certificadas por traductor público
        </h1>
        <p className="text-sm md:text-base text-slate-500 mt-4 leading-relaxed">
          Subí tu documento y recibílo certificado donde quieras. Desde USD $2.50 por página.
        </p>
      </div>

      {/* Right: Dropzone + controls */}
      <div className="mt-8 md:mt-0 space-y-4">
        {/* Dropzone */}
        <div
          onDragOver={e => { e.preventDefault(); setDrag(true); }}
          onDragLeave={() => setDrag(false)}
          onDrop={onFile}
          onClick={() => document.getElementById("fi").click()}
          className={`relative rounded-2xl p-6 md:p-8 text-center cursor-pointer transition-all duration-300 border-2 group ${
            drag ? "border-brand-400 bg-brand-50 scale-[1.01]" :
            file ? "border-brand-200 bg-gradient-to-b from-brand-50/50 to-white shadow-sm" :
            "border-dashed border-slate-200 hover:border-brand-300 hover:bg-brand-50/30 hover:shadow-sm"
          }`}
        >
          <input id="fi" type="file" accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.tiff" className="hidden"
            onChange={e => onFile({ preventDefault: () => {}, target: e.target })} />
          {file ? (
            <>
              <div className="w-12 h-12 gradient-brand rounded-xl flex items-center justify-center mx-auto mb-3 shadow-lg shadow-brand-200">
                <Icon name="file" size={22} color="white" strokeWidth={2} />
              </div>
              <p className="font-semibold text-brand-900 text-sm">{file.name}</p>
              <div className="mt-1.5 flex items-center justify-center gap-3 text-sm">
                <span className="text-slate-400">{(file.size / 1024).toFixed(0)} KB</span>
                <span className="text-slate-200">|</span>
                {analyzing ? <Spinner /> : (
                  <span className="text-brand-500 font-semibold">{pages} {pages === 1 ? "página" : "páginas"}</span>
                )}
              </div>
              <p className="text-xs text-slate-300 mt-3">Tocá para cambiar</p>
            </>
          ) : (
            <>
              <div className="w-12 h-12 bg-brand-50 rounded-xl flex items-center justify-center mx-auto mb-3 group-hover:bg-brand-100 transition-colors">
                <Icon name="upload" size={22} color="#3b82f6" />
              </div>
              <p className="font-semibold text-brand-900 text-sm">Subí tu documento</p>
              <p className="text-xs text-slate-400 mt-1">PDF, Word o imagen escaneada</p>
            </>
          )}
        </div>

        {/* Direction */}
        <div className="flex gap-2">
          {[
            { v: "en-es", l: "Inglés → Español" },
            { v: "es-en", l: "Español → Inglés" },
          ].map(o => (
            <button key={o.v} onClick={() => setDir(o.v)}
              className={`flex-1 py-3 px-3 rounded-xl text-sm font-semibold transition-all flex items-center justify-center gap-2 ${
                dir === o.v
                  ? "btn-primary"
                  : "bg-white text-slate-500 border border-slate-200 hover:border-brand-300 hover:text-brand-600"
              }`}>
              <Icon name="globe" size={14} color={dir === o.v ? "white" : "#94a3b8"} strokeWidth={2} />
              {o.l}
            </button>
          ))}
        </div>

        {/* Live quote */}
        {file && !analyzing && (
          <div className="surface-dark">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-brand-300">Cotización instantánea</span>
              <span className="text-xs bg-white/10 px-2.5 py-1 rounded-full font-medium">{pages} pág × ${PRICING[plan].price}</span>
            </div>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-2xl font-extrabold">USD ${total}</p>
                <p className="text-sm text-brand-300 mt-0.5">Entrega en {PRICING[plan].hours}hs</p>
              </div>
              <div className="flex gap-1.5">
                {Object.entries(PRICING).map(([k, p]) => (
                  <button key={k} onClick={() => setPlan(k)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                      plan === k ? "bg-accent-500 text-white" : "bg-white/10 text-brand-200 hover:bg-white/20"
                    }`}>
                    {p.name}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>

    {/* Process steps — full width below */}
    <div className="mt-16 md:mt-20">
      <div className="grid grid-cols-5 gap-2 md:gap-6 max-w-3xl mx-auto">
        {STEPS.map((s, i) => (
          <div key={i} className="flex flex-col items-center text-center">
            <div className="w-11 h-11 md:w-14 md:h-14 gradient-brand rounded-xl md:rounded-2xl flex items-center justify-center shadow-lg shadow-brand-200">
              <Icon name={s.icon} size={20} color="white" strokeWidth={2} />
            </div>
            <p className="text-[10px] md:text-sm font-bold text-brand-900 mt-2.5 leading-tight">{s.label}</p>
            <p className="text-[9px] md:text-xs text-slate-400 mt-0.5">{s.sub}</p>
          </div>
        ))}
      </div>
    </div>

    {/* Testimonial */}
    <div className="mt-12 md:mt-16 max-w-2xl mx-auto">
      <div className="bg-white rounded-2xl border border-slate-100 shadow-sm px-6 py-5 md:px-8 md:py-6 flex items-start gap-4">
        <div className="w-11 h-11 md:w-12 md:h-12 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center flex-shrink-0 text-white font-bold text-lg">
          A
        </div>
        <div>
          <p className="text-sm md:text-base text-slate-700 leading-relaxed italic">
            "Me voló la cabeza. Subí un contrato de 15 páginas y en 24 horas tenía la traducción certificada en la puerta de mi casa."
          </p>
          <p className="mt-3 text-sm font-semibold text-brand-900">Agustín Pangallo</p>
        </div>
      </div>
    </div>
  </div>
);
