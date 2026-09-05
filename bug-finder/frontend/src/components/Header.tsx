import { Link } from "react-router-dom";

export function Header() {
  return (
    <header className="border-b border-panel bg-panel">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <Link to="/" className="text-xl font-semibold tracking-tight text-white">
          Bug Finder
        </Link>
        <nav className="flex items-center gap-3 text-sm text-slate-300">
          <Link to="/leads" className="rounded bg-brand px-2.5 py-1 text-xs font-semibold text-white hover:bg-brand-hover">
            Goa Leads
          </Link>
          <button
            className="rounded px-2.5 py-1 text-xs font-medium text-slate-300 hover:text-white"
            onClick={() => alert("Auth is planned for v1.1. Use the web app directly for now.")}
          >
            Sign in
          </button>
        </nav>
      </div>
    </header>
  );
}
