import { useState } from "react";

const KEY = "bf_premium";

export function isPremium(): boolean {
  if (typeof localStorage === "undefined") return false;
  return localStorage.getItem(KEY) === "true";
}

export function setPremium(v: boolean): void {
  if (typeof localStorage !== "undefined") {
    localStorage.setItem(KEY, v ? "true" : "false");
  }
}

export function usePremium() {
  const [premium, setPremiumState] = useState<boolean>(isPremium());
  const setPremiumFn = (v: boolean) => {
    setPremiumState(v);
    setPremium(v);
  };
  return { premium, setPremium: setPremiumFn };
}
