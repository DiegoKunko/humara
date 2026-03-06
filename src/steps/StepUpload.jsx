import { Icon } from "../components/Icon";
import { Spinner } from "../components/Spinner";

const STEPS = [
  { icon: "upload", label: "Subí", sub: "tu documento" },
  { icon: "zap", label: "Cotización", sub: "instantánea" },
  { icon: "cpu", label: "IA traduce", sub: "y verifica" },
  { icon: "pen", label: "Certificación", sub: "traductor público" },
  { icon: "truck", label: "Recibí", sub: "en tu domicilio" },
];

const DOC_TYPES = [
  { v: "general", l: "Documento general" },
  { v: "partida_nacimiento", l: "Partida de nacimiento" },
];

export const StepUpload = ({
  file,
  drag,
  analyzing,
  words,
  wordMethod,
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
}) => (
  <div className="pt-8 md:pt-12">
    {/* Main content */}
    <div className="md:grid md:grid-cols-2 md:gap-12 md:items-start">
      {/* Left: Hero */}
      <div>
        <h1 className="text-2xl md:text-[2.5rem] font-extrabold text-brand-900 tracking-tight leading-[1.1]">
          Traducciones con{" "}
          <span className="gradient-brand bg-clip-text text-transparent">
            agentes IA
          </span>{" "}
          certificadas por traductor público
        </h1>
        <p className="text-sm md:text-base text-slate-500 mt-3 leading-relaxed">
          Subí tu documento y recibilo certificado donde quieras.
          Desde $3 UYU por palabra.
        </p>

        {/* Includes list */}
        {includes && (
          <div className="mt-4">
            <p className="text-sm font-bold text-brand-900 mb-1.5">
              🤯 Todo incluido en el precio por palabra
            </p>
            <ul className="space-y-1">
              {includes.slice(1).map((item, i) => (
                <li
                  key={i}
                  className="flex items-center gap-2 text-xs text-slate-500"
                >
                  <Icon name="check" size={11} color="#22c55e" strokeWidth={3} />
                  {item}
                </li>
              ))}
            </ul>
          </div>
        )}

      </div>

      {/* Right: Dropzone + controls */}
      <div className="mt-6 md:mt-0 space-y-3">
        {/* Doc type — subtle toggle, not a CTA */}
        <div className="flex gap-1.5">
          {DOC_TYPES.map((o) => (
            <button
              key={o.v}
              onClick={() => setDocType(o.v)}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                docType === o.v
                  ? "bg-accent-50 text-accent-600 border border-accent-400 shadow-sm font-semibold"
                  : "bg-slate-50 text-slate-400 border border-transparent hover:bg-slate-100 hover:text-slate-500"
              }`}
            >
              {o.l}
            </button>
          ))}
        </div>

        {/* Dropzone — compact */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDrag(true);
          }}
          onDragLeave={() => setDrag(false)}
          onDrop={onFile}
          onClick={() => document.getElementById("fi").click()}
          className={`relative rounded-xl p-4 md:p-5 text-center cursor-pointer transition-all duration-300 border-2 group ${
            drag
              ? "border-brand-400 bg-brand-50 scale-[1.01]"
              : file
                ? "border-brand-200 bg-gradient-to-b from-brand-50/50 to-white shadow-sm"
                : "border-dashed border-slate-200 hover:border-brand-300 hover:bg-brand-50/30"
          }`}
        >
          <input
            id="fi"
            type="file"
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,.tiff"
            className="hidden"
            onChange={(e) =>
              onFile({ preventDefault: () => {}, target: e.target })
            }
          />
          {file ? (
            <div className="flex items-center gap-3 text-left">
              <div className="w-10 h-10 gradient-brand rounded-lg flex items-center justify-center flex-shrink-0 shadow-md shadow-brand-200">
                <Icon name="file" size={18} color="white" strokeWidth={2} />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-brand-900 text-sm truncate">
                  {file.name}
                </p>
                <div className="flex items-center gap-2 text-xs mt-0.5">
                  <span className="text-slate-400">
                    {(file.size / 1024).toFixed(0)} KB
                  </span>
                  {analyzing ? (
                    <Spinner />
                  ) : words > 0 ? (
                    <span className="text-brand-500 font-semibold">
                      {words.toLocaleString()} palabras
                      {wordMethod === "estimate" && " (est.)"}
                    </span>
                  ) : wordMethod === null ? (
                    <span className="text-amber-500">
                      Ingresá palabras
                    </span>
                  ) : null}
                </div>
              </div>
              <span className="text-[10px] text-slate-300">Cambiar</span>
            </div>
          ) : (
            <>
              <div className="w-10 h-10 bg-brand-50 rounded-lg flex items-center justify-center mx-auto mb-2 group-hover:bg-brand-100 transition-colors">
                <Icon name="upload" size={20} color="#3b82f6" />
              </div>
              <p className="font-semibold text-brand-900 text-sm">
                Subí tu documento
              </p>
              <p className="text-xs text-slate-400 mt-0.5">
                PDF, Word o imagen escaneada
              </p>
            </>
          )}
        </div>

        {/* Manual word input for images/unsupported */}
        {file && !analyzing && wordMethod === null && (
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500">Palabras:</label>
            <input
              type="number"
              min={1}
              value={words || ""}
              onChange={(e) => setWords(Number(e.target.value) || 0)}
              className="w-28 px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
              placeholder="Cantidad"
            />
          </div>
        )}

        {/* Pages to translate (optional) */}
        {file && !analyzing && (
          <div className="flex items-center gap-2">
            <label className="text-xs text-slate-500 whitespace-nowrap">Páginas:</label>
            <input
              type="text"
              value={pages}
              onChange={(e) => setPages(e.target.value)}
              className="flex-1 px-3 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-accent-400"
              placeholder="Traducir todo el documento"
            />
            {pages && (
              <span className="text-[10px] text-accent-600 whitespace-nowrap">
                Solo páginas indicadas
              </span>
            )}
          </div>
        )}

        {/* Direction — subtle, not competing with CTA */}
        <div className="flex gap-1.5">
          {[
            { v: "en-es", l: "Inglés → Español" },
            { v: "es-en", l: "Español → Inglés" },
          ].map((o) => (
            <button
              key={o.v}
              onClick={() => setDir(o.v)}
              className={`flex-1 py-2 px-3 rounded-lg text-xs font-medium transition-all flex items-center justify-center gap-1.5 ${
                dir === o.v
                  ? "bg-accent-50 text-accent-600 border border-accent-400 shadow-sm font-semibold"
                  : "bg-slate-50 text-slate-400 border border-transparent hover:bg-slate-100 hover:text-slate-500"
              }`}
            >
              <Icon
                name="globe"
                size={12}
                color={dir === o.v ? "#059669" : "#94a3b8"}
                strokeWidth={2}
              />
              {o.l}
            </button>
          ))}
        </div>

        {/* Live quote */}
        {file && !analyzing && (words > 0 || docType === "partida_nacimiento") && (
          <div className="surface-dark rounded-xl p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-brand-300">
                Cotización instantánea
              </span>
              {docType !== "partida_nacimiento" && (
                <span className="text-[10px] bg-white/10 px-2 py-0.5 rounded-full font-medium">
                  {words.toLocaleString()} pal × ${rate}
                </span>
              )}
            </div>
            <div className="flex items-end justify-between">
              <div>
                <p className="text-xl font-extrabold">
                  ${total.toLocaleString()} UYU
                </p>
                <p className="text-xs text-brand-300 mt-0.5">
                  {docType === "partida_nacimiento"
                    ? "Precio fijo partida"
                    : "Incluye todo"}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>

    {/* Process steps */}
    <div className="mt-8 md:mt-10">
      <div className="grid grid-cols-5 gap-2 md:gap-6 max-w-3xl mx-auto">
        {STEPS.map((s, i) => (
          <div key={i} className="flex flex-col items-center text-center">
            <div className="w-9 h-9 md:w-12 md:h-12 gradient-brand rounded-lg md:rounded-xl flex items-center justify-center shadow-md shadow-brand-200">
              <Icon name={s.icon} size={16} color="white" strokeWidth={2} />
            </div>
            <p className="text-[9px] md:text-xs font-bold text-brand-900 mt-1.5 leading-tight">
              {s.label}
            </p>
            <p className="text-[8px] md:text-[10px] text-slate-400 mt-0.5">
              {s.sub}
            </p>
          </div>
        ))}
      </div>
    </div>

    {/* Testimonial — below steps */}
    <div className="mt-6 max-w-lg mx-auto">
      <div className="bg-slate-50 rounded-xl px-5 py-4 flex items-start gap-3">
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-brand-400 to-brand-600 flex items-center justify-center flex-shrink-0 text-white font-bold text-xs">
          A
        </div>
        <div>
          <p className="text-xs text-slate-600 leading-relaxed italic">
            "Me voló la cabeza. Subí un contrato de 25 páginas al mediodía
            y al otro día llegué a la oficina y estaba arriba de mi escritorio."
          </p>
          <p className="mt-1.5 text-xs font-semibold text-brand-900">
            Agustín Pangallo
          </p>
        </div>
      </div>
    </div>
    {/* Especialidades */}
    <div className="mt-10 md:mt-12">
      <h2 className="text-lg md:text-xl font-extrabold text-brand-900 text-center mb-1">
        Especializaciones
      </h2>
      <p className="text-xs text-slate-400 text-center mb-5">
        Glosarios profesionales y reglas específicas por área
      </p>
      <div className="grid grid-cols-3 md:grid-cols-5 gap-3">
        {[
          { emoji: "⚖️", name: "Jurídico", desc: "Contratos, poderes, escrituras, sentencias" },
          { emoji: "📊", name: "Comercial", desc: "Balances, actas, informes, estatutos" },
          { emoji: "⚙️", name: "Técnico", desc: "Manuales, patentes, fichas técnicas" },
          { emoji: "👤", name: "Civil", desc: "Partidas, certificados, apostillas" },
          { emoji: "🏥", name: "Medicina", desc: "Historias clínicas, estudios, informes" },
        ].map((s, i) => (
          <div
            key={i}
            className="bg-white border border-slate-100 rounded-xl p-3 text-center shadow-sm hover:shadow-md transition-shadow"
          >
            <div className="text-2xl mb-1">{s.emoji}</div>
            <p className="text-xs font-bold text-brand-900">{s.name}</p>
            <p className="text-[10px] text-slate-400 mt-0.5 leading-tight">{s.desc}</p>
          </div>
        ))}
      </div>
    </div>
  </div>
);
