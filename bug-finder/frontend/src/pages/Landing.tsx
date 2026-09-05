import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { FilesInput, useFileUpload, type FileEntry } from "../components/FilesInput";
import { scan, type ScanResult } from "../lib/api";
import { saveProject } from "../lib/store";
import { Header } from "../components/Header";
import { HealthBadge } from "../components/HealthBadge";

const EXAMPLE: FileEntry[] = [
  {
    name: "add.py",
    content: [
      "def add(a, b):",
      "    if a == 0:",
      "        return b",
      "    return a + b",
      "",
      "print(add(0, 5))",
      "print(add(None, 3))",
    ].join("\n"),
  },
];

export function Landing() {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [language, setLanguage] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const canScan = files.length > 0 && files.every((f) => f.name && f.content.trim());

  const run = async () => {
    if (!canScan) return;
    setLoading(true);
    setError(null);
    try {
      const filesMap: Record<string, string> = {};
      for (const f of files) filesMap[f.name] = f.content;
      const result: ScanResult = await scan(filesMap, language || undefined);
      saveProject(result.project_id, { files: filesMap, result });
      void navigate(`/workspace/${result.project_id}`);
    } catch (e: any) {
      setError(e.message ?? "scan failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Header />
      <main className="mx-auto grid max-w-6xl gap-10 px-4 py-12 md:py-16">
        <div className="text-center">
          <h1 className="text-4xl font-extrabold tracking-tight text-white md:text-5xl">
            Find. Fix. Ship with confidence.
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-slate-300">
            Paste or upload code from any codebase and get lint-level + AI-reviewed
            bug findings, each with a previewable fix diff you can apply with one click.
          </p>
        </div>

        <HealthBadge />

        <section className="space-y-2">
          <h2 className="text-sm font-semibold text-slate-300">Input source</h2>
          <Tabs />
        </section>

        <section className="rounded-xl border border-panel bg-panel p-5 shadow-xl">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="font-medium text-slate-200">Paste code</h3>
            <label className="text-xs text-slate-400">Language (optional):</label>
          </div>

          <div className="mb-4 flex gap-2">
            <select
              className="h-8 rounded bg-panel-2 border border-panel-2 text-slate-100 focus:border-brand focus:outline-none"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="">Auto-detect</option>
              <option value="python">Python</option>
              <option value="javascript">JavaScript</option>
              <option value="typescript">TypeScript</option>
            </select>
          </div>

          <FilesInput value={files} onChange={setFiles} loadExample={EXAMPLE} />

          <UploadArea onFiles={setFiles} existing={files} />

          {error && <p className="mt-3 text-sm text-rose-300">{error}</p>}

          <button
            onClick={run}
            disabled={!canScan || loading}
            className="mt-5 w-full rounded bg-brand px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-hover disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Scanning…" : "Scan for bugs"}
          </button>
        </section>

        <footer className="pt-6 text-center text-xs text-slate-500">
          v0.1 — lint-only mode works without configuration. Add an LLM provider key for
          semantic (AI) findings. See <code className="mx-1 rounded bg-panel-2 px-1.5 py-0.5">backend/.env.example</code>.
        </footer>
      </main>
    </>
  );
}

function Tabs() {
  return (
    <div className="flex gap-1.5 text-sm">
      <Tab active>Paste</Tab>
      <Tab>Upload</Tab>
      <Tab disabled>GitHub (v1.1)</Tab>
    </div>
  );
}

function Tab({ children, active = false, disabled = false }: { children: React.ReactNode; active?: boolean; disabled?: boolean }) {
  return (
    <button
      disabled={disabled}
      className={
        "rounded-t px-3 py-1 text-xs font-medium " +
        (disabled
          ? "cursor-not-allowed text-slate-500"
          : active
            ? "bg-panel text-brand"
            : "text-slate-400 hover:text-slate-200")
      }
    >
      {children}
    </button>
  );
}

function UploadArea({ onFiles, existing }: { onFiles: (f: FileEntry[]) => void; existing: FileEntry[] }) {
  const { drag, handlers, inputProps } = useFileUpload((added) => {
    const merged = [...existing];
    const byName = new Set(existing.map((f) => f.name));
    for (const f of added) {
      if (byName.has(f.name)) {
        const i = merged.findIndex((m) => m.name === f.name);
        merged[i] = f;
      } else {
        merged.push(f);
      }
    }
    onFiles(merged);
  });
  return (
    <label
      className={
        "mt-4 flex min-h-[110px] cursor-pointer items-center justify-center rounded-xl border-2 border-dashed text-center text-sm transition " +
        (drag
          ? "border-brand bg-panel-2/60 text-slate-100"
          : "border-panel-2 text-slate-400 hover:border-brand/50")
      }
    >
      <input {...inputProps} {...handlers} className="sr-only" />
      <span className="px-2">
        {drag ? "Drop to add" : "Or drop files here — they'll be appended as new tabs"}
      </span>
    </label>
  );
}
