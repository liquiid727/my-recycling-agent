import { FormEvent, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { ErrorCard, LoadingCard } from "../components/EditorialStates";
import { useCompanionPlan, useExperienceHome } from "../features/experience/hooks";

type TemplatePreset = {
  titleLine: string;
  summary: string;
  tags: string[];
};

const templatePresets: Record<string, TemplatePreset> = {
  quiet: {
    titleLine: "周六 16:30 · 梧桐树荫小环线",
    summary: "先骑到公园北门，再绕湖半圈。中途在草坪边坐 10 分钟，回程经过面包店。",
    tags: ["轻松", "有树荫", "适合拍一张照片"],
  },
  coffee: {
    titleLine: "周日上午 10:20 · 河边拿铁停靠点",
    summary: "骑到河岸慢车道后右转，停在咖啡窗口。喝完再沿小巷回家，整段不用赶时间。",
    tags: ["咖啡", "慢车道", "适合独处"],
  },
  sunset: {
    titleLine: "周日 17:10 · 橘色桥面慢行",
    summary: "日落前到桥面，停 5 分钟看水面反光。回程穿过居民区，路短但很有周末感。",
    tags: ["日落", "拍照", "短途"],
  },
};

function RouteArt({ routeCode, sectionLabel }: { routeCode: string; sectionLabel: string }) {
  let variant = "park";
  const source = `${routeCode} ${sectionLabel}`.toLowerCase();
  if (source.includes("river") || source.includes("coffee") || sectionLabel.includes("咖啡")) {
    variant = "coffee";
  } else if (source.includes("sunset") || source.includes("hill") || sectionLabel.includes("日落")) {
    variant = "sunset";
  }
  return <div aria-hidden="true" className={`route-art ${variant}`} />;
}

function WeatherIcon() {
  return (
    <svg fill="none" stroke="currentColor" strokeWidth="1.6" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="5" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3" />
    </svg>
  );
}

function RideIcon() {
  return (
    <svg fill="none" stroke="currentColor" strokeWidth="1.6" viewBox="0 0 24 24">
      <path d="M4 17c4-8 12-8 16 0" />
      <path d="M7 17h10" />
      <path d="M12 5v5" />
    </svg>
  );
}

function JournalIcon() {
  return (
    <svg fill="none" stroke="currentColor" strokeWidth="1.6" viewBox="0 0 24 24">
      <path d="M5 18c4-2 10-2 14 0" />
      <path d="M8 14c1-4 7-4 8 0" />
      <path d="M12 6v6" />
    </svg>
  );
}

function SceneIllustration() {
  return (
    <div aria-label="日落时分，年轻程序员骑车穿过树荫城市公园的水彩手账风场景" className="scene">
      <svg aria-label="水彩纸张、树荫、公园小路、落日与骑车的人" role="img" viewBox="0 0 900 620">
        <defs>
          <linearGradient id="pathTone" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0" stopColor="var(--surface)" stopOpacity=".7" />
            <stop offset="1" stopColor="var(--accent)" stopOpacity=".18" />
          </linearGradient>
          <filter height="120%" id="watercolorPaper" width="120%" x="-10%" y="-10%">
            <feTurbulence baseFrequency=".018 .045" numOctaves="3" result="grain" seed="7" type="fractalNoise" />
            <feDisplacementMap in="SourceGraphic" in2="grain" scale="7" />
          </filter>
        </defs>
        <g className="watercolor">
          <circle cx="710" cy="112" fill="var(--accent)" opacity=".30" r="62" />
          <path d="M0 420 C160 360 260 378 420 330 C580 284 705 322 900 260 L900 620 L0 620 Z" fill="var(--leaf-soft)" />
          <path
            d="M-20 570 C160 465 350 410 530 405 C660 404 770 446 920 520 L920 620 L-20 620 Z"
            fill="url(#pathTone)"
            stroke="var(--border)"
            strokeWidth="2"
          />
        </g>
        <g className="sketch-line" opacity=".34" strokeWidth="4">
          <path d="M120 120 C150 210 130 280 98 355" />
          <path d="M215 80 C250 195 248 295 220 390" />
          <path d="M782 80 C740 202 742 300 772 382" />
        </g>
        <g fill="var(--leaf-soft)" stroke="var(--border)" strokeWidth="2">
          <circle cx="107" cy="112" r="70" />
          <circle cx="210" cy="86" r="78" />
          <circle cx="782" cy="90" r="86" />
          <circle cx="742" cy="168" r="60" />
        </g>
        <g className="sketch-line" opacity=".38" strokeWidth="2">
          <path d="M70 456 C210 420 316 438 450 404 C590 368 724 388 842 336" />
          <path d="M96 496 C244 452 378 436 520 440 C650 442 762 474 846 512" />
          <path d="M148 167 C188 144 226 137 270 144" />
          <path d="M706 194 C736 176 774 172 812 184" />
        </g>
        <g transform="translate(424 344)">
          <circle cx="32" cy="92" fill="none" opacity=".62" r="44" stroke="var(--fg)" strokeWidth="6" />
          <circle cx="162" cy="92" fill="none" opacity=".62" r="44" stroke="var(--fg)" strokeWidth="6" />
          <path
            d="M32 92 L80 38 L116 92 L78 92 L162 92 L122 40"
            fill="none"
            opacity=".66"
            stroke="var(--fg)"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="6"
          />
          <path d="M82 38 C72 18 82 4 101 4 C121 5 127 22 119 40" fill="var(--accent)" opacity=".75" />
          <path d="M101 4 L112 -26" stroke="var(--fg)" strokeLinecap="round" strokeWidth="6" />
          <circle cx="115" cy="-35" fill="var(--surface)" r="17" stroke="var(--fg)" strokeWidth="4" />
          <path d="M112 -18 C135 12 135 42 118 67" stroke="var(--fg)" strokeLinecap="round" strokeWidth="7" />
          <path d="M100 20 L75 52" stroke="var(--fg)" strokeLinecap="round" strokeWidth="6" />
        </g>
      </svg>
      <div className="scene-card">
        <div className="weather-panel">
          <div>
            <p className="body-copy text-[13px]">今天 17:40 · 城市公园</p>
            <strong className="block text-base text-ink">暖光、树影、路面干爽，适合慢慢骑。</strong>
          </div>
          <span className="weather-temp">24°</span>
        </div>
      </div>
    </div>
  );
}

export default function HomePage() {
  const { content, loading, error } = useExperienceHome();
  const { submitting, response, error: submitError, submit } = useCompanionPlan();
  const [message, setMessage] = useState("");
  const [lastSubmittedMessage, setLastSubmittedMessage] = useState<string | null>(null);
  const [selectedTemplateIndex, setSelectedTemplateIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const prompts = useMemo(() => response?.suggested_prompts ?? content?.companion_persona.quick_prompts ?? [], [response, content]);
  const weekendTemplates = content?.weekend_plan_templates ?? [];
  const selectedTemplate = weekendTemplates[selectedTemplateIndex] ?? weekendTemplates[0];
  const selectedTemplatePreset = templatePresets[selectedTemplate?.slug ?? "quiet"] ?? {
    titleLine: selectedTemplate?.title ?? "周末轻计划",
    summary: selectedTemplate?.summary ?? "把路线、停靠点和记忆提示组合成一张轻计划。",
    tags: selectedTemplate?.title ? [selectedTemplate.title] : [],
  };

  function focusCompanion() {
    const companion = document.getElementById("companion");
    if (!companion) {
      return;
    }
    const targetTop = companion.getBoundingClientRect().top + window.pageYOffset - 72;
    window.scrollTo({ top: targetTop, behavior: "smooth" });
    window.setTimeout(() => inputRef.current?.focus(), 420);
  }

  function showWeekend() {
    const weekend = document.getElementById("weekend-plan-panel");
    if (!weekend) {
      return;
    }
    const targetTop = weekend.getBoundingClientRect().top + window.pageYOffset - 140;
    window.scrollTo({ top: targetTop, behavior: "smooth" });
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = message.trim();
    if (!trimmed) {
      return;
    }
    setLastSubmittedMessage(trimmed);
    void submit(trimmed);
  }

  if (loading) {
    return (
      <main className="paper-shell">
        <LoadingCard body="首页内容、今日建议和伙伴语气正在整理中。" title="正在翻开今天的骑行首页" />
      </main>
    );
  }

  if (error || !content) {
    return (
      <main className="paper-shell">
        <ErrorCard body={error ?? "首页内容暂时不可用，请稍后再试。"} title="今天这页还没有准备好" />
      </main>
    );
  }

  return (
    <>
      <header className="topnav" data-od-id="topnav">
        <div className="topnav-inner">
          <span className="topnav-logo">Over Cycling 偶尔骑行</span>
          <nav aria-label="主导航" className="topnav-nav">
            <a href="#today">今日轻骑</a>
            <a href="#routes">附近路线</a>
            <a href="#companion">AI 伙伴</a>
          </nav>
          <button className="primary-button" onClick={focusCompanion} type="button">
            问问骑行伙伴
          </button>
        </div>
      </header>

      <main className="home-main" id="content">
        <section className="home-section" data-od-id="hero">
          <div className="paper-shell hero-layout">
            <div>
              <p className="eyebrow">{content.hero.eyebrow}</p>
              <h1 className="display-title">{content.hero.title}</h1>
              <p className="lead-copy mt-5">{content.hero.lead}</p>
              <div className="hero-cta mt-7">
                <button className="primary-button" onClick={focusCompanion} type="button">
                  {content.hero.primary_cta}
                </button>
                <button className="ghost-button" onClick={showWeekend} type="button">
                  {content.hero.secondary_cta} <span aria-hidden="true">→</span>
                </button>
              </div>
            </div>
            <SceneIllustration />
          </div>
        </section>

        <section className="home-section" data-od-id="today" id="today">
          <div className="paper-shell space-y-12">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div className="max-w-[42ch]">
                <p className="eyebrow">TODAY&apos;S NUDGE</p>
                <h2 className="section-title">把今天的出门理由写成一页手账。</h2>
              </div>
              <button className="secondary-button" type="button">
                换一个今日建议
              </button>
            </div>
            <div className="feature-grid">
              <article className="paper-card feature-card">
                <div aria-hidden="true" className="feature-mark">
                  <WeatherIcon />
                </div>
                <h3 className="mb-1 text-[22px] font-semibold text-ink">天气便签</h3>
                <p className="body-copy">{content.today_nudges[0]?.body ?? "傍晚微风，日落前 45 分钟最舒服。带一件薄外套，停在湖边看一会儿光。"}</p>
              </article>
              <article className="paper-card feature-card">
                <div aria-hidden="true" className="feature-mark">
                  <RideIcon />
                </div>
                <h3 className="mb-1 text-[22px] font-semibold text-ink">今日慢骑便条</h3>
                <p className="body-copy">{content.today_nudges[1]?.body ?? content.today_nudges[0]?.body ?? "从公司附近出发，沿树荫路骑到河边咖啡窗口；不用赶路，听完一张专辑就回来。"}</p>
              </article>
              <article className="paper-card feature-card">
                <div aria-hidden="true" className="feature-mark">
                  <JournalIcon />
                </div>
                <h3 className="mb-1 text-[22px] font-semibold text-ink">心情边注</h3>
                <p className="body-copy">{content.today_nudges[2]?.body ?? "如果你只是想离开屏幕十分钟，AI 伙伴会把路线缩短，优先推荐安静、绿多、有座位的地方。"}</p>
              </article>
            </div>
          </div>
        </section>

        <section className="home-section" data-od-id="nearby-routes" id="routes">
          <div className="paper-shell">
            <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="eyebrow">NEARBY ROUTES</p>
                <h2 className="section-title">像翻一本城市自然手账一样找路线。</h2>
              </div>
              <div aria-label="路线分类" className="flex flex-wrap gap-2" role="list">
                <span className="pill-tag">公园</span>
                <span className="pill-tag">咖啡</span>
                <span className="pill-tag">日落</span>
                <span className="pill-tag">拍照</span>
              </div>
            </div>
            <div className="route-grid">
              {content.curated_routes.map((route) => (
                <Link className="paper-card route-card block" key={route.route_code} to={`/routes/${route.route_code}`}>
                  <RouteArt routeCode={route.route_code} sectionLabel={route.section_label} />
                  <div>
                    <p className="body-copy mb-2 text-[13px]">{route.section_label}</p>
                    <h3 className="text-[22px] font-semibold text-ink">{route.title}</h3>
                    <p className="body-copy mb-0 mt-3">{route.summary}</p>
                    <div className="route-meta">
                      {route.tags.map((tag) => (
                        <span className="pill-tag" key={tag}>
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        <section className="home-section" data-od-id="ai-companion" id="companion">
          <div className="paper-shell companion-layout">
            <aside aria-label="AI 骑行伙伴角色卡" className="buddy-card">
              <div>
                <p className="eyebrow">AI COMPANION · FIELD NOTES</p>
                <h2 className="section-title">{content.companion_persona.headline}</h2>
                <p className="lead-copy mt-4">{content.companion_persona.description}</p>
              </div>
              <div aria-hidden="true" className="buddy-face" />
              <p className="body-copy text-[14px]">伙伴语气：温柔、成熟、少催促。像旅行手账里的旁白，记录天气、停靠点和心情，不谈速度、卡路里或训练表现。</p>
            </aside>

            <div className="chat-card">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="body-copy text-[13px]">今天的对话</p>
                  <h3 className="text-[22px] font-semibold text-ink">今天想把哪一页写进生活？</h3>
                </div>
                <span className="pill-tag">FRIEND MODE</span>
              </div>

              <div aria-live="polite" className="chat-log" id="chatLog">
                <div className="bubble">我看了一下今天的天气，傍晚很适合去树多的地方。你想要咖啡、日落，还是安静公园？</div>
                {lastSubmittedMessage ? <div className="bubble user">{lastSubmittedMessage}</div> : null}
                {response ? <div className="bubble">{response.assistant_message}</div> : null}
                {submitError ? <div className="bubble">{submitError}</div> : null}
              </div>

              <div aria-label="快捷提问" className="quick-prompts">
                {prompts.map((prompt) => (
                  <button key={prompt} onClick={() => setMessage(prompt)} type="button">
                    {prompt}
                  </button>
                ))}
              </div>

              <form className="space-y-3" onSubmit={handleSubmit}>
                <label className="block" htmlFor="chatInput">
                  <span className="body-copy block text-[13px]">也可以直接告诉它你的心情</span>
                </label>
                <div className="flex flex-col gap-3 sm:flex-row sm:items-stretch">
                  <input
                    aria-label="今天的对话输入"
                    className="field-input flex-1"
                    id="chatInput"
                    placeholder="比如：今天脑子有点满，想去树多的地方骑一小圈。"
                    ref={inputRef}
                    type="text"
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                  />
                  <button className="primary-button shrink-0" disabled={submitting} type="submit">
                    {submitting ? "整理这一页中..." : "发送"}
                  </button>
                </div>
              </form>

              {response?.featured_plan ? (
                <div className="planner-result">
                  <h3 className="text-[22px] font-semibold text-ink">{response.featured_plan.route_name}</h3>
                  <p className="body-copy mt-3">{response.featured_plan.summary_reason}</p>
                  <div className="route-meta">
                    <span className="pill-tag">{response.featured_plan.distance_km} km</span>
                    <span className="pill-tag">{response.featured_plan.estimated_duration_hours} h</span>
                    <span className="pill-tag">{response.featured_plan.risk_level}</span>
                  </div>
                  {response.request_no ? (
                    <div className="mt-4">
                      <Link className="secondary-button" to={`/plans/${response.request_no}`}>
                        查看完整结果
                      </Link>
                    </div>
                  ) : null}
                </div>
              ) : null}
            </div>
          </div>
        </section>

        <section className="home-section" data-od-id="weekend-plans">
          <div className="paper-shell weekend-layout">
            <div>
              <p className="eyebrow">WEEKEND PLAN</p>
              <h2 className="section-title">三种周末，像贴进本子里的小计划。</h2>
              <p className="lead-copy mt-4">选择你这个周末的状态，Over Cycling 会把路线、停靠点和记忆提示组合成一张轻计划：不追求效率，只留下值得记住的片段。</p>
              <div className="hero-cta mt-7">
                {weekendTemplates.map((item, index) => (
                  <button className="secondary-button" key={item.slug} type="button" onClick={() => setSelectedTemplateIndex(index)}>
                    {item.title}
                  </button>
                ))}
              </div>
            </div>
            <div className="paper-card p-7" id="weekend-plan-panel">
              <p className="body-copy text-[13px]">生成结果</p>
              <div className="planner-result">
                <h3 className="text-[22px] font-semibold text-ink">{selectedTemplatePreset.titleLine}</h3>
                <p className="body-copy mt-3">{selectedTemplate?.summary ?? selectedTemplatePreset.summary}</p>
                <div className="route-meta">
                  {selectedTemplatePreset.tags.map((tag) => (
                    <span className="pill-tag" key={tag}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="home-section" data-od-id="journal">
          <div className="paper-shell">
            <div className="mb-10 max-w-[42ch]">
              <p className="eyebrow">CYCLING JOURNAL</p>
              <h2 className="section-title">把骑行记成一页背包里的生活，而不是一组成绩。</h2>
            </div>
            <div className="journal-strip">
              {content.journal_cards.map((item) => (
                <article className="journal-card" key={`${item.label}-${item.title}`}>
                  <span className="body-copy text-[13px]">{item.label}</span>
                  <div>
                    <h3 className="text-[22px] font-semibold text-ink">{item.title}</h3>
                    <p className="body-copy mb-0 mt-3">
                      {item.label === "今天看到" && "AI 伙伴会把这种小事存进记忆，而不是追问你骑得快不快。"}
                      {item.label === "适合下次" && "系统会记住更舒服的时间段，下次直接提醒。"}
                      {item.label === "停靠点" && "可收藏成“慢骑路线”的固定休息点。"}
                      {item.label === "心情" && "用一句话收尾，形成更生活化的骑行回忆。"}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section className="home-section text-center" data-od-id="cta-strip">
          <div className="paper-shell max-w-[640px]">
            <div className="quote-mark">"</div>
            <blockquote className="quote-block mx-auto">{content.cta_footer.quote}</blockquote>
            <p className="lead-copy mx-auto mt-4 mb-8">{content.cta_footer.lead}</p>
            <button className="primary-button" onClick={focusCompanion} type="button">
              {content.cta_footer.button_label}
            </button>
          </div>
        </section>
      </main>

      <footer className="pagefoot" data-od-id="footer">
        <div className="pagefoot-inner">
          <span>© 2026 Over Cycling 偶尔骑行</span>
          <span className="body-copy text-[13px]">生活方式骑行 · 公园 · 咖啡 · 日落 · 记忆</span>
        </div>
      </footer>
    </>
  );
}
