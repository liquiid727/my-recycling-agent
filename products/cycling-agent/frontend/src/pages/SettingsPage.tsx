/*
 * CN: 偏好设置页，编辑体能、坡度容忍和骑行风格并同步给后端。
 * EN: Settings page for editing fitness, slope tolerance, and ride style preferences and syncing them to backend.
 */

import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import ThemeToggle from "../components/ThemeToggle";
import {
  fetchUserProfile,
  loadUserProfile,
  persistUserProfile,
  saveUserProfile
} from "../features/settings/store";

export default function SettingsPage() {
  const [profile, setProfile] = useState(loadUserProfile);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function hydrateProfile() {
      try {
        const remoteProfile = await fetchUserProfile();
        if (cancelled || !remoteProfile) {
          return;
        }
        saveUserProfile(remoteProfile);
        setProfile(remoteProfile);
      } catch {
        if (!cancelled) {
          setError("当前未能同步远端偏好，已使用本地设置。");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    hydrateProfile();
    return () => {
      cancelled = true;
    };
  }, []);

  function togglePreference(tag: string) {
    setSaved(false);
    setProfile((current) => {
      const exists = current.ride_style_preferences.includes(tag);
      return {
        ...current,
        ride_style_preferences: exists
          ? current.ride_style_preferences.filter((item) => item !== tag)
          : [...current.ride_style_preferences, tag]
      };
    });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    saveUserProfile(profile);
    setSaved(false);
    setError(null);
    try {
      const persisted = await persistUserProfile(profile);
      saveUserProfile(persisted);
      setProfile(persisted);
      setSaved(true);
    } catch {
      setSaved(true);
      setError("远端偏好保存失败，当前已保留本地设置。");
    }
  }

  return (
    <main className="page-shell">
      <ThemeToggle />
      <section className="detail-panel">
        <div className="section-heading">
          <p className="section-kicker">Preferences</p>
          <h1>偏好设置</h1>
        </div>
        {loading ? <p className="summary-copy">正在同步已保存偏好...</p> : null}
        <form className="planner-form" onSubmit={submit}>
          <label className="field-label" htmlFor="fitness-level">
            体力等级
          </label>
          <select
            id="fitness-level"
            className="planner-input"
            value={profile.fitness_level}
            onChange={(event) => {
              setSaved(false);
              setProfile((current) => ({
                ...current,
                fitness_level: event.target.value as "low" | "medium" | "high" | ""
              }));
            }}
          >
            <option value="">未设置</option>
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>

          <label className="field-label" htmlFor="slope-tolerance">
            爬坡接受度
          </label>
          <select
            id="slope-tolerance"
            className="planner-input"
            value={profile.slope_tolerance}
            onChange={(event) => {
              setSaved(false);
              setProfile((current) => ({
                ...current,
                slope_tolerance: event.target.value as "avoid" | "neutral" | "prefer" | ""
              }));
            }}
          >
            <option value="">未设置</option>
            <option value="avoid">avoid</option>
            <option value="neutral">neutral</option>
            <option value="prefer">prefer</option>
          </select>

          <div className="preference-group">
            <span className="field-label">风格偏好</span>
            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={profile.ride_style_preferences.includes("scenic")}
                onChange={() => togglePreference("scenic")}
              />
              风景优先
            </label>
            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={profile.ride_style_preferences.includes("relaxed")}
                onChange={() => togglePreference("relaxed")}
              />
              轻松优先
            </label>
          </div>

          <div className="planner-actions">
            <button className="primary-button" type="submit">
              保存偏好
            </button>
            <Link to="/">返回规划页</Link>
          </div>
          {saved ? <p className="summary-copy">偏好已保存，下次规划会自动带入。</p> : null}
          {error ? <p className="summary-copy">{error}</p> : null}
        </form>
      </section>
    </main>
  );
}
