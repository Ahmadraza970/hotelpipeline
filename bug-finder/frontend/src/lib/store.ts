import type { ScanResult } from "./api";

const KEY_PREFIX = "bf:project:";

export function saveProject(id: string, payload: { files: Record<string, string>; result: ScanResult }): void {
  localStorage.setItem(`${KEY_PREFIX}${id}`, JSON.stringify(payload));
}

export function loadProject(id: string): { files: Record<string, string>; result: ScanResult } | null {
  const raw = localStorage.getItem(`${KEY_PREFIX}${id}`);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as { files: Record<string, string>; result: ScanResult };
  } catch {
    return null;
  }
}

export function clearProject(id: string): void {
  localStorage.removeItem(`${KEY_PREFIX}${id}`);
}
