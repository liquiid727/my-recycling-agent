/*
 * CN: 输入摘要卡片，展示本次规划实际采用的时间、地点和默认值。
 * EN: Input summary card showing the actual time, location, and defaults used for this plan.
 */

import type { InputSummary } from "../features/planner/api";

type Props = {
  summary: InputSummary;
};

export default function InputSummaryCard({ summary }: Props) {
  const dateTime = [summary.target_date, summary.departure_time].filter(Boolean).join(" ");
  return (
    <article className="detail-panel">
      <div className="section-heading">
        <p className="section-kicker">Input Summary</p>
        <h3>本次输入</h3>
      </div>
      <div className="risk-grid">
        <span>场景：{summary.planning_scene === "weekend_trip" || summary.planning_mode === "nearby_trip" ? "周末骑行出行" : "今晚 / 下午骑一下"}</span>
        <span>时间：{dateTime || "-"}</span>
        <span>城市：{summary.city_code}</span>
        <span>区域：{summary.origin_region ?? "-"}</span>
        <span>出发点：{summary.start_point ?? "-"}</span>
        <span>时长：{summary.available_hours ?? "-"} h</span>
        <span>距离：{summary.target_distance_km ?? "-"} km</span>
        <span>体力：{summary.fitness_level ?? "-"}</span>
        <span>风格：{summary.ride_style ?? "-"}</span>
        <span>爬坡：{summary.slope_tolerance ?? "-"}</span>
        <span>偏好：{summary.priority ?? "-"}</span>
        {summary.planning_mode === "nearby_trip" ? (
          <>
            <span>出行：{formatDurationBucket(summary.duration_bucket)}</span>
            <span>目的地：{(summary.destination_preferences ?? []).join(" / ") || "-"}</span>
            <span>返程：{summary.return_preference ?? "-"}</span>
            <span>过夜：{summary.overnight_preference ?? "-"}</span>
            <span>住宿：{summary.lodging_preference ?? "-"}</span>
          </>
        ) : null}
      </div>
      {summary.defaults_applied.length > 0 ? (
        <p className="summary-copy">使用默认值：{summary.defaults_applied.join(" / ")}</p>
      ) : null}
    </article>
  );
}

function formatDurationBucket(bucket: InputSummary["duration_bucket"]) {
  if (bucket === "evening") return "晚上";
  if (bucket === "half_day") return "半天";
  if (bucket === "one_day") return "一天";
  if (bucket === "two_day") return "两天";
  if (bucket === "three_day") return "三天";
  return "-";
}
