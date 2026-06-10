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
      climb_segments: []
    },
    roadbook: null
  };

  render(
    <MemoryRouter>
      <PlanResultView result={result} />
    </MemoryRouter>,
  );

  expect(screen.getByText("本次输入")).toBeInTheDocument();
  expect(screen.getByText(/2026-05-30 07:00/)).toBeInTheDocument();
  expect(screen.getByText("路线图")).toBeInTheDocument();
  expect(screen.getByText("从你的出发点开始")).toBeInTheDocument();
  expect(screen.getByText("总量：50 km / 3.3 h")).toBeInTheDocument();
  expect(screen.getByText("接驳：8 km / 0.5 h")).toBeInTheDocument();
  expect(screen.getByText("你的出发点：用户小区门口")).toBeInTheDocument();
  expect(screen.getByText("主路线起点：闻涛路滨江段")).toBeInTheDocument();
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
      climb_segments: []
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
