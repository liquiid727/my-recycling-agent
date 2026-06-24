/*
 * CN: 路线图区域默认展示路线关键点，用户主动请求后才加载高德 JS SDK。
 * EN: Route map section that shows route key points first and loads AMap JS SDK on demand.
 */

import { useEffect, useRef, useState } from "react";

import type { RouteMap } from "../features/planner/api";

type Props = {
  routeMap: RouteMap;
};

type MapStatus = "idle" | "loading" | "ready" | "fallback";

declare global {
  interface Window {
    AMap?: {
      Map: new (element: HTMLDivElement, options: Record<string, unknown>) => unknown;
      Polyline?: new (options: Record<string, unknown>) => { setMap: (map: unknown) => void };
      Marker?: new (options: Record<string, unknown>) => { setMap: (map: unknown) => void };
    };
  }
}

export default function RouteMapSection({ routeMap }: Props) {
  const mapRef = useRef<HTMLDivElement | null>(null);
  const [status, setStatus] = useState<MapStatus>("idle");
  const [mapRequested, setMapRequested] = useState(false);
  const amapKey = getAmapKey();
  const fallbackMessage = !amapKey
    ? "未配置高德地图 JS Key，当前展示路线关键点。"
    : "高德地图加载失败，当前展示路线关键点。";
  const userStartPoint = routeMap.user_start_point ?? routeMap.start_point;
  const templateStartPoint = routeMap.template_start_point ?? routeMap.start_point;
  const hasTemplateLayer = Boolean(routeMap.template);
  const hasLiveLayer = Boolean(routeMap.live);
  const hasApproachLayer = routeMap.approach_distance_km != null && routeMap.approach_duration_hours != null;
  const summaryRows = buildSummaryRows(routeMap);

  useEffect(() => {
    if (!mapRequested) {
      return;
    }
    const key = getAmapKey();
    if (!key || !mapRef.current) {
      setStatus("fallback");
      return;
    }

    loadAmapScript(key)
      .then(() => {
        if (!window.AMap || !mapRef.current) {
          setStatus("fallback");
          return;
        }
        const center = buildCenter(routeMap);
        const map = new window.AMap.Map(mapRef.current, { zoom: 12, center });
        if (routeMap.polyline_available && routeMap.polyline.length > 1 && window.AMap.Polyline) {
          new window.AMap.Polyline({
            path: routeMap.polyline.map((point) => [point.longitude, point.latitude]),
            strokeColor: "#0F766E",
            strokeWeight: 6
          }).setMap(map);
        }
        if (window.AMap.Marker) {
          new window.AMap.Marker({ position: center, title: userStartPoint.name ?? routeMap.route_name }).setMap(map);
        }
        setStatus("ready");
      })
      .catch(() => setStatus("fallback"));
  }, [mapRequested, routeMap, userStartPoint.name]);

  function handleLoadMap() {
    setMapRequested(true);
    setStatus("loading");
  }

  return (
    <article className="detail-panel route-map-panel">
      <div className="section-heading">
        <p className="section-kicker">Route Map</p>
        <h3>路线图</h3>
      </div>
      {mapRequested && amapKey ? (
        <div ref={mapRef} className="route-map-canvas" aria-label={`${routeMap.route_name}地图`} />
      ) : (
        <div className="route-map-placeholder">
          <p>默认不加载地图组件，先展示路线关键点和距离摘要。</p>
          <button type="button" className="secondary-button" onClick={handleLoadMap}>
            加载地图
          </button>
        </div>
      )}
      <div className="risk-grid">
        <span>从你的出发点开始</span>
        <span>总量：{formatMetric(routeMap.total_distance_km)} km / {formatMetric(routeMap.total_duration_hours)} h</span>
        {summaryRows.map((row) => (
          <span key={row.label}>
            {row.label}：{formatMetric(row.distanceKm)} km / {formatMetric(row.durationHours)} h
          </span>
        ))}
      </div>
      {status !== "ready" ? (
        <div className="route-map-fallback">
          <p>{status === "loading" ? "正在加载高德地图..." : fallbackMessage}</p>
          <ul className="detail-list">
            <li>你的出发点：{userStartPoint.name ?? "-"}</li>
            {hasTemplateLayer ? <li>模板起点：{templateStartPoint.name ?? "-"}</li> : null}
            <li>{hasTemplateLayer ? "路线终点" : "动态路线终点"}：{routeMap.end_point.name ?? "-"}</li>
            {hasLiveLayer ? <li>实时路径来源：{describeLiveLayer(routeMap)}</li> : null}
            {hasApproachLayer && hasTemplateLayer ? (
              <li>接驳口径：先按你的出发点接入，再叠加模板路线总量。</li>
            ) : null}
            {routeMap.supply_points.map((point) => (
              <li key={`${point.name}-${point.km_mark}`}>
                补给：{point.km_mark} km / {point.name} ({point.type})
              </li>
            ))}
            {routeMap.bailout_options.map((option) => (
              <li key={`${option.name}-${option.km_mark}`}>
                撤退：{option.name} / {option.reason}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <p className="summary-copy">
        路线口径：{describeMetricSource(routeMap)}
      </p>
    </article>
  );
}

function getAmapKey(): string | undefined {
  return import.meta.env.VITE_AMAP_JS_API_KEY;
}

function buildCenter(routeMap: RouteMap): [number, number] {
  const userStartPoint = routeMap.user_start_point ?? routeMap.start_point;
  if (userStartPoint.longitude && userStartPoint.latitude) {
    return [userStartPoint.longitude, userStartPoint.latitude];
  }
  const firstPoint = routeMap.polyline[0];
  if (firstPoint) {
    return [firstPoint.longitude, firstPoint.latitude];
  }
  return [120.2103, 30.2064];
}

function formatMetric(value: number | null | undefined): string {
  return value == null ? "-" : String(value);
}

function buildSummaryRows(routeMap: RouteMap): Array<{ label: string; distanceKm?: number | null; durationHours?: number | null }> {
  const rows: Array<{ label: string; distanceKm?: number | null; durationHours?: number | null }> = [];
  const shouldShowApproach =
    Boolean(routeMap.template) ||
    (routeMap.approach_distance_km ?? 0) > 0 ||
    (routeMap.approach_duration_hours ?? 0) > 0;
  if (shouldShowApproach) {
    rows.push({
      label: "接驳段",
      distanceKm: routeMap.approach_distance_km,
      durationHours: routeMap.approach_duration_hours
    });
  }
  if (routeMap.template) {
    rows.push({
      label: "模板骨架",
      distanceKm: routeMap.template.distance_km ?? routeMap.template_distance_km,
      durationHours: routeMap.template.duration_hours ?? routeMap.template_duration_hours
    });
  } else if (routeMap.live || routeMap.resolved?.metric_source === "dynamic-live") {
    rows.push({
      label: "动态路线",
      distanceKm: routeMap.resolved?.distance_km ?? routeMap.total_distance_km,
      durationHours: routeMap.resolved?.estimated_duration_hours ?? routeMap.total_duration_hours
    });
  }
  return rows;
}

function describeMetricSource(routeMap: RouteMap): string {
  const metricSource = routeMap.resolved?.metric_source;
  if (metricSource === "dynamic-live") {
    return "动态路线实时结果";
  }
  if (metricSource === "template-plus-approach") {
    return "模板骨架 + 出发点接驳";
  }
  if (metricSource === "template-plus-live") {
    return "模板骨架 + 实时路径";
  }
  return "模板路线估算";
}

function describeLiveLayer(routeMap: RouteMap): string {
  const factSource = routeMap.live?.fact_source ?? routeMap.fact_source;
  if (factSource === "amap-dynamic") {
    return "基于实时动态路径生成";
  }
  if (factSource === "amap" || factSource === "amap-approach") {
    return "高德路径结果";
  }
  if (factSource === "local-approach") {
    return "本地接驳估算";
  }
  return routeMap.provider_name;
}

function loadAmapScript(key: string): Promise<void> {
  if (window.AMap) {
    return Promise.resolve();
  }
  const existing = document.querySelector<HTMLScriptElement>("script[data-amap-js-sdk]");
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("amap-js-load-failed")), { once: true });
    });
  }
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${encodeURIComponent(key)}`;
    script.async = true;
    script.dataset.amapJsSdk = "true";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("amap-js-load-failed"));
    document.head.appendChild(script);
  });
}
