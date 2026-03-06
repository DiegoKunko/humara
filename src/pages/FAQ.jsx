import { useState } from "react";
import { Link } from "react-router-dom";
import { Navbar } from "../components/Navbar";
import { Icon } from "../components/Icon";

const FAQS = [
  {
    q: "¿Qué tipo de documentos traducen?",
    a: "Traducimos todo tipo de documentos: partidas de nacimiento, contratos, escrituras, certificados, diplomas, estados financieros, manuales técnicos, y más. Aceptamos PDF, Word e imágenes escaneadas.",
  },
  {
    q: "¿Cómo funciona la traducción con IA?",
    a: "Tu documento pasa por un pipeline de agentes IA especializados: primero se extrae el texto, luego se traduce con un modelo entrenado específicamente para traducción pública, y finalmente otro agente IA revisa la calidad. Todo es verificado y certificado por un traductor público matriculado.",
  },
  {
    q: "¿La traducción tiene validez legal?",
    a: "Sí. Todas las traducciones son certificadas por un traductor público matriculado, con firma, sello y timbre profesional. Tienen plena validez legal ante cualquier organismo público o privado.",
  },
  {
    q: "¿Cuánto tarda la entrega?",
    a: "Para documentos de hasta 15,000 palabras la entrega es en 24 horas. De 15,001 a 25,000 palabras en 48 horas. Más de 25,000 palabras en 72 horas. Las partidas de nacimiento tienen opción de entrega en el día.",
  },
  {
    q: "¿Cómo recibo el documento?",
    a: "Recibís el documento certificado en formato digital por email, y la copia física con timbres y sellos se entrega a domicilio dentro de Montevideo y Ciudad de la Costa. El envío está incluido en el precio.",
  },
  {
    q: "¿Qué incluye el precio?",
    a: "El precio incluye: timbres profesionales, doble verificación por agentes IA, certificación por traductor público, entrega a domicilio, y archivo digital.",
  },
  {
    q: "¿Qué métodos de pago aceptan?",
    a: "Aceptamos tarjetas de crédito y débito, MercadoPago, transferencia bancaria, Abitab y RedPagos.",
  },
  {
    q: "¿Puedo pedir una traducción urgente?",
    a: "Sí. Para documentos generales podés adelantar 24 horas pagando la tarifa express ($4.2 UYU/palabra). Para partidas de nacimiento ofrecemos entrega en el día.",
  },
];

export function FAQ() {
  const [open, setOpen] = useState(null);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <Navbar />
      <div className="max-w-2xl mx-auto px-5 py-12">
        <h1 className="text-2xl font-bold text-brand-900 text-center">
          Preguntas frecuentes
        </h1>
        <p className="text-sm text-slate-500 text-center mt-2 mb-10">
          Todo lo que necesitas saber sobre nuestro servicio
        </p>

        <div className="space-y-3">
          {FAQS.map((faq, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-slate-100 shadow-sm overflow-hidden"
            >
              <button
                onClick={() => setOpen(open === i ? null : i)}
                className="w-full flex items-center justify-between px-5 py-4 text-left"
              >
                <span className="text-sm font-semibold text-brand-900 pr-4">
                  {faq.q}
                </span>
                <Icon
                  name={open === i ? "x" : "arrow"}
                  size={14}
                  color="#94a3b8"
                />
              </button>
              {open === i && (
                <div className="px-5 pb-4">
                  <p className="text-sm text-slate-500 leading-relaxed">
                    {faq.a}
                  </p>
                </div>
              )}
            </div>
          ))}
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
