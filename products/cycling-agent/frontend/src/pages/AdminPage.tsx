/*
 * CN: 后台页面，维护路线模板、城市策略、风险规则，并查看查询日志。
 * EN: Admin page for maintaining route templates, city strategies, risk rules, and query logs.
 */

import { FormEvent, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import ThemeToggle from "../components/ThemeToggle";

type RouteItem = {
  route_code: string;
  name: string;
  start_point_name?: string;
  best_time_slots?: string[];
  district_tags: string[];
  ride_style_tags: string[];
  distance_km: number;
};

type StrategyItem = {
  city_code: string;
  config_type: string;
  config_key: string;
  config_value: Record<string, unknown>;
  status: string;
};

type QueryLogItem = {
  request_no: string;
  query: string;
  target_date: string;
  recommended_route_name: string;
  created_at: string;
};

type RiskRuleItem = {
  city_code: string;
  rule_key: string;
  rule_value: Record<string, unknown>;
  status: string;
};

type NearbyDestinationItem = {
  destination_no: string;
  city_code: string;
  name: string;
  destination_type: string;
  region_tags: string[];
  suitable_duration: string[];
  stay_duration_minutes: number;
  crowd_level: Record<string, unknown>;
  supply_summary: string;
  public_transport_options: string[];
  stay_suggestion: string;
};

type TripTemplateItem = {
  trip_no: string;
  city_code: string;
  route_template_id: string;
  destination_no: string;
  name: string;
  origin_region_tags: string[];
  total_duration_hours: number;
  ride_duration_hours: number;
  trip_style_tags: string[];
  return_mode_options: string[];
  fallback_plan: string;
};

export default function AdminPage() {
  const [routes, setRoutes] = useState<RouteItem[]>([]);
  const [strategies, setStrategies] = useState<StrategyItem[]>([]);
  const [riskRules, setRiskRules] = useState<RiskRuleItem[]>([]);
  const [nearbyDestinations, setNearbyDestinations] = useState<NearbyDestinationItem[]>([]);
  const [tripTemplates, setTripTemplates] = useState<TripTemplateItem[]>([]);
  const [queryLogs, setQueryLogs] = useState<QueryLogItem[]>([]);
  const [routeForm, setRouteForm] = useState({
    route_code: "HZ-ADMIN-001",
    name: "后台新路线样例",
    start_point_name: "滨江起点",
    start_point_lng: "120.20",
    start_point_lat: "30.20",
    end_point_name: "滨江终点",
    loop_type: "loop",
    district_tags: "滨江",
    ride_style_tags: "relaxed,scenic",
    season_tags: "spring,autumn",
    distance_km: "20",
    elevation_gain_m: "80",
    estimated_duration_hours: "1.8",
    difficulty_level: "easy",
    best_time_slots: "06:30-09:00",
    avoid_time_slots: "12:00-15:00",
    surface_type: "greenway",
    traffic_level: "low",
    supply_score: "7",
    return_difficulty_score: "2",
    scenic_score: "7",
    training_score: "3",
    beginner_friendly: true,
    climb_segments_json: '[{"name":"短坡段","distance_km":1.2,"elevation_gain_m":35,"gradient_note":"短缓坡"}]',
    supply_points_json: '[{"name":"江边便利店","km_mark":8,"type":"便利店"}]',
    bailout_options_json: '[{"name":"中段折返","km_mark":12,"reason":"体感不佳时提前结束"}]',
    holiday_penalty_level: "low",
    weather_sensitivity_json: '{"heat":"medium","rain":"low","crosswind":"low"}',
    route_notes: "后台录入样例。"
  });
  const [strategyForm, setStrategyForm] = useState({
    config_type: "risk_bias",
    config_key: "",
    config_json: '{"district_tags":["西湖"],"crowd_risk_delta":0.2}'
  });
  const [riskRuleForm, setRiskRuleForm] = useState({
    rule_key: "",
    rule_json:
      '{"target":"weather","delta":0.2,"conditions":{"district_tags_any":["龙井"],"temperature_max_gte":30,"weather_sensitivity_heat_in":["high"]}}'
  });
  const [destinationForm, setDestinationForm] = useState({
    destination_no: "DST-ADMIN-001",
    name: "后台江边咖啡点",
    destination_type: "咖啡",
    region_tags: "滨江,钱塘江,江边,咖啡",
    suitable_duration: "half_day",
    stay_duration_minutes: "60",
    crowd_level_json: '{"weekday":"low","weekend":"medium","holiday":"high"}',
    supply_summary: "江边咖啡与便利店充足。",
    public_transport_options: "地铁 6 号线返程",
    stay_suggestion: "到达后补水，停留 45 到 60 分钟。"
  });
  const [tripForm, setTripForm] = useState({
    trip_no: "TRIP-ADMIN-001",
    route_template_id: "HZ-RIVER-001",
    destination_no: "DST-ADMIN-001",
    name: "后台江边咖啡半日骑",
    origin_region_tags: "滨江",
    total_duration_hours: "4.5",
    ride_duration_hours: "2.8",
    trip_style_tags: "half_day,江边,咖啡",
    return_mode_options: "骑回,公共交通",
    fallback_plan: "天气转差时缩短到奥体折返。",
  });

  useEffect(() => {
    void Promise.all([
      fetch("/api/v1/admin/routes").then((res) => res.json()),
      fetch("/api/v1/admin/city-strategy").then((res) => res.json()),
      fetch("/api/v1/admin/risk-rules").then((res) => res.json()),
      fetch("/api/v1/admin/nearby-destinations").then((res) => res.json()),
      fetch("/api/v1/admin/trip-templates").then((res) => res.json()),
      fetch("/api/v1/admin/query-logs").then((res) => res.json())
    ]).then(([routesData, strategyData, riskRuleData, destinationData, tripData, logData]) => {
      setRoutes(routesData);
      setStrategies(strategyData);
      setRiskRules(riskRuleData);
      setNearbyDestinations(destinationData);
      setTripTemplates(tripData);
      setQueryLogs(logData);
    });
  }, []);

  const decisionStrategies = strategies.filter((item) => item.config_type !== "presentation_template");
  const presentationStrategies = strategies.filter((item) => item.config_type === "presentation_template");

  async function submitRoute(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = {
      route_code: routeForm.route_code,
      name: routeForm.name,
      city_code: "hangzhou",
      start_point_name: routeForm.start_point_name,
      start_point_lng: Number(routeForm.start_point_lng),
      start_point_lat: Number(routeForm.start_point_lat),
      end_point_name: routeForm.end_point_name,
      loop_type: routeForm.loop_type,
      district_tags: routeForm.district_tags.split(",").map((item) => item.trim()),
      ride_style_tags: routeForm.ride_style_tags.split(",").map((item) => item.trim()),
      season_tags: routeForm.season_tags.split(",").map((item) => item.trim()),
      distance_km: Number(routeForm.distance_km),
      elevation_gain_m: Number(routeForm.elevation_gain_m),
      estimated_duration_hours: Number(routeForm.estimated_duration_hours),
      difficulty_level: routeForm.difficulty_level,
      best_time_slots: routeForm.best_time_slots.split(",").map((item) => item.trim()),
      avoid_time_slots: routeForm.avoid_time_slots.split(",").map((item) => item.trim()),
      surface_type: routeForm.surface_type,
      traffic_level: routeForm.traffic_level,
      supply_score: Number(routeForm.supply_score),
      return_difficulty_score: Number(routeForm.return_difficulty_score),
      scenic_score: Number(routeForm.scenic_score),
      training_score: Number(routeForm.training_score),
      beginner_friendly: routeForm.beginner_friendly,
      climb_segments: JSON.parse(routeForm.climb_segments_json),
      supply_points: JSON.parse(routeForm.supply_points_json),
      bailout_options: JSON.parse(routeForm.bailout_options_json),
      holiday_penalty_level: routeForm.holiday_penalty_level,
      weather_sensitivity: JSON.parse(routeForm.weather_sensitivity_json),
      route_notes: routeForm.route_notes
    };
    const saved = await fetch("/api/v1/admin/routes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then((res) => res.json());
    setRoutes((current) => [saved, ...current.filter((item) => item.route_code !== saved.route_code)]);
  }

  async function submitStrategy(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = {
      city_code: "hangzhou",
      config_type: strategyForm.config_type,
      config_key: strategyForm.config_key,
      config_value: JSON.parse(strategyForm.config_json),
      status: "active"
    };
    const saved = await fetch("/api/v1/admin/city-strategy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then((res) => res.json());
    setStrategies((current) => [saved, ...current.filter((item) => item.config_key !== saved.config_key)]);
  }

  async function submitRiskRule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = {
      city_code: "hangzhou",
      rule_key: riskRuleForm.rule_key,
      rule_value: JSON.parse(riskRuleForm.rule_json),
      status: "active"
    };
    const saved = await fetch("/api/v1/admin/risk-rules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then((res) => res.json());
    setRiskRules((current) => [saved, ...current.filter((item) => item.rule_key !== saved.rule_key)]);
  }

  async function submitDestination(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = {
      destination_no: destinationForm.destination_no,
      city_code: "hangzhou",
      name: destinationForm.name,
      destination_type: destinationForm.destination_type,
      region_tags: destinationForm.region_tags.split(",").map((item) => item.trim()),
      suitable_duration: destinationForm.suitable_duration.split(",").map((item) => item.trim()),
      stay_duration_minutes: Number(destinationForm.stay_duration_minutes),
      crowd_level: JSON.parse(destinationForm.crowd_level_json),
      supply_summary: destinationForm.supply_summary,
      public_transport_options: destinationForm.public_transport_options.split(",").map((item) => item.trim()),
      stay_suggestion: destinationForm.stay_suggestion,
      status: "active"
    };
    const saved = await fetch("/api/v1/admin/nearby-destinations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then((res) => res.json());
    setNearbyDestinations((current) => [saved, ...current.filter((item) => item.destination_no !== saved.destination_no)]);
  }

  async function submitTripTemplate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = {
      trip_no: tripForm.trip_no,
      city_code: "hangzhou",
      route_template_id: tripForm.route_template_id,
      destination_no: tripForm.destination_no,
      name: tripForm.name,
      origin_region_tags: tripForm.origin_region_tags.split(",").map((item) => item.trim()),
      total_duration_hours: Number(tripForm.total_duration_hours),
      ride_duration_hours: Number(tripForm.ride_duration_hours),
      trip_style_tags: tripForm.trip_style_tags.split(",").map((item) => item.trim()),
      return_mode_options: tripForm.return_mode_options.split(",").map((item) => item.trim()),
      fallback_plan: tripForm.fallback_plan,
      status: "active"
    };
    const saved = await fetch("/api/v1/admin/trip-templates", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }).then((res) => res.json());
    setTripTemplates((current) => [saved, ...current.filter((item) => item.trip_no !== saved.trip_no)]);
  }

  return (
    <main className="page-shell">
      <ThemeToggle />
      <section className="hero-panel">
        <p className="eyebrow">Companion Admin</p>
        <h1>骑行陪伴资产后台</h1>
        <p className="hero-copy">按决策规则、路线资产、周末资产、陪伴话术四个桶维护骑行陪伴产品。</p>
        <p className="hero-link-row">
          <Link to="/">返回规划页</Link>
        </p>
      </section>

      <section className="success-layout">
        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Route Assets</p>
            <h3>路线模板、补给与撤退资产</h3>
          </div>
          <form className="planner-form" onSubmit={submitRoute}>
            <label className="field-label" htmlFor="route-code">
              路线编码
            </label>
            <input
              id="route-code"
              className="planner-input"
              value={routeForm.route_code}
              onChange={(event) => setRouteForm((current) => ({ ...current, route_code: event.target.value }))}
            />
            <label className="field-label" htmlFor="route-name">
              路线名称
            </label>
            <input
              id="route-name"
              className="planner-input"
              value={routeForm.name}
              onChange={(event) => setRouteForm((current) => ({ ...current, name: event.target.value }))}
            />
            <label className="field-label" htmlFor="route-start-point">
              起点名称
            </label>
            <input
              id="route-start-point"
              className="planner-input"
              value={routeForm.start_point_name}
              onChange={(event) => setRouteForm((current) => ({ ...current, start_point_name: event.target.value }))}
            />
            <label className="field-label" htmlFor="route-best-time-slots">
              推荐时间窗
            </label>
            <input
              id="route-best-time-slots"
              className="planner-input"
              value={routeForm.best_time_slots}
              onChange={(event) => setRouteForm((current) => ({ ...current, best_time_slots: event.target.value }))}
            />
            <label className="field-label" htmlFor="route-supply-points">
              补给点 JSON
            </label>
            <textarea
              id="route-supply-points"
              className="planner-input"
              rows={4}
              value={routeForm.supply_points_json}
              onChange={(event) => setRouteForm((current) => ({ ...current, supply_points_json: event.target.value }))}
            />
            <label className="field-label" htmlFor="route-bailout-options">
              撤退方案 JSON
            </label>
            <textarea
              id="route-bailout-options"
              className="planner-input"
              rows={4}
              value={routeForm.bailout_options_json}
              onChange={(event) => setRouteForm((current) => ({ ...current, bailout_options_json: event.target.value }))}
            />
            <label className="field-label" htmlFor="route-weather-sensitivity">
              天气敏感度 JSON
            </label>
            <textarea
              id="route-weather-sensitivity"
              className="planner-input"
              rows={3}
              value={routeForm.weather_sensitivity_json}
              onChange={(event) => setRouteForm((current) => ({ ...current, weather_sensitivity_json: event.target.value }))}
            />
            <div className="planner-actions">
              <button className="primary-button" type="submit">
                保存路线
              </button>
            </div>
          </form>
          <div className="admin-list">
            {routes.map((route) => (
              <article className="alternative-card" key={route.route_code}>
                <strong>{route.name}</strong>
                <span>{route.route_code}</span>
                <span>{route.start_point_name ?? "-"}</span>
                <span>{route.district_tags.join(" / ")}</span>
                <span>{(route.best_time_slots ?? []).join(" / ")}</span>
              </article>
            ))}
          </div>
        </article>

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Decision Rules</p>
            <h3>澄清与推荐偏置规则</h3>
          </div>
          <form className="planner-form" onSubmit={submitStrategy}>
            <label className="field-label" htmlFor="strategy-type">
              规则类别
            </label>
            <select
              id="strategy-type"
              value={strategyForm.config_type}
              onChange={(event) => setStrategyForm((current) => ({ ...current, config_type: event.target.value }))}
            >
              <option value="risk_bias">推荐偏置</option>
              <option value="clarification_rule">澄清规则</option>
              <option value="presentation_template">陪伴话术</option>
            </select>
            <label className="field-label" htmlFor="strategy-key">
              策略键
            </label>
            <input
              id="strategy-key"
              className="planner-input"
              value={strategyForm.config_key}
              onChange={(event) => setStrategyForm((current) => ({ ...current, config_key: event.target.value }))}
            />
            <label className="field-label" htmlFor="strategy-json">
              配置 JSON
            </label>
            <textarea
              id="strategy-json"
              className="planner-input"
              rows={5}
              value={strategyForm.config_json}
              onChange={(event) => setStrategyForm((current) => ({ ...current, config_json: event.target.value }))}
            />
            <div className="planner-actions">
              <button className="primary-button" type="submit">
                保存策略
              </button>
            </div>
          </form>
          <div className="admin-list">
            {decisionStrategies.map((strategy) => (
              <article className="alternative-card" key={strategy.config_key}>
                <strong>{strategy.config_key}</strong>
                <span>{strategy.config_type}</span>
                <pre className="parsed-json">{JSON.stringify(strategy.config_value, null, 2)}</pre>
              </article>
            ))}
          </div>
        </article>

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Decision Rules</p>
            <h3>风险与降级规则</h3>
          </div>
          <form className="planner-form" onSubmit={submitRiskRule}>
            <label className="field-label" htmlFor="risk-rule-key">
              规则键
            </label>
            <input
              id="risk-rule-key"
              className="planner-input"
              value={riskRuleForm.rule_key}
              onChange={(event) => setRiskRuleForm((current) => ({ ...current, rule_key: event.target.value }))}
            />
            <label className="field-label" htmlFor="risk-rule-json">
              规则 JSON
            </label>
            <textarea
              id="risk-rule-json"
              className="planner-input"
              rows={6}
              value={riskRuleForm.rule_json}
              onChange={(event) => setRiskRuleForm((current) => ({ ...current, rule_json: event.target.value }))}
            />
            <div className="planner-actions">
              <button className="primary-button" type="submit">
                保存风险规则
              </button>
            </div>
          </form>
          <div className="admin-list">
            {riskRules.map((rule) => (
              <article className="alternative-card" key={rule.rule_key}>
                <strong>{rule.rule_key}</strong>
                <span>{rule.status}</span>
                <pre className="parsed-json">{JSON.stringify(rule.rule_value, null, 2)}</pre>
              </article>
            ))}
          </div>
        </article>

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Weekend Assets</p>
            <h3>周边目的地资产</h3>
          </div>
          <form className="planner-form" onSubmit={submitDestination}>
            <label className="field-label" htmlFor="destination-no">
              目的地编号
            </label>
            <input id="destination-no" className="planner-input" value={destinationForm.destination_no} onChange={(event) => setDestinationForm((current) => ({ ...current, destination_no: event.target.value }))} />
            <label className="field-label" htmlFor="destination-name">
              目的地名称
            </label>
            <input id="destination-name" className="planner-input" value={destinationForm.name} onChange={(event) => setDestinationForm((current) => ({ ...current, name: event.target.value }))} />
            <label className="field-label" htmlFor="destination-tags">
              区域与偏好标签
            </label>
            <input id="destination-tags" className="planner-input" value={destinationForm.region_tags} onChange={(event) => setDestinationForm((current) => ({ ...current, region_tags: event.target.value }))} />
            <label className="field-label" htmlFor="destination-crowd">
              拥挤规则 JSON
            </label>
            <textarea id="destination-crowd" className="planner-input" rows={3} value={destinationForm.crowd_level_json} onChange={(event) => setDestinationForm((current) => ({ ...current, crowd_level_json: event.target.value }))} />
            <label className="field-label" htmlFor="destination-return">
              公共交通返程
            </label>
            <input id="destination-return" className="planner-input" value={destinationForm.public_transport_options} onChange={(event) => setDestinationForm((current) => ({ ...current, public_transport_options: event.target.value }))} />
            <label className="field-label" htmlFor="destination-stay">
              停留建议
            </label>
            <textarea id="destination-stay" className="planner-input" rows={3} value={destinationForm.stay_suggestion} onChange={(event) => setDestinationForm((current) => ({ ...current, stay_suggestion: event.target.value }))} />
            <div className="planner-actions">
              <button className="primary-button" type="submit">
                保存目的地
              </button>
            </div>
          </form>
          <div className="admin-list">
            {nearbyDestinations.map((destination) => (
              <article className="alternative-card" key={destination.destination_no}>
                <strong>{destination.name}</strong>
                <span>{destination.destination_no}</span>
                <span>{destination.destination_type}</span>
                <span>{(destination.region_tags ?? []).join(" / ")}</span>
                <span>{(destination.public_transport_options ?? []).join(" / ")}</span>
              </article>
            ))}
          </div>
        </article>

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Weekend Assets</p>
            <h3>周末方案模板</h3>
          </div>
          <form className="planner-form" onSubmit={submitTripTemplate}>
            <label className="field-label" htmlFor="trip-no">
              方案编号
            </label>
            <input id="trip-no" className="planner-input" value={tripForm.trip_no} onChange={(event) => setTripForm((current) => ({ ...current, trip_no: event.target.value }))} />
            <label className="field-label" htmlFor="trip-name">
              方案名称
            </label>
            <input id="trip-name" className="planner-input" value={tripForm.name} onChange={(event) => setTripForm((current) => ({ ...current, name: event.target.value }))} />
            <label className="field-label" htmlFor="trip-route">
              关联路线模板
            </label>
            <input id="trip-route" className="planner-input" value={tripForm.route_template_id} onChange={(event) => setTripForm((current) => ({ ...current, route_template_id: event.target.value }))} />
            <label className="field-label" htmlFor="trip-destination">
              关联目的地模板
            </label>
            <input id="trip-destination" className="planner-input" value={tripForm.destination_no} onChange={(event) => setTripForm((current) => ({ ...current, destination_no: event.target.value }))} />
            <label className="field-label" htmlFor="trip-return">
              返程方式
            </label>
            <input id="trip-return" className="planner-input" value={tripForm.return_mode_options} onChange={(event) => setTripForm((current) => ({ ...current, return_mode_options: event.target.value }))} />
            <label className="field-label" htmlFor="trip-fallback">
              撤退方案
            </label>
            <textarea id="trip-fallback" className="planner-input" rows={3} value={tripForm.fallback_plan} onChange={(event) => setTripForm((current) => ({ ...current, fallback_plan: event.target.value }))} />
            <div className="planner-actions">
              <button className="primary-button" type="submit">
                保存周边游模板
              </button>
            </div>
          </form>
          <div className="admin-list">
            {tripTemplates.map((trip) => (
              <article className="alternative-card" key={trip.trip_no}>
                <strong>{trip.name}</strong>
                <span>{trip.trip_no}</span>
                <span>{trip.route_template_id} / {trip.destination_no}</span>
                <span>{trip.total_duration_hours} h</span>
                <span>{(trip.return_mode_options ?? []).join(" / ")}</span>
              </article>
            ))}
          </div>
        </article>

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Agent Presentation Assets</p>
            <h3>推荐话术与降级话术</h3>
          </div>
          <p className="summary-copy">使用上面的规则配置，选择“陪伴话术”后保存，就能把推荐语气和降级提示逐步从代码迁到结构化资产。</p>
          <div className="admin-list">
            {presentationStrategies.map((strategy) => (
              <article className="alternative-card" key={strategy.config_key}>
                <strong>{strategy.config_key}</strong>
                <span>{strategy.config_type}</span>
                <pre className="parsed-json">{JSON.stringify(strategy.config_value, null, 2)}</pre>
              </article>
            ))}
          </div>
        </article>

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Decision Audit</p>
            <h3>查询日志记录</h3>
          </div>
          <div className="admin-list">
            {queryLogs.map((log) => (
              <article className="alternative-card" key={log.request_no}>
                <strong>{log.query}</strong>
                <span>{log.recommended_route_name}</span>
                <span>{log.created_at}</span>
              </article>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
