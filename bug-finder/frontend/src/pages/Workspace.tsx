import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import type { Bug, FixResult } from "../lib/api";
import { loadProject } from "../lib/store";
import { exportPatch } from "../lib/api";
import { Header } from "../components/Header";
import { ScanSummary } from "../components/ScanSummary";
import { ResultList } from "../components/ResultList";
import { CodeEditor, type MarkerInput } from "../components/CodeEditor";
import { BugDetail } from "../components/BugDetail";
import { usePremium } from "../lib/premium";

export function Workspace() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [state, setState] = useState<{ files: Record<string, string>; result: any } | null>(null);
  const [activeFile, setActiveFile] = useState<string>("");
  const [selectedBug, setSelectedBug] = useState<Bug | null>(null);
  const [fixes, setFixes] = useState<Record<string, FixResult>>({});
  const { premium } = usePremium();

  useEffect(() => {
    if (!projectId) {
      navigate("/");
      return;
    }
    const loaded = loadProject(projectId);
    if (!loaded) {
      navigate("/");
      return;
    }
    setState({ files: loaded.files, result: loaded.result });
    const files = Object.keys(loaded.files);
    setActiveFile(files[0] ?? "");
  }, [projectId, navigate]);

  if (!state) {
    return (
      <>
        <Header />
        <main className="mx-auto max-w-6xl px-4 py-12">
          <p className="text-slate-400">Loading project…</p>
        </main>
      </>
    );
  }

  const { files, result } = state;
  const bugs: Bug[] = result.bugs ?? [];
  const selectedFile = activeFile;
  const applied = Object.values(fixes);
  const selectedFileBugs = bugs.filter((b) => b.file === selectedFile);

  const handleApplied = (res: FixResult) => {
    setFixes((prev) => ({ ...prev, [res.bug_id]: res }));
  };

  const handleExportAll = async () => {
    if (applied.length === 0) return;
    try {
      const res = await exportPatch(result.project_id);
      const blob = new Blob([res.patch], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `bug-fixes-${result.project_id}.patch`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert(e.message);
    }
  };

  const content = files[selectedFile] ?? "";
  const markers: MarkerInput[] = selectedFileBugs.map((b) => ({
    line: b.line,
    message: b.title,
    severity: b.severity === "Critical" || b.severity === "High" ? "error" : "warning",
  }));

  const explorerItems = Object.keys(files);

  return (
    <>
      <Header />
      <main className="mx-auto flex h-[calc(100vh-3.5rem)] max-w-6xl flex-col gap-4 px-4 py-4">
        <ScanSummary result={result} exploredFiles={explorerItems.length} />

        <div className="flex h-[calc(100vh-8rem)] w-full gap-3">
          {/* File explorer */}
          <nav className="flex w-56 shrink-0 flex-col gap-1 overflow-y-auto rounded-xl border border-panel bg-panel p-2">
            <button
              className="text-left rounded px-2 py-1 text-xs font-semibold text-slate-400 uppercase"
              disabled
            >
              Files
            </button>
            {explorerItems.map((f) => (
              <button
                key={f}
                onClick={() => {
                  setActiveFile(f);
                  setSelectedBug(null);
                }}
                className={
                  "truncate rounded px-2 py-1.5 text-left text-sm " +
                  (f === selectedFile
                    ? "bg-panel-2 text-brand"
                    : "text-slate-300 hover:bg-panel-2/60")
                }
                title={f}
              >
                {f}
              </button>
            ))}
          </nav>

          {/* Editor */}
          <div className="flex-1 rounded-xl border border-panel bg-panel">
            <CodeEditor
              key={selectedFile}
              value={content}
              file={selectedFile}
              markers={markers}
            />
          </div>

          {/* Results */}
          <div className="relative flex w-80 shrink-0 flex-col rounded-xl border border-panel bg-panel">
            <div className="border-b border-panel px-3 py-2 text-xs font-semibold text-slate-400">
              Findings
            </div>
            {!premium && (
              <div className="flex items-center justify-between gap-2 rounded-md bg-panel-2/60 px-3 py-2 text-xs text-amber-200">
                <span>AI fix suggestions require Pro</span>
                <a
                  href="/pricing"
                  className="shrink-0 rounded bg-brand px-2 py-1 text-[10px] font-semibold text-white text-center"
                >
                  Upgrade
                </a>
              </div>
            )}
            <div className="min-h-0 flex-1 overflow-y-auto">
              <ResultList
                bugs={bugs}
                selectedId={selectedBug?.id ?? null}
                onSelect={(b) => {
                  setSelectedBug(b);
                  if (b) {
                    setActiveFile(b.file);
                  }
                }}
                activeFile={selectedFile}
              />
            </div>
          </div>
        </div>

        {selectedBug && (
          <BugDetail
            projectId={result.project_id}
            bug={selectedBug}
            onClose={() => setSelectedBug(null)}
            onApplied={handleApplied}
            hasApplied={applied.length > 0}
            onExportAll={handleExportAll}
          />
        )}
      </main>
    </>
  );
}
