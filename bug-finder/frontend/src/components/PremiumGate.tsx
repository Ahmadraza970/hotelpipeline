import { useNavigate } from "react-router-dom";

interface Props {
  onRequest?: (name: string) => void;
}

export function PremiumGate({ onRequest }: Props) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-xl border border-panel bg-panel p-6 shadow-xl">
        <div className="flex items-center gap-3">
          <span className="text-amber-400">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M1 21h22L12 2 1 21zm12-3v-2h-2v2h2zm0-3.5c-.55 0-1-.45-1-1V12c0-.55.45-1 1-1h2c.55 0 1 .45 1 1v2.5c0 .55-.45 1-1 1h-2z" />
            </svg>
          </span>
          <h3 className="text-lg font-semibold text-white">AI Fix Generator is a Pro feature</h3>
        </div>
        <p className="mt-2 text-sm text-slate-300">
          Your scan found bugs. Generating and validating an AI-suggested fix consumes
          model calls and is reserved for Pro and Team plans.
        </p>
        <ul className="mt-3 space-y-1 text-sm text-slate-300">
          <li className="flex items-center gap-2">
            <span className="text-emerald-400">✓</span>
            Unlimited AI fix suggestions
          </li>
          <li className="flex items-center gap-2">
            <span className="text-emerald-400">✓</span>
            Semantic (LLM judge) bug findings
          </li>
          <li className="flex items-center gap-2">
            <span className="text-emerald-400">✓</span>
            One-click GitHub PR creation
          </li>
          <li className="flex items-center gap-2">
            <span className="text-emerald-400">✓</span>
            2000+ lines / month
          </li>
        </ul>
        <div className="mt-5 flex gap-3">
          <button
            onClick={() => onRequest?.("pro")}
            className="flex-1 rounded bg-brand px-4 py-2 text-sm font-semibold text-white hover:bg-brand-hover"
          >
            Upgrade to Pro — $12/mo
          </button>
          <button
            onClick={() => onRequest?.("cancel")}
            className="flex-1 rounded bg-panel-2 px-4 py-2 text-sm text-slate-200 hover:bg-panel"
          >
            Maybe later
          </button>
        </div>
        <button
          onClick={() => useNavigate()("/pricing")}
          className="mt-3 text-center text-xs text-slate-400 underline hover:text-slate-200"
        >
          Compare all plans
        </button>
      </div>
    </div>
  );
}
