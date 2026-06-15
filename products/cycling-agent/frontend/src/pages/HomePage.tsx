/*
 * CN: 首页规划页面，承载输入表单、流式阶段反馈、澄清提示和即时结果。
 * EN: Home planning page with query form, streaming stage feedback, clarification prompts, and inline results.
 */

import PlanResultView from "../components/PlanResultView";
import ThemeToggle from "../components/ThemeToggle";
import type { PlannerHandoffContext } from "../features/planner/api";
import { usePlannerFlow } from "../features/planner/hooks";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useEffect, useRef } from "react";

const START_POINT_SUGGESTIONS = [
  { name: "闻涛路滨江段", region: "滨江", hint: "钱塘江休闲往返" },
  { name: "杨公堤南口", region: "西湖", hint: "西湖/龙井轻爬坡" },
  { name: "湘湖游客中心", region: "湘湖", hint: "湘湖半日休闲" },
  { name: "奥体印象城外广场", region: "滨江", hint: "滨江晨骑刷圈" },
  { name: "余杭良渚文化村口", region: "余杭", hint: "余杭轻郊野" }
];

const REGION_OPTIONS = ["滨江", "西湖", "湘湖", "萧山", "余杭", "龙井"];

export default function HomePage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const appliedPlannerSeed = useRef<string | null>(null);
  const {
    clarificationPrompt,
    error,
    intent,
    inputMode,
    loading,
    loadingLabel,
    messages,
    quickReplies,
    query,
    result,
    setInputMode,
    setIntent,
    setHandoffContext,
    setQuery,
    setQueryFromQuickReply,
    setStructuredField,
    setTargetDate,
    detectOriginLocation,
    stageUpdates,
    structuredConstraints,
    submit,
    handoffContext,
    targetDate
  } = usePlannerFlow({
    onSuccess: (plan) => navigate(`/plans/${plan.request_no}`)
  });

  useEffect(() => {
    const handoffContext = buildPlannerHandoffContext(searchParams);
    const seededQuery = searchParams.get("seedQuery")?.trim();
    const seededIntent = searchParams.get("intent");
    if (!seededQuery && !handoffContext) {
      return;
    }
    const seedKey = `${seededIntent ?? ""}:${seededQuery ?? ""}:${handoffContext?.source ?? ""}:${handoffContext?.action_key ?? ""}:${handoffContext?.status_key ?? ""}`;
    if (appliedPlannerSeed.current === seedKey) {
      return;
    }
    appliedPlannerSeed.current = seedKey;
    setHandoffContext(handoffContext);
    if (seededIntent === "ride_plan" || seededIntent === "weekend_recommendation" || seededIntent === "ride_today") {
      setIntent(seededIntent);
    }
    if (seededQuery) {
      setQuery(seededQuery);
    }
    if (handoffContext?.origin_region) {
      setStructuredField("origin_region", handoffContext.origin_region);
    }
    if (handoffContext?.suggested_duration_hours != null) {
      setStructuredField("available_hours", String(handoffContext.suggested_duration_hours));
    }
    if (handoffContext?.suggested_scene === "weekend_trip") {
      setStructuredField("duration_bucket", "half_day");
    }
  }, [searchParams, setHandoffContext, setIntent, setQuery, setStructuredField]);

  function applyStartPointSuggestion(name: string, region: string) {
    setStructuredField("start_point", name);
    setStructuredField("origin_region", region);
  }

  function toggleDestinationPreference(preference: string) {
    const current = structuredConstraints.destination_preferences ?? [];
    const next = current.includes(preference) ? current.filter((item) => item !== preference) : [...current, preference];
    setStructuredField("destination_preferences", next);
  }

  return (
    <main className="page-shell">
      <ThemeToggle />
      <section className="hero-panel">
        <p className="eyebrow">AAA Ride Buddy</p>
        <h1>AAA骑车帮帮</h1>
        <p className="hero-copy">像和朋友聊天一样说出你想怎么骑。我会先帮你判断值不值得出发，再给轻松、可执行的路线选择。</p>
        <div className="hero-stat-row" aria-label="规划输出内容">
          <span>今天能不能骑</span>
          <span>帮我安排一次骑行</span>
          <span>周末去哪骑</span>
        </div>
        <p className="hero-link-row">
          <Link to="/settings">打开偏好设置</Link>
        </p>
      </section>

      <section className="planner-panel">
        {handoffContext ? (
          <article className="detail-panel state-success">
            <div className="section-heading">
              <p className="section-kicker">Planner Handoff</p>
              <h2>{formatHandoffHeadline(handoffContext)}</h2>
            </div>
            <p className="summary-copy">{formatHandoffBody(handoffContext)}</p>
            <div className="metric-row">
              <span>来源：{handoffContext.source === "monthly_summary" ? "月度总结" : "增长回顾"}</span>
              {handoffContext.status_key ? <span>状态：{handoffContext.status_key}</span> : null}
              {handoffContext.ride_count != null ? <span>{handoffContext.ride_count} 条记录</span> : null}
              {handoffContext.weekly_streak != null ? <span>连续 {handoffContext.weekly_streak} 周</span> : null}
              {handoffContext.origin_region ? <span>区域：{handoffContext.origin_region}</span> : null}
              {handoffContext.suggested_duration_hours != null ? <span>{handoffContext.suggested_duration_hours} h</span> : null}
            </div>
          </article>
        ) : null}
        <form className="planner-form" onSubmit={submit}>
          <div className="segmented-control" aria-label="骑行意图">
            <button type="button" aria-pressed={intent === "ride_today"} onClick={() => setIntent("ride_today")}>
              今天适合骑吗
            </button>
            <button type="button" aria-pressed={intent === "ride_plan"} onClick={() => setIntent("ride_plan")}>
              帮我安排一次骑行
            </button>
            <button type="button" aria-pressed={intent === "weekend_recommendation"} onClick={() => setIntent("weekend_recommendation")}>
              周末去哪骑
            </button>
          </div>
          <p className="planner-hint">
            {intent === "weekend_recommendation"
              ? "目的地方向、天数、住宿和返程建议"
              : intent === "ride_plan"
                ? "出发点、时长、风格和稳妥路线"
                : "先判断今天值不值得骑，再给保守建议"}
          </p>

          <div className="segmented-control" aria-label="规划输入方式">
            <button type="button" aria-pressed={inputMode === "natural"} onClick={() => setInputMode("natural")}>
              一句话描述
            </button>
            <button type="button" aria-pressed={inputMode === "structured"} onClick={() => setInputMode("structured")}>
              表单规划
            </button>
          </div>

          <section className="chat-panel" aria-label="骑行规划对话">
            <div className="quick-reply-row" aria-label="快捷回复">
              {((quickReplies ?? []).length > 0 ? quickReplies : ["今天适合骑吗", "骑 2 小时", "不要爬坡", "周末两天", "千岛湖"]).map((reply) => (
                <button key={reply} type="button" className="quick-reply-chip" onClick={() => setQueryFromQuickReply(reply)}>
                  {reply}
                </button>
              ))}
            </div>
            <div className="chat-thread">
              {messages.map((message) => (
                <article key={message.id} className={`chat-message chat-message-${message.role}`}>
                  <span>{message.role === "assistant" ? "AAA骑车帮帮" : "你"}</span>
                  <p>{message.content}</p>
                </article>
              ))}
              {loading ? (
                <article className="chat-message chat-message-assistant">
                  <span>AAA骑车帮帮</span>
                  <p>{loadingLabel ?? (intent === "weekend_recommendation" ? "我正在整理周末出行方案，先给你结论。" : "我正在看天气和路线难度。")}</p>
                </article>
              ) : null}
            </div>

            {inputMode === "natural" ? (
              <label className="field-label chat-composer" htmlFor="planner-query">
                骑行需求
                <textarea
                  id="planner-query"
                  className="planner-input"
                  placeholder={
                    clarificationPrompt
                      ? intent === "weekend_recommendation"
                        ? "直接回复：从杭州市区出发，骑两天，可以过夜"
                        : "直接回复：从闻涛路滨江段出发，骑 2 小时，不要爬坡"
                      : intent === "weekend_recommendation"
                        ? "例如：周末想出去骑车，附近有什么推荐线路么"
                        : intent === "ride_plan"
                          ? "例如：从滨江出发骑两小时，不想太累"
                          : "例如：我今天晚上想出去骑行一下"
                  }
                  rows={3}
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                />
              </label>
            ) : null}
          </section>

          {inputMode === "structured" ? (
            <div className="structured-grid structured-grid-followup">
              <label className="field-label" htmlFor="target-date">
                目标日期
                <input id="target-date" type="date" value={targetDate} onChange={(event) => setTargetDate(event.target.value)} />
              </label>
              <label className="field-label" htmlFor="departure-time">
                出发时间
                <input
                  id="departure-time"
                  type="time"
                  value={structuredConstraints.departure_time ?? ""}
                  onChange={(event) => setStructuredField("departure_time", event.target.value)}
                />
              </label>
              <label className="field-label field-label-wide" htmlFor="start-point">
                准确出发地点
                <input
                  id="start-point"
                  aria-label="准确出发地点"
                  placeholder="输入路名、地标或骑行集合点，例如：闻涛路滨江段"
                  value={structuredConstraints.start_point ?? ""}
                  onChange={(event) => setStructuredField("start_point", event.target.value)}
                />
              </label>
              <div className="field-label">
                定位
                <button type="button" className="secondary-button" onClick={detectOriginLocation}>
                  使用当前位置
                </button>
              </div>
              <label className="field-label" htmlFor="origin-region">
                出发片区
                <select
                  id="origin-region"
                  aria-label="出发片区"
                  value={structuredConstraints.origin_region ?? "滨江"}
                  onChange={(event) => setStructuredField("origin_region", event.target.value)}
                >
                  {REGION_OPTIONS.map((region) => (
                    <option key={region} value={region}>
                      {region}
                    </option>
                  ))}
                </select>
              </label>
              <div className="field-label field-label-wide">
                地点关键字
                <div className="suggestion-row" aria-label="常用出发地点">
                  {START_POINT_SUGGESTIONS.map((item) => (
                    <button
                      key={item.name}
                      type="button"
                      className="suggestion-chip"
                      aria-label={item.name}
                      onClick={() => applyStartPointSuggestion(item.name, item.region)}
                    >
                      <span>{item.name}</span>
                      <small>{item.hint}</small>
                    </button>
                  ))}
                </div>
              </div>
              <label className="field-label" htmlFor="available-hours">
                可骑时长
                <input
                  id="available-hours"
                  type="number"
                  min="0"
                  step="0.5"
                  value={structuredConstraints.available_hours ?? ""}
                  onChange={(event) => setStructuredField("available_hours", event.target.value)}
                />
              </label>
              <label className="field-label" htmlFor="target-distance">
                目标距离
                <input
                  id="target-distance"
                  type="number"
                  min="0"
                  step="1"
                  value={structuredConstraints.target_distance_km ?? ""}
                  onChange={(event) => setStructuredField("target_distance_km", event.target.value)}
                />
              </label>
              {intent === "weekend_recommendation" ? (
                <>
                  <label className="field-label" htmlFor="duration-bucket">
                    出行时长
                    <select
                      id="duration-bucket"
                      value={structuredConstraints.duration_bucket ?? "two_day"}
                      onChange={(event) => setStructuredField("duration_bucket", event.target.value)}
                    >
                      <option value="two_day">两天</option>
                      <option value="three_day">三天</option>
                      <option value="half_day">半天</option>
                      <option value="one_day">一天</option>
                    </select>
                  </label>
                  <label className="field-label" htmlFor="return-preference">
                    返程偏好
                    <select
                      id="return-preference"
                      value={structuredConstraints.return_preference ?? "ride_back"}
                      onChange={(event) => setStructuredField("return_preference", event.target.value)}
                    >
                      <option value="ride_back">骑回</option>
                      <option value="public_transport">公共交通返程</option>
                      <option value="shorten_route">缩短路线</option>
                    </select>
                  </label>
                  <label className="field-label" htmlFor="overnight-preference">
                    过夜偏好（两天以上更关键）
                    <select
                      id="overnight-preference"
                      value={structuredConstraints.overnight_preference ?? "required"}
                      onChange={(event) => setStructuredField("overnight_preference", event.target.value)}
                    >
                      <option value="required">接受过夜</option>
                      <option value="optional">可过夜可不住</option>
                      <option value="avoid">不想过夜</option>
                    </select>
                  </label>
                  <label className="field-label" htmlFor="lodging-preference">
                    住宿偏好
                    <input
                      id="lodging-preference"
                      value={structuredConstraints.lodging_preference ?? ""}
                      onChange={(event) => setStructuredField("lodging_preference", event.target.value)}
                    />
                  </label>
                  <div className="field-label field-label-wide">
                    目的地偏好
                    <div className="suggestion-row" aria-label="目的地偏好">
                      {["千岛湖", "湖州", "江边", "咖啡", "亲水", "湖区", "公园", "茶村", "轻爬坡", "轻郊游"].map((preference) => (
                        <button
                          key={preference}
                          type="button"
                          className="suggestion-chip"
                          aria-pressed={(structuredConstraints.destination_preferences ?? []).includes(preference)}
                          onClick={() => toggleDestinationPreference(preference)}
                        >
                          <span>{preference}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                </>
              ) : null}
              <label className="field-label" htmlFor="fitness-level">
                体力等级
                <select
                  id="fitness-level"
                  value={structuredConstraints.fitness_level ?? "medium"}
                  onChange={(event) => setStructuredField("fitness_level", event.target.value)}
                >
                  <option value="low">low</option>
                  <option value="medium">medium</option>
                  <option value="high">high</option>
                </select>
              </label>
              <label className="field-label" htmlFor="ride-style">
                骑行风格
                <select
                  id="ride-style"
                  value={structuredConstraints.ride_style ?? "scenic_relaxed"}
                  onChange={(event) => setStructuredField("ride_style", event.target.value)}
                >
                  <option value="scenic_relaxed">风景轻松</option>
                  <option value="climb">轻爬坡</option>
                  <option value="training_loop">刷圈训练</option>
                  <option value="general">通用</option>
                </select>
              </label>
              <label className="field-label" htmlFor="slope-tolerance">
                爬坡接受度
                <select
                  id="slope-tolerance"
                  value={structuredConstraints.slope_tolerance ?? "avoid"}
                  onChange={(event) => setStructuredField("slope_tolerance", event.target.value)}
                >
                  <option value="avoid">avoid</option>
                  <option value="neutral">neutral</option>
                  <option value="prefer">prefer</option>
                </select>
              </label>
              <label className="field-label" htmlFor="priority">
                偏好重点
                <input
                  id="priority"
                  value={structuredConstraints.priority ?? ""}
                  onChange={(event) => setStructuredField("priority", event.target.value)}
                />
              </label>
            </div>
          ) : null}
          <div className="planner-actions">
            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? "规划中..." : inputMode === "natural" ? "发送" : "开始规划"}
            </button>
            <p className="planner-hint">直接补一句就行，我会记住前面聊过的内容。</p>
          </div>
        </form>
      </section>

      <section className="result-grid">
        {!loading && !error && !result ? (
          <article className="state-panel">
            <h2>待生成</h2>
            <p>提交后会先返回本次是否建议出发，再展示路线、天气风险、补给、装备和周末住宿安排。</p>
          </article>
        ) : null}

        {loading ? (
          <article className="state-panel">
            <h2>{loadingLabel ?? "正在生成路线建议"}</h2>
            <p>{intent === "weekend_recommendation" ? "系统正在匹配周末目的地、路线模板、住宿、装备、天气窗口、返程方案与风险。" : "系统正在解析需求、确认出发点、匹配市区路线，并计算天气与风险。"}</p>
            {stageUpdates.length > 0 ? (
              <ul className="stage-update-list">
                {stageUpdates.map((stage, index) => (
                  <li key={`${stage.stage_name}-${index}`}>
                    <strong>{stage.stage_name}</strong>
                    {" · "}
                    {stage.summary}
                  </li>
                ))}
              </ul>
            ) : null}
          </article>
        ) : null}

        {error ? (
          <article className="state-panel state-error" role="alert">
            <h2>请求失败</h2>
            <p>{error}</p>
          </article>
        ) : null}

        {result ? <PlanResultView result={result} /> : null}
      </section>
    </main>
  );
}

function buildPlannerHandoffContext(searchParams: URLSearchParams): PlannerHandoffContext | null {
  const source = searchParams.get("handoffSource");
  const actionKey = searchParams.get("handoffActionKey");
  const suggestedScene = searchParams.get("handoffScene");
  if (
    (source !== "monthly_summary" && source !== "growth_review")
    || (suggestedScene !== "city_ride" && suggestedScene !== "weekend_trip")
    || !actionKey
  ) {
    return null;
  }
  return {
    source,
    action_key: actionKey as PlannerHandoffContext["action_key"],
    suggested_scene: suggestedScene,
    seed_query: searchParams.get("seedQuery")?.trim() || undefined,
    source_month: searchParams.get("handoffMonth")?.trim() || undefined,
    source_window_days: parseOptionalInt(searchParams.get("handoffWindowDays")) as PlannerHandoffContext["source_window_days"],
    status_key: searchParams.get("handoffStatus")?.trim() || undefined,
    ride_count: parseOptionalInt(searchParams.get("handoffRideCount")),
    weekly_streak: parseOptionalInt(searchParams.get("handoffWeeklyStreak")),
    recent_ride_count: parseOptionalInt(searchParams.get("handoffRecentRideCount")),
    total_distance_km: parseOptionalFloat(searchParams.get("handoffDistanceKm")),
    origin_region: searchParams.get("handoffOriginRegion")?.trim() || undefined,
    top_tag: searchParams.get("handoffTag")?.trim() || undefined,
    suggested_duration_hours: parseOptionalFloat(searchParams.get("handoffSuggestedHours")),
  };
}

function parseOptionalInt(value: string | null): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function parseOptionalFloat(value: string | null): number | undefined {
  if (!value) {
    return undefined;
  }
  const parsed = Number.parseFloat(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function formatHandoffHeadline(handoffContext: PlannerHandoffContext): string {
  if (handoffContext.source === "growth_review") {
    return "已从增长回顾带入这次规划上下文";
  }
  return "已从月度总结带入这次规划上下文";
}

function formatHandoffBody(handoffContext: PlannerHandoffContext): string {
  if (handoffContext.source === "growth_review") {
    return "当前规划会带上最近滚动窗口的节奏信息，方便把下一次出门接在真实进展之后。";
  }
  return "当前规划会带上最近月度节奏和下一步建议，不再只是把一句 seed 文案塞回首页。";
}
