import { FormEvent } from "react";
import { Link } from "react-router-dom";

import { ErrorCard } from "../components/EditorialStates";
import PlanResultView from "../components/PlanResultView";
import { usePlannerFlow } from "../features/planner/hooks";

const plannerModeCopy = {
  route: {
    label: "今晚 / 城市轻骑",
    note: "适合下班后、傍晚和半日慢骑，优先走原来的 chat-first 路线咨询链路。",
  },
  nearby_trip: {
    label: "周末 / 周边出行",
    note: "保留周末和多天出行规划语义，继续走同一套 planner 编排。",
  },
} as const;

export default function PlannerPage() {
  const planner = usePlannerFlow();

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    void planner.submit(event);
  }

  return (
    <>
      <header className="topnav">
        <div className="topnav-inner">
          <span className="topnav-logo">Over Cycling Planner</span>
          <nav aria-label="Planner 导航" className="topnav-nav">
            <Link to="/">首页</Link>
            <Link to="/planner">Planner</Link>
            <Link to="/admin">Admin</Link>
            <Link to="/settings">偏好</Link>
          </nav>
        </div>
      </header>

      <main className="paper-shell planner-page">
        <section className="paper-section planner-hero">
          <div>
            <p className="eyebrow">AGENT PLANNER</p>
            <h1 className="display-title max-w-[11ch]">把路线咨询主流程接回当前产品界面。</h1>
            <p className="lead-copy mt-5">
              这一页专门承接原来的 agent 主流程：多轮补槽、流式规划、地图、路书和 provider 轨迹。首页继续负责内容化入口，Planner 负责真正的路线咨询。
            </p>
          </div>
          <aside className="paper-card planner-hero-note">
            <p className="eyebrow">FLOW NOTES</p>
            <ul className="planner-bullet-list">
              <li>优先走 `/api/v1/ride/chat/turn` 补槽，再进 `/api/v1/ride/plan/stream`。</li>
              <li>结果页继续保留地图、风险、路书和 fallback 轨迹。</li>
              <li>高德地图仍然按原实现懒加载，点“加载地图”后再注入 SDK。</li>
            </ul>
          </aside>
        </section>

        <section className="planner-shell">
          <article className="paper-section planner-console">
            <div className="planner-toolbar">
              <div>
                <p className="eyebrow">PLANNING MODE</p>
                <h2 className="section-title">先选这次要聊哪一类路线。</h2>
              </div>
              <div aria-label="规划模式" className="planner-mode-switch" role="tablist">
                <button
                  aria-selected={planner.planningMode === "route"}
                  className={planner.planningMode === "route" ? "primary-button" : "secondary-button"}
                  onClick={() => planner.setPlanningMode("route")}
                  role="tab"
                  type="button"
                >
                  今晚 / 城市轻骑
                </button>
                <button
                  aria-selected={planner.planningMode === "nearby_trip"}
                  className={planner.planningMode === "nearby_trip" ? "primary-button" : "secondary-button"}
                  onClick={() => planner.setPlanningMode("nearby_trip")}
                  role="tab"
                  type="button"
                >
                  周末 / 周边出行
                </button>
              </div>
            </div>

            <p className="body-copy planner-mode-note">{plannerModeCopy[planner.planningMode].note}</p>

            <div aria-live="polite" className="planner-chat-log">
              {planner.messages.map((message) => (
                <div className={`planner-bubble ${message.role === "user" ? "user" : ""}`} key={message.id}>
                  {message.content}
                </div>
              ))}
            </div>

            <div aria-label="快捷建议" className="quick-prompts">
              {planner.quickReplies.map((reply) => (
                <button key={reply} onClick={() => planner.setQueryFromQuickReply(reply)} type="button">
                  {reply}
                </button>
              ))}
            </div>

            <section className="mt-6 grid gap-4 md:grid-cols-3" aria-label="骑前状态">
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-ink">身体状态</span>
                <select
                  aria-label="身体状态"
                  className="field-input"
                  value={planner.riderState.fatigue_level}
                  onChange={(event) => planner.setRiderStateField("fatigue_level", event.target.value as "" | "fresh" | "normal" | "tired")}
                >
                  <option value="">先不指定</option>
                  <option value="fresh">刚休息好</option>
                  <option value="normal">正常</option>
                  <option value="tired">有点累</option>
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-ink">这次想怎么骑</span>
                <select
                  aria-label="这次想怎么骑"
                  className="field-input"
                  value={planner.riderState.mood}
                  onChange={(event) => planner.setRiderStateField("mood", event.target.value as "" | "relax" | "exercise" | "explore" | "social" | "recover")}
                >
                  <option value="">先不指定</option>
                  <option value="relax">放松散心</option>
                  <option value="recover">恢复一下</option>
                  <option value="explore">想逛逛</option>
                  <option value="exercise">想活动活动</option>
                  <option value="social">想约人一起</option>
                </select>
              </label>
              <label className="block">
                <span className="mb-2 block text-sm font-semibold text-ink">上次骑行</span>
                <select
                  aria-label="上次骑行"
                  className="field-input"
                  value={planner.riderState.last_ride_days_ago}
                  onChange={(event) => planner.setRiderStateField("last_ride_days_ago", event.target.value ? Number(event.target.value) : "")}
                >
                  <option value="">先不指定</option>
                  <option value="0">今天刚骑过</option>
                  <option value="1">昨天</option>
                  <option value="3">3 天前</option>
                  <option value="7">一周前</option>
                </select>
              </label>
            </section>

            <form className="planner-form" onSubmit={handleSubmit}>
              <label className="block" htmlFor="plannerQuery">
                <span className="body-copy block text-[13px]">从一句自然语言开始</span>
              </label>
              <div className="planner-form-row">
                <input
                  aria-label="规划对话输入"
                  className="field-input"
                  id="plannerQuery"
                  placeholder="比如：我在闻涛路滨江段，今晚想轻松骑 2 小时，最好有江边和咖啡。"
                  type="text"
                  value={planner.query}
                  onChange={(event) => planner.setQuery(event.target.value)}
                />
                <button className="primary-button shrink-0" disabled={planner.loading} type="submit">
                  {planner.loading ? planner.loadingLabel ?? "规划中..." : "开始规划"}
                </button>
              </div>
            </form>

            {planner.error ? <ErrorCard body={planner.error} title="规划暂时不可用" /> : null}
          </article>

          <aside className="paper-section planner-sidebar">
            <div>
              <p className="eyebrow">LIVE STATUS</p>
              <h2 className="section-title">把每个阶段都留在台面上。</h2>
            </div>
            <div className="planner-status-chip-row">
              <span className="pill-tag">模式：{plannerModeCopy[planner.planningMode].label}</span>
              <span className="pill-tag">状态：{planner.loading ? "运行中" : planner.result ? "已生成结果" : "等待输入"}</span>
              {planner.riderState.fatigue_level ? <span className="pill-tag">体感：{planner.riderState.fatigue_level}</span> : null}
            </div>
            <div className="planner-stage-list">
              {planner.stageUpdates.length > 0 ? (
                planner.stageUpdates.map((stage, index) => (
                  <article className="planner-stage-card" key={`${stage.stage_name}-${index}`}>
                    <div className="planner-stage-head">
                      <strong>{stage.stage_name}</strong>
                      <span className="pill-tag">{stage.status}</span>
                    </div>
                    <p className="body-copy">{stage.summary}</p>
                    <p className="body-copy text-[13px]">
                      provider: {stage.provider_name}
                      {stage.fallback_reason ? ` / fallback: ${stage.fallback_reason}` : ""}
                    </p>
                  </article>
                ))
              ) : (
                <article className="planner-stage-card">
                  <div className="planner-stage-head">
                    <strong>waiting_for_request</strong>
                    <span className="pill-tag">idle</span>
                  </div>
                  <p className="body-copy">提交后这里会显示 query parser、天气、动态路线发现、风险、路书等阶段更新。</p>
                </article>
              )}
            </div>
            <div className="planner-actions">
              <Link className="secondary-button" to="/">
                返回首页
              </Link>
              <Link className="secondary-button" to="/settings">
                调整偏好
              </Link>
            </div>
          </aside>
        </section>

        {planner.result ? (
          <section className="planner-result-section">
            <PlanResultView result={planner.result} />
          </section>
        ) : null}
      </main>
    </>
  );
}
