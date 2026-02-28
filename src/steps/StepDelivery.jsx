import { Icon } from "../components/Icon";
import { Input } from "../components/Input";
import { PRICING } from "../constants";

export const StepDelivery = ({ f, up, pages, plan, total, dir }) => (
  <div className="space-y-5">
    <div>
      <h2 className="text-xl font-bold text-brand-900">Datos de entrega</h2>
      <p className="text-sm text-slate-400 mt-1">El documento certificado llega a esta dirección.</p>
    </div>
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3">
        <Input icon="user" label="Nombre" req placeholder="Juan Pérez" value={f.name} onChange={e => up("name", e.target.value)} />
        <Input icon="mail" label="Email" req type="email" placeholder="juan@email.com" value={f.email} onChange={e => up("email", e.target.value)} />
      </div>
      <Input icon="phone" label="Teléfono" type="tel" placeholder="+598 99 123 456" value={f.phone} onChange={e => up("phone", e.target.value)} />
      <Input icon="home" label="Dirección" req placeholder="Av. 18 de Julio 1234, Apto 501" value={f.address} onChange={e => up("address", e.target.value)} />
      <div className="grid grid-cols-2 gap-3">
        <Input icon="map" label="Ciudad" req placeholder="Montevideo" value={f.city} onChange={e => up("city", e.target.value)} />
        <Input icon="map" label="Código postal" placeholder="11200" value={f.zip} onChange={e => up("zip", e.target.value)} />
      </div>
    </div>
    {/* Mini summary */}
    <div className="bg-brand-50 rounded-xl p-4 flex items-center justify-between border border-brand-100">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 gradient-brand rounded-lg flex items-center justify-center shadow-sm shadow-brand-200">
          <Icon name="file" size={16} color="white" />
        </div>
        <div>
          <p className="text-sm font-semibold text-brand-900">{pages} pág · {PRICING[plan].name}</p>
          <p className="text-xs text-slate-400">{dir === "en-es" ? "Inglés → Español" : "Español → Inglés"}</p>
        </div>
      </div>
      <p className="text-lg font-extrabold text-brand-900">USD ${total}</p>
    </div>
  </div>
);
