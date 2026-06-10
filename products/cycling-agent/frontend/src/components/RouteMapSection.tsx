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
        <span>接驳：{formatMetric(routeMap.approach_distance_km)} km / {formatMetric(routeMap.approach_duration_hours)} h</span>
        <span>主路线：{formatMetric(routeMap.template_distance_km)} km / {formatMetric(routeMap.template_duration_hours)} h</span>
      </div>
      {status !== "ready" ? (
        <div className="route-map-fallback">
          <p>{status === "loading" ? "正在加载高德地图..." : fallbackMessage}</p>
          <ul className="detail-list">
            <li>你的出发点：{userStartPoint.name ?? "-"}</li>
            <li>主路线起点：{templateStartPoint.name ?? "-"}</li>
            <li>终点：{routeMap.end_point.name ?? "-"}</li>
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
        地图来源：{routeMap.provider_name} / {routeMap.fact_source}
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
