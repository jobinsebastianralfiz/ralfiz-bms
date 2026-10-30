import { useEffect, useState } from "react";

export type ThemeChoice = "system" | "light" | "dark";

const KEY = "noetsa:theme";
const EVENT = "noetsa:theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

export function getTheme(): ThemeChoice {
  try {
    const value = localStorage.getItem(KEY);
    return value === "light" || value === "dark" ? value : "system";
  } catch {
    return "system";
  }
}

/** "system" removes the attribute so the CSS media query decides. index.html applies the
 * saved choice before first paint to avoid a flash. */
export function setTheme(choice: ThemeChoice) {
  try {
    if (choice === "system") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, choice);
  } catch {
    // Private mode: the choice lasts until reload.
  }
  if (choice === "system") delete document.documentElement.dataset.theme;
  else document.documentElement.dataset.theme = choice;
  window.dispatchEvent(new Event(EVENT));
}

function resolve(choice: ThemeChoice) {
  return choice === "system" ? (window.matchMedia(DARK_QUERY).matches ? "dark" : "light") : choice;
}

/** The theme actually showing, following both the saved choice and the system setting. */
export function useResolvedTheme() {
  const [theme, setResolved] = useState(() => resolve(getTheme()));
  useEffect(() => {
    const update = () => setResolved(resolve(getTheme()));
    const mq = window.matchMedia(DARK_QUERY);
    mq.addEventListener("change", update);
    window.addEventListener(EVENT, update);
    return () => {
      mq.removeEventListener("change", update);
      window.removeEventListener(EVENT, update);
    };
  }, []);
  return theme;
}
