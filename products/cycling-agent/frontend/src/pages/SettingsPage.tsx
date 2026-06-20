import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorCard, LoadingCard } from "../components/EditorialStates";
import { useLifestyleProfile } from "../features/lifestyle/hooks";

type LifestyleFormState = {
  home_region: string;
  preferred_vibe: string;
  companion_tone: string;
  favorite_motifs_text: string;
  avoid_motifs_text: string;
};

export default function SettingsPage() {
  const { profile, loading, saving, error, saved, persist } = useLifestyleProfile();
  const [form, setForm] = useState<LifestyleFormState | null>(null);

  const initialForm = useMemo(() => {
    if (!profile) {
      return null;
    }
    return {
      home_region: profile.home_region ?? "",
      preferred_vibe: profile.preferred_vibe ?? "",
      companion_tone: profile.companion_tone ?? "",
      favorite_motifs_text: profile.favorite_motifs.join(", "),
      avoid_motifs_text: profile.avoid_motifs.join(", "),
    };
  }, [profile]);

  const ready = form ?? initialForm;

  function updateForm<K extends keyof LifestyleFormState>(key: K, value: LifestyleFormState[K]) {
    if (!ready) {
      return;
    }
    setForm({ ...ready, [key]: value });
  }

  if (loading) {
    return (
      <main className="paper-shell">
        <LoadingCard title="正在读取你的生活方式偏好" body="树荫、咖啡、语气和避开的东西都会落在这一页。" />
      </main>
    );
  }

  if (error || !ready) {
    return (
      <main className="paper-shell">
        <ErrorCard title="偏好页暂时打不开" body={error ?? "请稍后再试。"} />
      </main>
    );
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!ready) {
      return;
    }
    void persist({
      home_region: ready.home_region,
      preferred_vibe: ready.preferred_vibe,
      companion_tone: ready.companion_tone,
      favorite_motifs: ready.favorite_motifs_text.split(",").map((item) => item.trim()).filter(Boolean),
      avoid_motifs: ready.avoid_motifs_text.split(",").map((item) => item.trim()).filter(Boolean),
    });
  }

  return (
    <main className="paper-shell">
      <section className="paper-section">
        <p className="eyebrow">LIFESTYLE PROFILE</p>
        <h1 className="display-title max-w-[12ch]">把你想留下的骑行质感说清楚。</h1>
        <form className="mt-8 grid gap-5 lg:grid-cols-2" onSubmit={handleSubmit}>
          <label className="block">
            <span className="mb-2 block text-sm font-semibold text-ink">常出发片区</span>
            <input
              aria-label="常出发片区"
              className="field-input"
              value={ready.home_region}
              onChange={(event) => updateForm("home_region", event.target.value)}
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-semibold text-ink">偏好的氛围</span>
            <input
              aria-label="偏好的氛围"
              className="field-input"
              value={ready.preferred_vibe}
              onChange={(event) => updateForm("preferred_vibe", event.target.value)}
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-semibold text-ink">伙伴语气</span>
            <input
              aria-label="伙伴语气"
              className="field-input"
              value={ready.companion_tone}
              onChange={(event) => updateForm("companion_tone", event.target.value)}
            />
          </label>
          <label className="block lg:col-span-2">
            <span className="mb-2 block text-sm font-semibold text-ink">喜欢的意象</span>
            <input
              aria-label="喜欢的意象"
              className="field-input"
              value={ready.favorite_motifs_text}
              onChange={(event) => updateForm("favorite_motifs_text", event.target.value)}
            />
          </label>
          <label className="block lg:col-span-2">
            <span className="mb-2 block text-sm font-semibold text-ink">想避开的东西</span>
            <input
              aria-label="想避开的东西"
              className="field-input"
              value={ready.avoid_motifs_text}
              onChange={(event) => updateForm("avoid_motifs_text", event.target.value)}
            />
          </label>
          <div className="flex flex-wrap items-center gap-3 lg:col-span-2">
            <button className="primary-button" disabled={saving} type="submit">
              {saving ? "保存中..." : "保存偏好"}
            </button>
            <Link className="secondary-button" to="/">返回首页</Link>
            {saved ? <span className="body-copy text-sm text-moss">偏好已保存</span> : null}
          </div>
        </form>
      </section>
    </main>
  );
}
