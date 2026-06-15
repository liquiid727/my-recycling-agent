import { ChangeEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import ThemeToggle from "../components/ThemeToggle";
import {
  getRideGrowthReview,
  getRideMonthlySummary,
  listRideRecords,
  trackRideGrowthReviewCtaClick,
  trackRideMonthlySummaryCtaClick,
  type RideGrowthReviewPayload,
  type RideGrowthReviewWindowDays,
  type RideMonthlySummaryPayload,
  type RideRecordListItem,
} from "../features/planner/api";

export default function RideRecordsPage() {
  const [items, setItems] = useState<RideRecordListItem[]>([]);
  const [month, setMonth] = useState(currentMonthValue());
  const [growthWindowDays, setGrowthWindowDays] = useState<RideGrowthReviewWindowDays>(90);
  const [growthReview, setGrowthReview] = useState<RideGrowthReviewPayload | null>(null);
  const [growthLoading, setGrowthLoading] = useState(true);
  const [growthError, setGrowthError] = useState<string | null>(null);
  const [summary, setSummary] = useState<RideMonthlySummaryPayload | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const plannerCtaHref = useMemo(() => {
    if (!summary) {
      return "/";
    }
    return buildPlannerHandoffHref({
      intent: summary.next_action.suggested_scene === "weekend_trip" ? "weekend_recommendation" : "ride_plan",
      seedQuery: summary.next_action.suggested_entry ?? summary.next_action.title,
      handoffSource: "monthly_summary",
      handoffActionKey: summary.next_action.action_key,
      handoffScene: summary.next_action.suggested_scene,
      handoffStatus: summary.habit_status,
      handoffRideCount: summary.ride_count,
      handoffWeeklyStreak: summary.weekly_streak,
      handoffRecentRideCount: summary.recent_30d_ride_count,
      handoffOriginRegion: summary.top_start_region ?? undefined,
      handoffTag: summary.top_tag ?? undefined,
      handoffMonth: summary.month,
      handoffSuggestedHours: suggestedDurationHoursForPlannerHandoff(summary.next_action.action_key, summary.next_action.suggested_scene),
    });
  }, [summary]);

  const growthPlannerCtaHref = useMemo(() => {
    if (!growthReview) {
      return "/";
    }
    return buildPlannerHandoffHref({
      intent: growthReview.next_focus.suggested_scene === "weekend_trip" ? "weekend_recommendation" : "ride_plan",
      seedQuery: growthReview.next_focus.suggested_entry ?? growthReview.next_focus.title,
      handoffSource: "growth_review",
      handoffActionKey: growthReview.next_focus.action_key,
      handoffScene: growthReview.next_focus.suggested_scene,
      handoffStatus: growthReview.growth_status,
      handoffRideCount: growthReview.ride_count,
      handoffWeeklyStreak: growthReview.best_weekly_streak,
      handoffDistanceKm: growthReview.total_distance_km,
      handoffOriginRegion: growthReview.top_start_region ?? undefined,
      handoffTag: growthReview.top_tag ?? undefined,
      handoffWindowDays: growthReview.window_days,
      handoffSuggestedHours: suggestedDurationHoursForPlannerHandoff(growthReview.next_focus.action_key, growthReview.next_focus.suggested_scene),
    });
  }, [growthReview]);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    void listRideRecords(12)
      .then((payload) => {
        if (!active) {
          return;
        }
        setItems(payload.items);
        setLoading(false);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setError("最近骑行记录暂时不可用，请稍后再试。");
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    setSummaryLoading(true);
    setSummaryError(null);

    void getRideMonthlySummary(month)
      .then((payload) => {
        if (!active) {
          return;
        }
        setSummary(payload.ride_monthly_summary);
        setSummaryLoading(false);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setSummaryError("本月骑行总结暂时不可用，请稍后再试。");
        setSummaryLoading(false);
      });

    return () => {
      active = false;
    };
  }, [month]);

  useEffect(() => {
    let active = true;
    setGrowthLoading(true);
    setGrowthError(null);

    void getRideGrowthReview(growthWindowDays)
      .then((payload) => {
        if (!active) {
          return;
        }
        setGrowthReview(payload.ride_growth_review);
        setGrowthLoading(false);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setGrowthError("增长回顾暂时不可用，请稍后再试。");
        setGrowthLoading(false);
      });

    return () => {
      active = false;
    };
  }, [growthWindowDays]);

  function handleMonthChange(event: ChangeEvent<HTMLInputElement>) {
    if (!event.target.value) {
      return;
    }
    setMonth(event.target.value);
  }

  function handlePlannerCtaClick() {
    if (!summary) {
      return;
    }
    void trackRideMonthlySummaryCtaClick({
      month: summary.month,
      action_key: summary.next_action.action_key,
      suggested_scene: summary.next_action.suggested_scene,
    }).catch(() => undefined);
  }

  function handleGrowthWindowChange(windowDays: RideGrowthReviewWindowDays) {
    setGrowthWindowDays(windowDays);
  }

  function handleGrowthPlannerCtaClick() {
    if (!growthReview) {
      return;
    }
    void trackRideGrowthReviewCtaClick({
      window_days: growthReview.window_days,
      action_key: growthReview.next_focus.action_key,
      suggested_scene: growthReview.next_focus.suggested_scene,
      growth_status: growthReview.growth_status,
    }).catch(() => undefined);
  }

  return (
    <main className="page-shell">
      <ThemeToggle />
      <section className="hero-panel">
        <p className="eyebrow">Recent Rides</p>
        <h1>最近骑行记录</h1>
        <p className="hero-copy">回看最近完成、缩短或取消的骑行记录，快速定位当时的收尾反馈和总结。</p>
        <p className="hero-link-row">
          <Link to="/rides/new">手动补录</Link>
          {" · "}
          <Link to="/">返回规划页</Link>
        </p>
      </section>

      <section className="result-grid">
        {summaryLoading ? (
          <article className="state-panel">
            <h2>正在加载本月骑行总结</h2>
            <p>系统正在聚合本月骑行节奏和下一步建议。</p>
          </article>
        ) : null}

        {summaryError ? (
          <article className="state-panel state-error" role="alert">
            <h2>本月骑行总结读取失败</h2>
            <p>{summaryError}</p>
          </article>
        ) : null}

        {!summaryLoading && !summaryError && summary ? (
          <div className="success-layout summary-band">
            <article className="detail-panel detail-panel-primary">
              <div className="section-heading">
                <p className="section-kicker">Monthly Summary</p>
                <h2>{summary.summary_headline}</h2>
              </div>
              <p className="summary-copy">{summary.summary_body}</p>
              <div className="month-toolbar">
                <label className="field-label" htmlFor="ride-summary-month">
                  查看月份
                  <input id="ride-summary-month" type="month" value={month} onChange={handleMonthChange} />
                </label>
                <div className="metric-row">
                  <span>{formatMonthLabel(summary.month)}</span>
                  <span>状态：{formatHabitStatus(summary.habit_status)}</span>
                  <span>最近一次：{formatLastRide(summary.last_ride_date, summary.days_since_last_ride)}</span>
                </div>
              </div>
            </article>

            <article className="detail-panel">
              <div className="section-heading">
                <p className="section-kicker">This Month</p>
                <h2>这段时间骑得怎么样</h2>
              </div>
              <div className="metric-row">
                <span>{summary.ride_count} 条记录</span>
                <span>{summary.ride_day_count} 个骑行日</span>
                <span>{summary.total_distance_km.toFixed(1)} km</span>
                <span>{summary.total_duration_hours.toFixed(1)} h</span>
                <span>连续 {summary.weekly_streak} 周</span>
                <span>近 30 天 {summary.recent_30d_ride_count} 次</span>
              </div>
              <div className="metric-row">
                <span>完成 {summary.completed_count}</span>
                <span>缩短 {summary.shortened_count}</span>
                <span>取消 {summary.cancelled_count}</span>
                {summary.top_start_region ? <span>常见出发区：{summary.top_start_region}</span> : null}
                {summary.top_tag ? <span>高频标签：{summary.top_tag}</span> : null}
              </div>
            </article>

            <article className="detail-panel">
              <div className="section-heading">
                <p className="section-kicker">Next Step</p>
                <h2>{summary.next_action.title}</h2>
              </div>
              <p className="summary-copy">{summary.next_action.body}</p>
              {summary.next_action.suggested_entry ? <p className="summary-copy">建议输入：{summary.next_action.suggested_entry}</p> : null}
              <div className="planner-actions">
                <Link className="primary-button button-link" to={plannerCtaHref} onClick={handlePlannerCtaClick}>
                  按这个建议去规划
                </Link>
                <span className="inline-note">场景：{summary.next_action.suggested_scene === "weekend_trip" ? "周末出行" : "城市骑行"}</span>
              </div>
            </article>
          </div>
        ) : null}

        {growthLoading ? (
          <article className="state-panel">
            <h2>正在加载增长回顾</h2>
            <p>系统正在回看最近一段时间的骑行节奏变化。</p>
          </article>
        ) : null}

        {growthError ? (
          <article className="state-panel state-error" role="alert">
            <h2>增长回顾读取失败</h2>
            <p>{growthError}</p>
          </article>
        ) : null}

        {!growthLoading && !growthError && growthReview ? (
          <article className="detail-panel growth-review-panel">
            <div className="review-toolbar">
              <div className="section-heading">
                <p className="section-kicker">Growth Review</p>
                <h2>{growthReview.review_headline}</h2>
              </div>
              <div className="segmented-control" aria-label="增长回顾窗口">
                {[30, 90, 180].map((windowDays) => (
                  <button
                    key={windowDays}
                    type="button"
                    aria-pressed={growthWindowDays === windowDays}
                    onClick={() => handleGrowthWindowChange(windowDays as RideGrowthReviewWindowDays)}
                  >
                    {`近 ${windowDays} 天`}
                  </button>
                ))}
              </div>
            </div>

            <p className="summary-copy">{growthReview.review_body}</p>
            <div className="metric-row">
              <span>{growthReview.ride_count} 次实际骑行</span>
              <span>{growthReview.ride_day_count} 个骑行日</span>
              <span>{growthReview.total_distance_km.toFixed(1)} km</span>
              <span>{growthReview.total_duration_hours.toFixed(1)} h</span>
              <span>最长 {growthReview.longest_distance_km.toFixed(1)} km</span>
              <span>连续 {growthReview.best_weekly_streak} 周</span>
            </div>
            <div className="metric-row">
              <span>状态：{formatGrowthStatus(growthReview.growth_status)}</span>
              <span>活跃月份 {growthReview.active_month_count}</span>
              {growthReview.top_start_region ? <span>常见出发区：{growthReview.top_start_region}</span> : null}
              {growthReview.top_tag ? <span>高频标签：{growthReview.top_tag}</span> : null}
              <span>{formatRideDelta(growthReview.recent_vs_previous_ride_delta)}</span>
              <span>{formatDistanceDelta(growthReview.recent_vs_previous_distance_delta_km)}</span>
            </div>

            {growthReview.milestones.length > 0 ? (
              <ul className="milestone-list">
                {growthReview.milestones.map((milestone) => (
                  <li key={milestone.milestone_key} className="milestone-item">
                    <strong>{milestone.title}</strong>
                    <span>{milestone.body}</span>
                  </li>
                ))}
              </ul>
            ) : null}

            <div className="planner-actions">
              <Link className="primary-button button-link" to={growthPlannerCtaHref} onClick={handleGrowthPlannerCtaClick}>
                {growthReview.next_focus.title}
              </Link>
              <span className="inline-note">
                场景：{growthReview.next_focus.suggested_scene === "weekend_trip" ? "周末出行" : "城市骑行"}
              </span>
            </div>
          </article>
        ) : null}

        {loading ? (
          <article className="state-panel">
            <h2>正在加载最近骑行记录</h2>
            <p>系统正在读取最近保存的骑后记录。</p>
          </article>
        ) : null}

        {error ? (
          <article className="state-panel state-error" role="alert">
            <h2>最近骑行记录读取失败</h2>
            <p>{error}</p>
          </article>
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <article className="state-panel">
            <h2>还没有骑行记录</h2>
            <p>先从一条手动补录开始，后面规划页里的骑后入口也会自动接到这里。</p>
            <p className="hero-link-row">
              <Link to="/rides/new">现在去补录</Link>
            </p>
          </article>
        ) : null}

        {!loading && !error && items.length > 0 ? (
          <div className="success-layout">
            {items.map((item) => (
              <article key={item.ride_record_no} className="detail-panel">
                <div className="section-heading">
                  <p className="section-kicker">Ride Record</p>
                  <h2>{item.route_title ?? item.destination_name ?? item.ride_record_no}</h2>
                </div>
                {item.summary_headline ? <p className="summary-copy">{item.summary_headline}</p> : null}
                <div className="metric-row">
                  <span>{item.ride_date}</span>
                  <span>完成情况：{item.completion_status}</span>
                  {item.destination_name ? <span>目的地：{item.destination_name}</span> : null}
                </div>
                <div className="planner-actions">
                  <Link aria-label={`查看记录 ${item.ride_record_no}`} to={`/rides/${item.ride_record_no}`}>
                    查看详情
                  </Link>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </main>
  );
}

function currentMonthValue(now = new Date()): string {
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  return `${year}-${month}`;
}

function formatMonthLabel(month: string): string {
  return `${month.slice(0, 4)} 年 ${month.slice(5, 7)} 月`;
}

function formatHabitStatus(status: RideMonthlySummaryPayload["habit_status"]): string {
  return {
    starting: "重新起步",
    rebuilding: "恢复节奏",
    steady: "节奏稳定",
    overreaching: "需要恢复",
  }[status];
}

function formatLastRide(lastRideDate?: string | null, daysSinceLastRide?: number | null): string {
  if (!lastRideDate) {
    return "本月还没有实际骑行";
  }
  if (daysSinceLastRide == null) {
    return lastRideDate;
  }
  return `${lastRideDate} · ${daysSinceLastRide} 天前`;
}

function formatGrowthStatus(status: RideGrowthReviewPayload["growth_status"]): string {
  return {
    building: "继续起步",
    steady: "节奏稳定",
    expanding: "范围在打开",
    resetting: "需要重新接回",
  }[status];
}

function formatRideDelta(delta: number): string {
  if (delta > 0) {
    return `近 30 天比前一段多 ${delta} 次`;
  }
  if (delta < 0) {
    return `近 30 天比前一段少 ${Math.abs(delta)} 次`;
  }
  return "近 30 天和前一段次数持平";
}

function formatDistanceDelta(delta: number): string {
  if (delta > 0) {
    return `距离多了 ${delta.toFixed(1)} km`;
  }
  if (delta < 0) {
    return `距离少了 ${Math.abs(delta).toFixed(1)} km`;
  }
  return "距离和前一段基本持平";
}

function buildPlannerHandoffHref(params: {
  intent: "ride_plan" | "weekend_recommendation" | "ride_today";
  seedQuery: string;
  handoffSource: "monthly_summary" | "growth_review";
  handoffActionKey: string;
  handoffScene: "city_ride" | "weekend_trip";
  handoffStatus?: string;
  handoffRideCount?: number;
  handoffWeeklyStreak?: number;
  handoffRecentRideCount?: number;
  handoffDistanceKm?: number;
  handoffOriginRegion?: string;
  handoffTag?: string;
  handoffMonth?: string;
  handoffWindowDays?: number;
  handoffSuggestedHours?: number;
}): string {
  const searchParams = new URLSearchParams();
  searchParams.set("intent", params.intent);
  searchParams.set("seedQuery", params.seedQuery);
  searchParams.set("handoffSource", params.handoffSource);
  searchParams.set("handoffActionKey", params.handoffActionKey);
  searchParams.set("handoffScene", params.handoffScene);
  if (params.handoffStatus) {
    searchParams.set("handoffStatus", params.handoffStatus);
  }
  if (params.handoffRideCount != null) {
    searchParams.set("handoffRideCount", String(params.handoffRideCount));
  }
  if (params.handoffWeeklyStreak != null) {
    searchParams.set("handoffWeeklyStreak", String(params.handoffWeeklyStreak));
  }
  if (params.handoffRecentRideCount != null) {
    searchParams.set("handoffRecentRideCount", String(params.handoffRecentRideCount));
  }
  if (params.handoffDistanceKm != null) {
    searchParams.set("handoffDistanceKm", String(params.handoffDistanceKm));
  }
  if (params.handoffOriginRegion) {
    searchParams.set("handoffOriginRegion", params.handoffOriginRegion);
  }
  if (params.handoffTag) {
    searchParams.set("handoffTag", params.handoffTag);
  }
  if (params.handoffMonth) {
    searchParams.set("handoffMonth", params.handoffMonth);
  }
  if (params.handoffWindowDays != null) {
    searchParams.set("handoffWindowDays", String(params.handoffWindowDays));
  }
  if (params.handoffSuggestedHours != null) {
    searchParams.set("handoffSuggestedHours", String(params.handoffSuggestedHours));
  }
  return `/?${searchParams.toString()}`;
}

function suggestedDurationHoursForPlannerHandoff(
  actionKey: string,
  suggestedScene: "city_ride" | "weekend_trip",
): number {
  if (suggestedScene === "weekend_trip") {
    return 3.5;
  }
  if (actionKey === "take_recovery_window") {
    return 1;
  }
  return 2;
}
