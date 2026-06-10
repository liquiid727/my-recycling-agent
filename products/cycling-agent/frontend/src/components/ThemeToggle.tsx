/*
 * CN: 主题切换组件，负责在运动极简和户外手账两套视觉主题之间切换。
 * EN: Theme switcher component for toggling between sport-minimal and trail-journal visual themes.
 */

import { useEffect, useState } from "react";

const THEME_STORAGE_KEY = "cycling-agent-theme";

const themes = [
  {
    id: "sport-minimal",
    label: "城市骑行运动极简",
    shortLabel: "运动极简"
  },
  {
    id: "trail-journal",
    label: "户外路线手账",
    shortLabel: "路线手账"
  }
] as const;

type ThemeId = (typeof themes)[number]["id"];

function readInitialTheme(): ThemeId {
  if (typeof window === "undefined" || typeof window.localStorage?.getItem !== "function") {
    return "sport-minimal";
  }

  return window.localStorage.getItem(THEME_STORAGE_KEY) === "trail-journal" ? "trail-journal" : "sport-minimal";
}

export default function ThemeToggle() {
  const [theme, setTheme] = useState<ThemeId>(readInitialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    if (typeof window.localStorage?.setItem === "function") {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme);
    }
  }, [theme]);

  return (
    <div className="theme-bar" aria-label="主题切换">
      <span className="theme-bar-label">Theme</span>
      <div className="theme-switch" role="group" aria-label="骑行界面主题">
        {themes.map((item) => (
          <button
            className="theme-option"
            type="button"
            key={item.id}
            aria-label={item.label}
            aria-pressed={theme === item.id}
            data-active={theme === item.id ? "true" : undefined}
            onClick={() => setTheme(item.id)}
          >
            {item.shortLabel}
          </button>
        ))}
      </div>
    </div>
  );
}
