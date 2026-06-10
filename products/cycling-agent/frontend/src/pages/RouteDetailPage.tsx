/*
 * CN: 路线详情页，展示模板路线的时间窗、补给、撤退和关键爬坡信息。
 * EN: Route detail page showing route time windows, supplies, bailouts, and key climb segments.
 */

import { useEffect, useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";

import ThemeToggle from "../components/ThemeToggle";
import { getRouteDetail, type RouteDetail } from "../features/planner/api";

type RouteState = {
  route?: {
    routeCode: string;
    routeName: string;
    distanceKm: number;
    elevationGainM: number;
    estimatedDurationHours: number;
    riskLevel: string;
    summaryReason: string;
  };
};

export default function RouteDetailPage() {
  const { routeCode = "" } = useParams();
  const location = useLocation();
  const state = location.state as RouteState | null;
  const routeSummary = state?.route;
  const [routeDetail, setRouteDetail] = useState<RouteDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    void getRouteDetail(routeCode)
      .then((detail) => {
        if (!active) {
          return;
        }
        setRouteDetail(detail);
        setLoading(false);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setError("路线详情暂时不可用，请稍后再试。");
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [routeCode]);

  if (loading) {
    return (
      <main className="page-shell">
        <ThemeToggle />
        <article className="state-panel">
          <h1>路线详情</h1>
          <p>正在加载路线细节与补给信息。</p>
        </article>
      </main>
    );
  }

  if (error || !routeDetail) {
    return (
      <main className="page-shell">
        <ThemeToggle />
        <article className="state-panel">
          <h1>路线详情</h1>
          <p>{error ?? "当前没有可展示的路线数据，请返回结果页重新选择。"}</p>
          <Link to="/">返回首页</Link>
          <p>Route code: {routeCode}</p>
        </article>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <ThemeToggle />
      <article className="detail-panel detail-panel-primary">
        <div className="section-heading">
          <p className="section-kicker">Route Detail</p>
          <h1>{routeDetail.route_name}</h1>
        </div>
        <p className="summary-copy">{routeSummary?.summaryReason ?? routeDetail.route_notes ?? "杭州本地样板路线详情。"}</p>
        <div className="metric-row">
          <span>{routeDetail.distance_km} km</span>
          <span>{routeDetail.elevation_gain_m} m</span>
          <span>{routeDetail.estimated_duration_hours} h</span>
          <span>难度：{routeDetail.difficulty_level}</span>
          <span>风险：{routeSummary?.riskLevel ?? "见规划结果"}</span>
        </div>
        <div className="risk-grid">
          <span>起点：{routeDetail.start_point_name ?? "-"}</span>
          <span>终点：{routeDetail.end_point_name ?? "-"}</span>
          <span>路线形态：{routeDetail.loop_type ?? "-"}</span>
          <span>路面：{routeDetail.surface_type ?? "-"}</span>
          <span>补给分：{routeDetail.supply_score}</span>
          <span>返程难度：{routeDetail.return_difficulty_score}</span>
        </div>
      </article>

      <section className="success-layout">
        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Time Window</p>
            <h3>推荐时间与规避时段</h3>
          </div>
          <p>推荐出发：{routeDetail.best_time_slots.join(" / ") || "-"}</p>
          <p>尽量避开：{routeDetail.avoid_time_slots.join(" / ") || "-"}</p>
          <p>适骑季节：{routeDetail.season_tags.join(" / ") || "-"}</p>
        </article>

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Supply</p>
            <h3>补给点</h3>
          </div>
          <ul className="detail-list">
            {routeDetail.supply_points.map((point) => (
              <li key={`${point.name}-${point.km_mark}`}>
                {point.km_mark} km: {point.name} ({point.type})
              </li>
            ))}
          </ul>
        </article>

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Bailout</p>
            <h3>缩短与撤退方案</h3>
          </div>
          <ul className="detail-list">
            {routeDetail.bailout_options.map((option) => (
              <li key={`${option.name}-${option.km_mark}`}>
                {option.name}: {option.reason}
              </li>
            ))}
          </ul>
        </article>

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Climb Segments</p>
            <h3>关键路段</h3>
          </div>
          <ul className="detail-list">
            {routeDetail.climb_segments.length > 0 ? (
              routeDetail.climb_segments.map((segment) => (
                <li key={segment.name}>
                  {segment.name}: {segment.distance_km} km / {segment.elevation_gain_m} m / {segment.gradient_note}
                </li>
              ))
            ) : (
              <li>当前路线没有需要特别提示的连续爬坡段。</li>
            )}
          </ul>
        </article>
      </section>

      <p className="hero-link-row">
        <Link to="/">返回规划页</Link>
      </p>
    </main>
  );
}
