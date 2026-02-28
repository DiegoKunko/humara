import { Icon } from "./Icon";

export const Navbar = () => (
  <nav className="border-b border-slate-100 bg-white/80 backdrop-blur-md sticky top-0 z-20">
    <div className="max-w-5xl mx-auto px-5 md:px-8 h-16 flex items-center justify-between">
      <img src="/logo-humara.png" alt="Humara" className="h-16" />
      <div className="flex items-center gap-1.5 bg-accent-50 text-accent-600 px-3 py-1.5 rounded-full">
        <Icon name="shield" size={13} />
        <span className="text-xs font-semibold">Certificado</span>
      </div>
    </div>
  </nav>
);
