export const Spinner = () => (
  <div className="inline-flex items-center gap-1.5">
    <div className="w-1.5 h-1.5 bg-brand-500 rounded-full animate-[pulse_1s_ease-in-out_infinite]" />
    <div className="w-1.5 h-1.5 bg-brand-400 rounded-full animate-[pulse_1s_ease-in-out_0.2s_infinite]" />
    <div className="w-1.5 h-1.5 bg-brand-500 rounded-full animate-[pulse_1s_ease-in-out_0.4s_infinite]" />
  </div>
);
