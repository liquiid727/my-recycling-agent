/*
 * CN: 前端测试文件，验证路线地图区域的输入摘要和无高德 key 降级。
 * EN: Frontend tests for route map input summary and no-key fallback rendering.
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import PlanResultView from "../components/PlanResultView";
import type { RidePlanResponse } from "../features/planner/api";

test("renders input summary and map fallback when amap js key is unavailable", async () => {
  const result: RidePlanResponse = {
    request_no: "RQ-MAP",
    status: "success",
    parsed_constraints: { origin_region: "滨江", available_hours: 3, ride_style: "scenic_relaxed" },
    input_summary: {
      input_mode: "structured",
      target_date: "2026-05-30",
      departure_time: "07:00",
      city_code: "hangzhou",
      origin_region: "滨江",
      start_point: "闻涛路滨江段",
      available_hours: 3,
      target_distance_km: 42,
      fitness_level: "medium",
      ride_style: "scenic_relaxed",
      slope_tolerance: "avoid",
      priority: "风景",
      defaults_applied: []
    },
    clarification_prompt: null,
    no_match_reason: null,
    recommended_plan: {
      go_decision: "go",
      route_name: "滨江-钱塘江休闲往返线",
      route_code: "HZ-RIVER-001",
      distance_km: 42,
      elevation_gain_m: 180,
      estimated_duration_hours: 2.8,
      risk_level: "low",
      summary_reason: "时长匹配，轻松稳定。"
    },
    alternatives: [],
    weather_snapshot: {
      region_code: "binjiang",
      forecast_date: "2026-05-30",
      temperature_min: 22,
      temperature_max: 31,
      precipitation_probability: 0.15,
      wind_speed: 4.8,
      wind_direction: "SE",
      weather_summary: "cloudy",
      provider_name: "stub",
      raw_payload: {}
    },
    ride_readiness: {
      status: "light",
      score: 0.58,
      summary: "今天更适合轻一点骑，先把强度收住。",
      reasons: ["你现在偏累，今天更适合轻一点。", "风速 4.8 m/s，体感会比平时更耗。"],
      caution_flags: ["fatigue", "wind"],
      recommended_intensity: "light"
    },
    decision_summary: {
      scene: "city_ride",
      go_decision: "caution",
      decision_title: "这次可以谨慎骑，建议保留缩短方案",
      decision_reason: "时长匹配，轻松稳定。 当前身体和天气状态判断：今天更适合轻一点骑，先把强度收住。你现在偏累，今天更适合轻一点。",
      confidence_notes: ["风险等级：low", "天气：cloudy", "状态：今天更适合轻一点骑，先把强度收住。", "出发点：闻涛路滨江段"],
      equipment_advice: ["带一瓶水"]
    },
    fallback_reason: [],
    tool_trace: [],
    route_map: {
      route_code: "HZ-RIVER-001",
      route_name: "滨江-钱塘江休闲往返线",
      provider_name: "template-only",
      fact_source: "template",
      polyline: [],
      polyline_available: false,
      fallback_reason: "route-polyline-unavailable",
      start_point: { name: "闻涛路滨江段", longitude: 120.2103, latitude: 30.2064 },
      user_start_point: { name: "用户小区门口", longitude: 120.3, latitude: 30.3 },
      template_start_point: { name: "闻涛路滨江段", longitude: 120.2103, latitude: 30.2064 },
      end_point: { name: "钱塘江南岸观景折返点", longitude: 120.2103, latitude: 30.2064 },
      approach_distance_km: 8,
      approach_duration_hours: 0.5,
      template_distance_km: 42,
      template_duration_hours: 2.8,
      total_distance_km: 50,
      total_duration_hours: 3.3,
      supply_points: [{ name: "闻涛路便利店", km_mark: 4, type: "便利店" }],
      bailout_options: [{ name: "奥体中途折返", km_mark: 18, reason: "保留江景主段，返程最稳" }],
      climb_segments: [],
      template: {
        fact_source: "template",
        route_code: "HZ-RIVER-001",
        route_name: "滨江-钱塘江休闲往返线",
        start_point: { name: "闻涛路滨江段", longitude: 120.2103, latitude: 30.2064 },
        end_point: { name: "钱塘江南岸观景折返点", longitude: 120.2103, latitude: 30.2064 },
        distance_km: 42,
        duration_hours: 2.8,
        surface_type: "greenway",
        loop_type: "out_and_back"
      },
      live: {
        provider_name: "template-only",
        fact_source: "local-approach",
        user_start_point: { name: "用户小区门口", longitude: 120.3, latitude: 30.3 },
        approach_distance_km: 8,
        approach_duration_hours: 0.5,
        polyline: []
      },
      resolved: {
        provider_name: "template-only",
        fact_source: "template+local-approach",
        metric_source: "template-plus-approach",
        distance_km: 50,
        estimated_duration_hours: 3.3,
        total_distance_km: 50,
        total_duration_hours: 3.3
      }
    },
    roadbook: null
  };

  render(
    <MemoryRouter>
      <PlanResultView result={result} />
    </MemoryRouter>,
  );

  expect(screen.getByText("本次输入")).toBeInTheDocument();
  expect(screen.getByText("这次可以谨慎骑，建议保留缩短方案")).toBeInTheDocument();
  expect(screen.getByText("时长匹配，轻松稳定。")).toBeInTheDocument();
  expect(screen.getByText("骑前身体和天气状态已经在下方单独展开。")).toBeInTheDocument();
  expect(screen.queryByText("状态：今天更适合轻一点骑，先把强度收住。")).not.toBeInTheDocument();
  expect(screen.queryByText(/当前身体和天气状态判断：/)).not.toBeInTheDocument();
  expect(screen.getByText("骑前状态判断")).toBeInTheDocument();
  expect(screen.getByText("建议：轻一点骑")).toBeInTheDocument();
  expect(screen.getByText("强度：恢复节奏")).toBeInTheDocument();
  expect(screen.getByText("准备度：58 分")).toBeInTheDocument();
  expect(screen.getByText("注意项：疲劳 / 大风")).toBeInTheDocument();
  expect(screen.getByText(/2026-05-30 07:00/)).toBeInTheDocument();
  expect(screen.getByText("路线图")).toBeInTheDocument();
  expect(screen.getByText("从你的出发点开始")).toBeInTheDocument();
  expect(screen.getByText("总量：50 km / 3.3 h")).toBeInTheDocument();
  expect(screen.getByText("接驳段：8 km / 0.5 h")).toBeInTheDocument();
  expect(screen.getByText("模板骨架：42 km / 2.8 h")).toBeInTheDocument();
  expect(screen.getByText("你的出发点：用户小区门口")).toBeInTheDocument();
  expect(screen.getByText("模板起点：闻涛路滨江段")).toBeInTheDocument();
  expect(screen.getByText("路线口径：模板骨架 + 出发点接驳")).toBeInTheDocument();
  expect(screen.getByText("未配置高德地图 JS Key，当前展示路线关键点。")).toBeInTheDocument();
  expect(screen.getByText(/闻涛路便利店/)).toBeInTheDocument();
});

test("keeps the heavy map canvas unloaded until the user requests it", () => {
  const result: RidePlanResponse = {
    request_no: "RQ-MAP-LAZY",
    status: "success",
    parsed_constraints: {},
    clarification_prompt: null,
    no_match_reason: null,
    recommended_plan: {
      go_decision: "go",
      route_name: "滨江-钱塘江休闲往返线",
      route_code: "HZ-RIVER-001",
      distance_km: 42,
      elevation_gain_m: 180,
      estimated_duration_hours: 2.8,
      risk_level: "low",
      summary_reason: "时长匹配，轻松稳定。"
    },
    alternatives: [],
    weather_snapshot: {
      region_code: "binjiang",
      forecast_date: "2026-05-30",
      temperature_min: 22,
      temperature_max: 31,
      precipitation_probability: 0.15,
      wind_speed: 4.8,
      wind_direction: "SE",
      weather_summary: "cloudy",
      provider_name: "stub",
      raw_payload: {}
    },
    fallback_reason: [],
    tool_trace: [],
    route_map: {
      route_code: "HZ-RIVER-001",
      route_name: "滨江-钱塘江休闲往返线",
      provider_name: "template-only",
      fact_source: "template",
      polyline: [{ longitude: 120.2103, latitude: 30.2064 }],
      polyline_available: true,
      fallback_reason: null,
      start_point: { name: "闻涛路滨江段", longitude: 120.2103, latitude: 30.2064 },
      user_start_point: { name: "用户小区门口", longitude: 120.3, latitude: 30.3 },
      template_start_point: { name: "闻涛路滨江段", longitude: 120.2103, latitude: 30.2064 },
      end_point: { name: "钱塘江南岸观景折返点", longitude: 120.2103, latitude: 30.2064 },
      approach_distance_km: 8,
      approach_duration_hours: 0.5,
      template_distance_km: 42,
      template_duration_hours: 2.8,
      total_distance_km: 50,
      total_duration_hours: 3.3,
      supply_points: [],
      bailout_options: [],
      climb_segments: [],
      template: {
        fact_source: "template",
        route_code: "HZ-RIVER-001",
        route_name: "滨江-钱塘江休闲往返线",
        start_point: { name: "闻涛路滨江段", longitude: 120.2103, latitude: 30.2064 },
        end_point: { name: "钱塘江南岸观景折返点", longitude: 120.2103, latitude: 30.2064 },
        distance_km: 42,
        duration_hours: 2.8
      },
      live: {
        provider_name: "template-only",
        fact_source: "local-approach",
        user_start_point: { name: "用户小区门口", longitude: 120.3, latitude: 30.3 },
        approach_distance_km: 8,
        approach_duration_hours: 0.5,
        polyline: [{ longitude: 120.2103, latitude: 30.2064 }]
      },
      resolved: {
        provider_name: "template-only",
        fact_source: "template+local-approach",
        metric_source: "template-plus-approach",
        distance_km: 50,
        estimated_duration_hours: 3.3,
        total_distance_km: 50,
        total_duration_hours: 3.3
      }
    },
    roadbook: null
  };

  render(
    <MemoryRouter>
      <PlanResultView result={result} />
    </MemoryRouter>,
  );

  expect(screen.getByText("路线图")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "加载地图" })).toBeInTheDocument();
  expect(screen.queryByLabelText("滨江-钱塘江休闲往返线地图")).not.toBeInTheDocument();
});

test("renders dynamic route semantics without template labels", () => {
  const result: RidePlanResponse = {
    request_no: "RQ-MAP-DYNAMIC",
    status: "success",
    parsed_constraints: {},
    clarification_prompt: null,
    no_match_reason: null,
    recommended_plan: {
      go_decision: "go",
      route_name: "闻涛路滨江段-运河亚运公园休闲往返线",
      route_code: "DYN-HANGZHOU-001",
      distance_km: 10,
      elevation_gain_m: 0,
      estimated_duration_hours: 0.7,
      risk_level: "low",
      summary_reason: "动态路线更贴合当前出发点。"
    },
    alternatives: [],
    weather_snapshot: {
      region_code: "binjiang",
      forecast_date: "2026-05-30",
      temperature_min: 22,
      temperature_max: 31,
      precipitation_probability: 0.15,
      wind_speed: 4.8,
      wind_direction: "SE",
      weather_summary: "cloudy",
      provider_name: "stub",
      raw_payload: {}
    },
    fallback_reason: [],
    tool_trace: [],
    route_map: {
      route_code: "DYN-HANGZHOU-001",
      route_name: "闻涛路滨江段-运河亚运公园休闲往返线",
      provider_name: "dynamic-nearby-route",
      fact_source: "amap-dynamic",
      polyline: [],
      polyline_available: false,
      fallback_reason: "route-polyline-unavailable",
      start_point: { name: "闻涛路滨江段", longitude: 120.2103, latitude: 30.2064 },
      user_start_point: { name: "闻涛路滨江段", longitude: 120.2103, latitude: 30.2064 },
      end_point: { name: "运河亚运公园", longitude: 120.145, latitude: 30.31 },
      approach_distance_km: 0,
      approach_duration_hours: 0,
      template_distance_km: 10,
      template_duration_hours: 0.7,
      total_distance_km: 10,
      total_duration_hours: 0.7,
      supply_points: [],
      bailout_options: [],
      climb_segments: [],
      template: null,
      live: {
        provider_name: "dynamic-nearby-route",
        fact_source: "amap-dynamic",
        user_start_point: { name: "闻涛路滨江段", longitude: 120.2103, latitude: 30.2064 },
        polyline: []
      },
      resolved: {
        provider_name: "dynamic-nearby-route",
        fact_source: "amap-dynamic",
        metric_source: "dynamic-live",
        distance_km: 10,
        estimated_duration_hours: 0.7,
        total_distance_km: 10,
        total_duration_hours: 0.7
      }
    },
    roadbook: null
  };

  render(
    <MemoryRouter>
      <PlanResultView result={result} />
    </MemoryRouter>
  );

  expect(screen.getByText("动态路线：10 km / 0.7 h")).toBeInTheDocument();
  expect(screen.getByText("动态路线终点：运河亚运公园")).toBeInTheDocument();
  expect(screen.getByText("实时路径来源：基于实时动态路径生成")).toBeInTheDocument();
  expect(screen.getByText("路线口径：动态路线实时结果")).toBeInTheDocument();
  expect(screen.queryByText(/模板起点：/)).not.toBeInTheDocument();
  expect(screen.queryByText(/模板骨架：/)).not.toBeInTheDocument();
});
