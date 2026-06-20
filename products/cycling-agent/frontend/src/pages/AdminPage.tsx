import { FormEvent } from "react";
import { Link } from "react-router-dom";

import { ErrorCard, LoadingCard } from "../components/EditorialStates";
import { useAdminExperienceContent } from "../features/admin-content/hooks";

export default function AdminPage() {
  const { content, loading, saving, error, persist, setContent } = useAdminExperienceContent();

  if (loading) {
    return (
      <main className="paper-shell">
        <LoadingCard title="正在打开内容编排后台" body="首页品牌文案、今日建议和伙伴话术正在加载中。" />
      </main>
    );
  }

  if (error || !content) {
    return (
      <main className="paper-shell">
        <ErrorCard title="内容后台暂时不可用" body={error ?? "请稍后再试。"} />
      </main>
    );
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!content) {
      return;
    }
    void persist(content);
  }

  return (
    <main className="paper-shell">
      <section className="paper-section">
        <p className="eyebrow">CONTENT ORCHESTRATION</p>
        <h1 className="display-title max-w-[12ch]">用内容把首页、伙伴和周末计划编在一起。</h1>
        <form className="mt-8 grid gap-5 lg:grid-cols-2" onSubmit={handleSubmit}>
          <label className="block lg:col-span-2">
            <span className="mb-2 block text-sm font-semibold text-ink">首页标题</span>
            <input
              aria-label="首页标题"
              className="field-input"
              value={content.hero.title}
              onChange={(event) => setContent({ ...content, hero: { ...content.hero, title: event.target.value } })}
            />
          </label>
          <label className="block lg:col-span-2">
            <span className="mb-2 block text-sm font-semibold text-ink">首页导语</span>
            <textarea
              className="field-input min-h-[120px]"
              value={content.hero.lead}
              onChange={(event) => setContent({ ...content, hero: { ...content.hero, lead: event.target.value } })}
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-semibold text-ink">CTA 按钮文案</span>
            <input
              aria-label="CTA 按钮文案"
              className="field-input"
              value={content.cta_footer.button_label}
              onChange={(event) => setContent({ ...content, cta_footer: { ...content.cta_footer, button_label: event.target.value } })}
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-semibold text-ink">伙伴标题</span>
            <input
              className="field-input"
              value={content.companion_persona.headline}
              onChange={(event) =>
                setContent({
                  ...content,
                  companion_persona: { ...content.companion_persona, headline: event.target.value },
                })
              }
            />
          </label>
          <label className="block lg:col-span-2">
            <span className="mb-2 block text-sm font-semibold text-ink">第一条今日建议</span>
            <input
              className="field-input"
              value={content.today_nudges[0]?.body ?? ""}
              onChange={(event) =>
                setContent({
                  ...content,
                  today_nudges: content.today_nudges.map((item, index) =>
                    index === 0 ? { ...item, body: event.target.value } : item,
                  ),
                })
              }
            />
          </label>
          <div className="flex flex-wrap items-center gap-3 lg:col-span-2">
            <button className="primary-button" disabled={saving} type="submit">
              {saving ? "保存中..." : "保存内容"}
            </button>
            <Link className="secondary-button" to="/planner">
              进入 Planner
            </Link>
          </div>
        </form>
      </section>
    </main>
  );
}
