export type Severity = "Critical" | "High" | "Medium" | "Low" | "Info";
export type BugStatus = "open" | "dismissed" | "fixed";
export type BugSource = "lint" | "llm";

export interface Bug {
  id: string;
  file: string;
  line: number;
  end_line?: number | null;
  column?: number | null;
  severity: Severity;
  confidence: number;
  category: string;
  title: string;
  description: string;
  snippet?: string | null;
  status: BugStatus;
  source: BugSource;
}

export interface ScanSummary {
  total: number;
  by_severity: Record<string, number>;
  by_source: Record<string, number>;
  languages: string[];
}

export interface ScanResult {
  project_id: string;
  bugs: Bug[];
  summary: ScanSummary;
  elapsed_ms: number;
}

export interface FixResult {
  bug_id: string;
  file: string;
  diff: string;
  lint_ok: boolean;
  explanation: string;
}

export interface ExportResult {
  patch: string;
  bytes: number;
}

const base = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");

type JsonOptions = { [k: string]: unknown };
async function post<T>(path: string, body: JsonOptions): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`request to ${path} failed (${res.status}): ${text}`);
  }
  return (await res.json()) as T;
}

export async function scan(
  files: Record<string, string>,
  language?: string,
): Promise<ScanResult> {
  return post<ScanResult>("/scan", { files, language });
}

export async function fix(projectId: string, bugId: string): Promise<FixResult> {
  return post<FixResult>("/fix", { project_id: projectId, bug_id: bugId });
}

export async function exportPatch(
  projectId: string,
  diffs?: FixResult[],
): Promise<ExportResult> {
  return post<ExportResult>(
    "/export",
    diffs ? { diffs } : { project_id: projectId },
  );
}

export async function health(): Promise<{ ok: boolean }> {
  const res = await fetch(`${base}/health`);
  return (await res.json()) as { ok: boolean };
}
