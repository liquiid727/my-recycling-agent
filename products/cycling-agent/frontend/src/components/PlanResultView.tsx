/*
 * CN: 规划结果组合视图，把主推荐、天气、风险、路书和备选路线组装到结果页。
 * EN: Composed plan-result view that assembles recommendation, weather, risk, roadbook, and alternatives.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import AlternativeRouteList from "./AlternativeRouteList";
import InputSummaryCard from "./InputSummaryCard";
import RecommendationCard from "./RecommendationCard";
import RiskBreakdownCard from "./RiskBreakdownCard";
import RouteMapSection from "./RouteMapSection";
import RoadbookSection from "./RoadbookSection";
import WeatherStatusCard from "./WeatherStatusCard";
import { getRecommendedRoutes, type RecommendedRoute, type RidePlanResponse } from "../features/planner/api";

type Props = {
  result: RidePlanResponse;
};

export default function PlanResultView({ result }: Props) {
  const displayDecisionSummary = result.decision_summary
    ? buildDisplayDecisionSummary(result.decision_summary, result.ride_readiness)
    : null;
  if (result.status === "no_match") {
    const showPopularFallback = shouldShowPopularRouteFallback(result);
    return (
      <div className="success-layout">
        {result.ride_readiness ? <RideReadinessPanel readiness={result.ride_readiness} /> : null}
        <article className="detail-panel state-error">
          <h3>当前没有合适路线</h3>
          <p>{result.no_match_reason ?? "请调整时长、出发区域或骑行偏好后重试。"}</p>
          {result.clarification_prompt ? <p>{result.clarification_prompt}</p> : null}
        </article>
        {showPopularFallback ? <PopularRouteFallback result={result} /> : null}
      </div>
    );
  }

  const recommendation = {
    routeName: result.recommended_plan.route_name,
    distanceKm: result.recommended_plan.distance_km,
    elevationGainM: result.recommended_plan.elevation_gain_m,
    estimatedDurationHours: result.recommended_plan.estimated_duration_hours,
    riskLevel: result.recommended_plan.risk_level,
    summaryReason: result.recommended_plan.summary_reason
  };

  const alternatives =
    result.alternatives.map((plan) => ({
      routeName: plan.route_name,
      distanceKm: plan.distance_km,
      elevationGainM: plan.elevation_gain_m,
      estimatedDurationHours: plan.estimated_duration_hours,
      riskLevel: plan.risk_level,
      summaryReason: plan.summary_reason
    })) ?? [];

  const roadbook = result.roadbook
    ? {
        departureWindow: result.roadbook.departure_window,
        keySegments: result.roadbook.key_segments,
        supplyAdvice: result.roadbook.supply_advice,
        mitigationAdvice: result.roadbook.mitigation_advice,
        shortenOptions: result.roadbook.shorten_options,
        poiSummary: result.roadbook.poi_summary,
        routeContext: result.roadbook.route_context
      }
    : null;

  const parsedConstraints = result.parsed_constraints ?? null;
  const clarificationPrompt = result.clarification_prompt;
  const weatherSnapshot = result.weather_snapshot
    ? {
        forecastDate: result.weather_snapshot.forecast_date,
        temperatureMin: result.weather_snapshot.temperature_min,
        temperatureMax: result.weather_snapshot.temperature_max,
        precipitationProbability: result.weather_snapshot.precipitation_probability,
        windSpeed: result.weather_snapshot.wind_speed,
        windDirection: result.weather_snapshot.wind_direction,
        weatherSummary: result.weather_snapshot.weather_summary,
        providerName: result.weather_snapshot.provider_name
      }
    : null;
  const fallbackReason = result.fallback_reason ?? [];
  const toolTrace = result.tool_trace ?? [];

  if (result.planning_mode === "nearby_trip" && result.recommended_trip) {
    return (
      <div className="success-layout">
        {displayDecisionSummary ? <DecisionSummaryPanel summary={displayDecisionSummary} readinessLinked={Boolean(result.ride_readiness)} /> : null}
        {result.ride_readiness ? <RideReadinessPanel readiness={result.ride_readiness} /> : null}
        {result.input_summary ? <InputSummaryCard summary={result.input_summary} /> : null}
        {weatherSnapshot ? <WeatherStatusCard snapshot={weatherSnapshot} fallbackReason={fallbackReason} /> : null}
        <article className="detail-panel detail-panel-primary">
          <div className="section-heading">
            <p className="section-kicker">Weekend Trip</p>
            <h2>{result.recommended_trip.trip_name}</h2>
          </div>
          <p className="summary-copy">{result.recommended_trip.why_recommended}</p>
          <div className="metric-row">
            <span>{result.recommended_trip.destination_name}</span>
            <span>{result.recommended_trip.total_distance_km} km</span>
            <span>{result.recommended_trip.ride_duration_hours} h 骑行</span>
            <span>{result.recommended_trip.total_duration_hours} h 总时长</span>
          </div>
          <p className="risk-pill">风险：{result.recommended_trip.risk_level}</p>
          <p className="summary-copy">{result.recommended_trip.suitable_for}</p>
          <p className="summary-copy">{result.recommended_trip.stay_suggestion}</p>
          {result.recommended_trip.lodging_plan ? <p className="summary-copy">住宿：{result.recommended_trip.lodging_plan}</p> : null}
          {result.recommended_trip.weather_window_notes ? <p className="summary-copy">天气窗口：{result.recommended_trip.weather_window_notes}</p> : null}
          {(result.recommended_trip.equipment_advice ?? []).length > 0 ? (
            <ul className="detail-list">
              {(result.recommended_trip.equipment_advice ?? []).map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </article>

        {result.recommended_trip.source_meta ? (
          <TripSourceMetaPanel
            sourceMeta={result.recommended_trip.source_meta}
            destinationName={result.recommended_trip.destination_name}
          />
        ) : null}

        {result.trip_rhythm ? (
          <article className="detail-panel">
            <div className="section-heading">
              <p className="section-kicker">Trip Rhythm</p>
              <h3>节奏安排</h3>
            </div>
            <ul className="detail-list">
              {result.trip_rhythm.segments.map((segment) => (
                <li key={`${segment.stage}-${segment.time_window}`}>
                  <strong>{segment.stage}</strong>
                  {" · "}
                  {segment.time_window}
                  {" · "}
                  {segment.description}
                </li>
              ))}
            </ul>
          </article>
        ) : null}

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Return / Fallback</p>
            <h3>返程和撤退</h3>
          </div>
          <ul className="detail-list">
            {result.recommended_trip.return_options.map((option) => (
              <li key={option}>{option}</li>
            ))}
          </ul>
          {result.trip_risks ? <p className="summary-copy">{result.trip_risks.fallback_plan}</p> : null}
        </article>

        {result.trip_risks ? (
          <article className="detail-panel">
            <div className="section-heading">
              <p className="section-kicker">Risk First</p>
              <h3>风险与替代</h3>
            </div>
            <ul className="detail-list">
              {result.trip_risks.risk_items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        ) : null}

        {(result.trip_alternatives ?? []).length > 0 ? (
          <article className="detail-panel">
            <div className="section-heading">
              <p className="section-kicker">Alternatives</p>
              <h3>备选周边游</h3>
            </div>
            <ul className="detail-list">
              {(result.trip_alternatives ?? []).map((trip) => (
                <li key={trip.trip_no}>
                  {trip.trip_name}: {trip.destination_name} / {trip.total_duration_hours} h / {trip.risk_level}
                  {trip.source_meta ? `。${formatTripAlternativeSourceMeta(trip.source_meta)}` : ""}
                </li>
              ))}
            </ul>
          </article>
        ) : null}

        {toolTrace.length > 0 ? <DebugTracePanel toolTrace={toolTrace} /> : null}
        {result.route_map ? <RouteMapSection routeMap={result.route_map} /> : null}
      </div>
    );
  }

  return (
    <div className="success-layout">
      {displayDecisionSummary ? <DecisionSummaryPanel summary={displayDecisionSummary} readinessLinked={Boolean(result.ride_readiness)} /> : null}
      {result.ride_readiness ? <RideReadinessPanel readiness={result.ride_readiness} /> : null}
      {result.input_summary ? <InputSummaryCard summary={result.input_summary} /> : null}
      {clarificationPrompt ? (
        <article className="detail-panel state-error">
          <h3>建议补充信息</h3>
          <p>{clarificationPrompt}</p>
        </article>
      ) : null}
      {weatherSnapshot ? <WeatherStatusCard snapshot={weatherSnapshot} fallbackReason={fallbackReason} /> : null}
      <Link
        className="card-link"
        to={`/routes/${result.recommended_plan.route_code}`}
        state={{ route: recommendation }}
      >
        <RecommendationCard plan={recommendation} />
      </Link>
      {result.roadbook?.risk_summary ? <RiskBreakdownCard risk={result.roadbook.risk_summary} /> : null}
      {result.route_map ? <RouteMapSection routeMap={result.route_map} /> : null}
      {alternatives.length > 0 ? <AlternativeRouteList plans={alternatives} /> : null}
      {roadbook ? <RoadbookSection roadbook={roadbook} /> : null}
      {parsedConstraints || toolTrace.length > 0 ? <DebugDetailsPanel parsedConstraints={parsedConstraints} toolTrace={toolTrace} /> : null}
    </div>
  );
}

function shouldShowPopularRouteFallback(result: RidePlanResponse): boolean {
  const fallbackReason = result.fallback_reason ?? [];
  const toolTrace = result.tool_trace ?? [];
  return (
    fallbackReason.includes("nearby-route-discovery-unavailable") ||
    toolTrace.some(
      (stage) =>
        stage.stage_name === "nearby_route_discovery" &&
        stage.status === "fallback" &&
        stage.fallback_reason === "nearby-route-discovery-unavailable",
    )
  );
}

function PopularRouteFallback({ result }: Props) {
  const [routes, setRoutes] = useState<RecommendedRoute[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");

  useEffect(() => {
    let active = true;
    void getRecommendedRoutes({
      cityCode: result.input_summary?.city_code ?? "hangzhou",
      originRegion: result.input_summary?.origin_region ?? null,
      rideStyle: typeof result.parsed_constraints?.ride_style === "string" ? result.parsed_constraints.ride_style : null
    })
      .then((items) => {
        if (!active) {
          return;
        }
        setRoutes(items.slice(0, 3));
        setStatus("ready");
      })
      .catch(() => {
        if (active) {
          setStatus("error");
        }
      });
    return () => {
      active = false;
    };
  }, [result.input_summary?.city_code, result.input_summary?.origin_region, result.parsed_constraints]);

  return (
    <article className="detail-panel">
      <div className="section-heading">
        <p className="section-kicker">Fallback Routes</p>
        <h3>不妨看看最近的热门和精品路线吧</h3>
      </div>
      <p className="summary-copy">这些路线不是本次动态规划结果，只在动态路线服务暂时不可用时作为浏览参考。</p>
      {status === "loading" ? <p className="summary-copy">正在加载热门路线...</p> : null}
      {status === "error" ? <p className="summary-copy">热门路线暂时也加载失败了，请稍后再试。</p> : null}
      {status === "ready" && routes.length === 0 ? <p className="summary-copy">当前没有可展示的热门路线。</p> : null}
      {routes.length > 0 ? (
        <ul className="detail-list">
          {routes.map((route) => (
            <li key={route.route_code}>
              <Link to={`/routes/${route.route_code}`}>
                {route.route_name}
              </Link>
              {" · "}
              {route.distance_km} km / {route.estimated_duration_hours} h / {route.difficulty_level}
            </li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}

function DecisionSummaryPanel({
  summary,
  readinessLinked
}: {
  summary: NonNullable<RidePlanResponse["decision_summary"]>;
  readinessLinked: boolean;
}) {
  return (
    <article className="detail-panel detail-panel-primary">
      <div className="section-heading">
        <p className="section-kicker">先说结论</p>
        <h2>{summary.decision_title}</h2>
      </div>
      <p className="summary-copy">{summary.decision_reason}</p>
      <p className="risk-pill">结论：{summary.go_decision}</p>
      {readinessLinked ? <p className="body-copy">骑前身体和天气状态已经在下方单独展开。</p> : null}
      {summary.confidence_notes.length > 0 ? (
        <ul className="detail-list">
          {summary.confidence_notes.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      {summary.equipment_advice.length > 0 ? (
        <ul className="detail-list">
          {summary.equipment_advice.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
    </article>
  );
}

function RideReadinessPanel({ readiness }: { readiness: NonNullable<RidePlanResponse["ride_readiness"]> }) {
  const cautionFlags = readiness.caution_flags ?? [];
  return (
    <article className="detail-panel">
      <div className="section-heading">
        <p className="section-kicker">Ride Readiness</p>
        <h3>骑前状态判断</h3>
      </div>
      <div className="metric-row">
        <span className="pill-tag">建议：{formatReadinessStatus(readiness.status)}</span>
        <span className="pill-tag">强度：{formatIntensity(readiness.recommended_intensity)}</span>
        <span className="pill-tag">准备度：{Math.round(readiness.score * 100)} 分</span>
      </div>
      <p className="summary-copy">{readiness.summary}</p>
      {readiness.reasons.length > 0 ? (
        <ul className="detail-list">
          {readiness.reasons.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      {cautionFlags.length > 0 ? (
        <p className="body-copy">注意项：{cautionFlags.map(formatCautionFlag).join(" / ")}</p>
      ) : null}
    </article>
  );
}

function formatReadinessStatus(status: NonNullable<RidePlanResponse["ride_readiness"]>["status"]): string {
  if (status === "go") {
    return "可以出发";
  }
  if (status === "light") {
    return "轻一点骑";
  }
  return "先休息";
}

function formatIntensity(intensity: NonNullable<RidePlanResponse["ride_readiness"]>["recommended_intensity"]): string {
  if (intensity === "steady") {
    return "正常节奏";
  }
  if (intensity === "light") {
    return "恢复节奏";
  }
  return "不建议拉强度";
}

function formatCautionFlag(flag: string): string {
  const labelMap: Record<string, string> = {
    heat: "高温",
    cold: "低温",
    rain: "降雨",
    wind: "大风",
    fatigue: "疲劳",
    recovery: "恢复期",
    long_break: "久未骑行",
    low_fitness: "体能保守"
  };
  return labelMap[flag] ?? flag;
}

function TripSourceMetaPanel({
  sourceMeta,
  destinationName
}: {
  sourceMeta: NonNullable<NonNullable<RidePlanResponse["recommended_trip"]>["source_meta"]>;
  destinationName: string;
}) {
  const tripTemplate = sourceMeta.trip_template;
  const destinationTemplate = sourceMeta.destination_template;
  const routeBinding = sourceMeta.route_binding;
  const resolvedMetrics = sourceMeta.resolved_metrics;

  return (
    <article className="detail-panel">
      <div className="section-heading">
        <p className="section-kicker">Binding</p>
        <h3>这次怎么承接</h3>
      </div>
      <ul className="detail-list">
        {tripTemplate?.trip_no ? (
          <li>
            周末骨架：{tripTemplate.trip_no}
            {tripTemplate.duration_bucket ? ` / ${formatDurationBucket(tripTemplate.duration_bucket)}` : ""}
          </li>
        ) : null}
        {destinationTemplate ? (
          <li>
            目的地模板：{destinationTemplate.destination_no ?? destinationName}
            {destinationTemplate.destination_type ? ` / ${destinationTemplate.destination_type}` : ""}
          </li>
        ) : null}
        {routeBinding?.selected_route_name ? (
          <li>
            实际承接路线：{routeBinding.selected_route_name}
            {routeBinding.selected_route_code ? ` / ${routeBinding.selected_route_code}` : ""}
            {routeBinding.selected_route_source ? ` / ${formatRouteBindingSource(routeBinding.selected_route_source)}` : ""}
          </li>
        ) : null}
        {resolvedMetrics?.metric_source ? (
          <li>总量口径：{formatTripMetricSource(resolvedMetrics.metric_source)}</li>
        ) : null}
        {routeBinding?.audit_summary ? <li>审计摘要：{routeBinding.audit_summary}</li> : null}
        {routeBinding ? (
          <li>
            匹配方式：
            {routeBinding.is_template_route_match
              ? "沿用原 trip skeleton 绑定的推荐路线。"
              : "没有强行沿用模板路线，改用更贴合这次出发点和约束的路线去承接。"}
          </li>
        ) : null}
      </ul>
    </article>
  );
}

function formatDurationBucket(durationBucket: string): string {
  const labelMap: Record<string, string> = {
    evening: "夜骑",
    half_day: "半天",
    one_day: "一天",
    two_day: "两天",
    three_day: "三天"
  };
  return labelMap[durationBucket] ?? durationBucket;
}

function formatRouteBindingSource(source: string): string {
  const labelMap: Record<string, string> = {
    dynamic_nearby: "动态近场路线",
    "amap-dynamic": "实时动态路径",
    template: "模板路线",
    "template+amap": "模板 + 实时路径",
    amap: "高德路径结果",
    "template+local-approach": "模板 + 本地接驳"
  };
  return labelMap[source] ?? source;
}

function formatTripMetricSource(source: string): string {
  const labelMap: Record<string, string> = {
    "dynamic-live": "动态路线实时结果",
    "template-plus-approach": "模板骨架 + 出发点接驳",
    "template-plus-live": "模板骨架 + 实时路径",
    template: "模板路线估算"
  };
  return labelMap[source] ?? source;
}

function formatTripAlternativeSourceMeta(
  sourceMeta: NonNullable<NonNullable<RidePlanResponse["recommended_trip"]>["source_meta"]>
): string {
  const routeBinding = sourceMeta.route_binding;
  const tripTemplate = sourceMeta.trip_template;
  const routeLabel = routeBinding?.selected_route_name ?? routeBinding?.selected_route_code ?? "未标注路线";
  const matchLabel = routeBinding?.is_template_route_match ? "沿用原模板路线" : "改用更贴当前条件的路线";
  const durationLabel = tripTemplate?.duration_bucket ? formatDurationBucket(tripTemplate.duration_bucket) : null;
  if (durationLabel) {
    return `${durationLabel}骨架，${routeLabel}承接，${matchLabel}`;
  }
  return `${routeLabel}承接，${matchLabel}`;
}

function buildDisplayDecisionSummary(
  summary: NonNullable<RidePlanResponse["decision_summary"]>,
  rideReadiness: RidePlanResponse["ride_readiness"] | null | undefined
): NonNullable<RidePlanResponse["decision_summary"]> {
  if (!rideReadiness) {
    return summary;
  }

  return {
    ...summary,
    decision_reason: stripReadinessReason(summary.decision_reason),
    confidence_notes: summary.confidence_notes.filter((item) => !item.startsWith("状态："))
  };
}

function stripReadinessReason(reason: string): string {
  const separator = " 当前身体和天气状态判断：";
  const index = reason.indexOf(separator);
  if (index === -1) {
    return reason;
  }
  return reason.slice(0, index).trim();
}

function DebugDetailsPanel({
  parsedConstraints,
  toolTrace
}: {
  parsedConstraints: Record<string, unknown> | null;
  toolTrace: RidePlanResponse["tool_trace"];
}) {
  return (
    <details className="debug-details">
      <summary>查看识别和服务调用细节</summary>
      {parsedConstraints ? <pre className="parsed-json">{JSON.stringify(parsedConstraints, null, 2)}</pre> : null}
      {toolTrace.length > 0 ? <DebugTracePanel toolTrace={toolTrace} /> : null}
    </details>
  );
}

function DebugTracePanel({ toolTrace }: { toolTrace: RidePlanResponse["tool_trace"] }) {
  return (
    <article className="detail-panel">
      <div className="section-heading">
        <p className="section-kicker">Debug Trace</p>
        <h3>服务调用细节</h3>
      </div>
      <ul className="detail-list">
        {toolTrace.map((item, index) => (
          <li key={`${item.stage_name}-${item.provider_name}-${index}`}>
            {item.stage_name}: {item.provider_name} / {item.status} / {item.summary}
          </li>
        ))}
      </ul>
    </article>
  );
}
