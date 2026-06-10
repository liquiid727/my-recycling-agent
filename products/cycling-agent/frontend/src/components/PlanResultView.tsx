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
  if (result.status === "no_match") {
    const showPopularFallback = shouldShowPopularRouteFallback(result);
    return (
      <div className="success-layout">
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
        {result.decision_summary ? <DecisionSummaryPanel summary={result.decision_summary} /> : null}
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
      {result.decision_summary ? <DecisionSummaryPanel summary={result.decision_summary} /> : null}
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

function DecisionSummaryPanel({ summary }: { summary: NonNullable<RidePlanResponse["decision_summary"]> }) {
  return (
    <article className="detail-panel detail-panel-primary">
      <div className="section-heading">
        <p className="section-kicker">先说结论</p>
        <h2>{summary.decision_title}</h2>
      </div>
      <p className="summary-copy">{summary.decision_reason}</p>
      <p className="risk-pill">结论：{summary.go_decision}</p>
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
        {toolTrace.map((item) => (
          <li key={`${item.stage_name}-${item.provider_name}`}>
            {item.stage_name}: {item.provider_name} / {item.status} / {item.summary}
          </li>
        ))}
      </ul>
    </article>
  );
}
