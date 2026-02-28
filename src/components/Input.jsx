import { Icon } from "./Icon";

export const Input = ({ icon, label, req, ...props }) => (
  <div>
    <label className="flex items-center gap-1.5 text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wider">
      <Icon name={icon} size={13} color="#94a3b8" strokeWidth={2} />
      {label}
      {req && <span className="text-brand-500">*</span>}
    </label>
    <input
      {...props}
      className="w-full px-4 py-3.5 bg-white border border-slate-200 rounded-xl focus:border-brand-500 focus:ring-2 focus:ring-brand-100 outline-none transition-all text-sm text-brand-900 placeholder-slate-300"
    />
  </div>
);
