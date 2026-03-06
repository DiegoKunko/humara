import { Link } from "react-router-dom";
import { Navbar } from "../components/Navbar";
import { Icon } from "../components/Icon";

const STEPS = [
  {
    icon: "upload",
    title: "1. Subí tu documento",
    desc: "Cargá tu PDF, Word o imagen escaneada. Nuestro sistema detecta automáticamente la cantidad de palabras y te da una cotización instantánea.",
  },
  {
    icon: "cpu",
    title: "2. Agentes IA traducen",
    desc: "Tu documento pasa por un pipeline de agentes IA especializados. Un agente traduce y otro revisa la calidad, garantizando precisión y consistencia terminológica.",
  },
  {
    icon: "pen",
    title: "3. Certificación profesional",
    desc: "Un traductor público matriculado verifica la traducción, la certifica con firma, sello y timbre profesional. Validez legal plena.",
  },
  {
    icon: "truck",
    title: "4. Entrega a domicilio",
    desc: "Recibís el archivo digital por email inmediatamente y la copia física certificada con timbres se entrega en tu domicilio.",
  },
];

export function About() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <Navbar />
      <div className="max-w-3xl mx-auto px-5 py-12">
        <div className="text-center mb-12">
          <h1 className="text-2xl md:text-3xl font-bold text-brand-900">
            Cómo funciona Humara
          </h1>
          <p className="text-sm md:text-base text-slate-500 mt-3 max-w-lg mx-auto">
            Combinamos inteligencia artificial de última generación con
            certificación profesional para entregarte traducciones rápidas,
            precisas y con validez legal.
          </p>
        </div>

        <div className="space-y-6">
          {STEPS.map((s, i) => (
            <div
              key={i}
              className="flex gap-5 bg-white rounded-2xl border border-slate-100 shadow-sm p-6"
            >
              <div className="w-12 h-12 gradient-brand rounded-xl flex items-center justify-center flex-shrink-0 shadow-lg shadow-brand-200">
                <Icon name={s.icon} size={20} color="white" strokeWidth={2} />
              </div>
              <div>
                <h3 className="font-bold text-brand-900">{s.title}</h3>
                <p className="text-sm text-slate-500 mt-1 leading-relaxed">
                  {s.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Security section */}
        <div className="mt-16 text-center">
          <h2 className="text-xl font-bold text-brand-900 mb-6">
            Seguridad y confianza
          </h2>
          <div className="grid grid-cols-3 gap-4">
            {[
              { icon: "lock", label: "Conexión SSL", sub: "Datos encriptados" },
              { icon: "shield", label: "Certificado", sub: "Traductor público" },
              { icon: "file", label: "Privacidad", sub: "Docs protegidos" },
            ].map((s, i) => (
              <div
                key={i}
                className="bg-white rounded-xl border border-slate-100 shadow-sm p-4"
              >
                <div className="w-10 h-10 bg-accent-50 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Icon name={s.icon} size={18} color="#22c55e" />
                </div>
                <p className="text-xs font-bold text-brand-900">{s.label}</p>
                <p className="text-[10px] text-slate-400">{s.sub}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="text-center mt-12">
          <Link
            to="/"
            className="inline-flex items-center gap-2 px-6 py-3 btn-primary rounded-xl text-sm"
          >
            Pedir traducción
            <Icon name="arrow" size={14} color="white" strokeWidth={2.5} />
          </Link>
        </div>
      </div>
    </div>
  );
}
