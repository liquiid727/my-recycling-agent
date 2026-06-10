/*
 * CN: Phase 2 周边游结果页测试，验证 trip 输出不是 mvp1 路线卡片的字段混用。
 * EN: Phase 2 nearby-trip result tests proving trip output is distinct from mvp1 route cards.
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import PlanResultView from "../components/PlanResultView";
import type { RidePlanResponse } from "../features/planner/api";

test("renders nearby trip recommendation rhythm risks and return options", () => {
  const result = {
    status: "success",
    planning_mode: "nearby_trip",
    request_no: "RQ-TRIP0001",
    parsed_constraints: { planning_scene: "weekend_trip", origin_region: "滨江", duration_bucket: "half_day", destination_preferences: ["江边", "咖啡"] },
    clarification_prompt: null,
    no_match_reason: null,
    recommended_plan: {
      go_decision: "go",
      route_name: "钱塘江沿线亲水骑 + 江边咖啡",
      route_code: "HZ-RIVER-001",
      distance_km: 42,
      elevation_gain_m: 180,
      estimated_duration_hours: 2.8,
      risk_level: "medium",
      summary_reason: "半天内可完成，目的地停留和返程都明确。"
    },
    alternatives: [],
    recommended_trip: {
      trip_no: "TRIP-HZ-RIVER-CAFE",
      trip_name: "钱塘江沿线亲水骑 + 江边咖啡",
      destination_name: "钱塘江滨江咖啡休息带",
      suitable_for: "适合想要轻松江景和明确停留点的半日骑用户",
      total_distance_km: 42,
      ride_duration_hours: 2.8,
      total_duration_hours: 4.5,
      recommended_departure_time: "08:00",
      stay_suggestion: "到达后停留 45 到 60 分钟，补水和咖啡休息。",
      why_recommended: "出发区域、半天时长和江边咖啡偏好匹配。",
      risk_level: "medium",
      return_options: ["骑回", "地铁 6 号线公共交通返程"],
      lodging_plan: "无需过夜，按半日骑执行。",
      equipment_advice: ["基础装备：头盔、手套、补胎工具、随身水壶。"],
      weather_window_notes: "午前完成更稳。"
    },
    trip_alternatives: [
      {
        trip_no: "TRIP-HZ-XIANGHU",
        trip_name: "湘湖半日休闲骑",
        destination_name: "湘湖",
        suitable_for: "适合轻松休闲",
        total_distance_km: 35,
        ride_duration_hours: 2.5,
        total_duration_hours: 4,
        recommended_departure_time: "07:30",
        stay_suggestion: "湖边停留。",
        why_recommended: "同属半日轻松方案。",
        risk_level: "low",
        return_options: ["骑回"],
        equipment_advice: []
      }
    ],
    trip_rhythm: {
      segments: [
        { stage: "出发前准备", time_window: "07:30-08:00", description: "检查天气和补水。" },
        { stage: "返程方式", time_window: "12:00-12:45", description: "优先骑回，体感下降时改公共交通。" }
      ]
    },
    trip_risks: {
      risk_items: ["天气风险：午前热感上升", "返程风险：午后体力下降时改公共交通"],
      fallback_plan: "天气转差时缩短到奥体折返。"
    },
    weather_snapshot: {
      region_code: "binjiang",
      forecast_date: "2026-06-06",
      temperature_min: 23,
      temperature_max: 32,
      precipitation_probability: 0.2,
      wind_speed: 4.2,
      wind_direction: "SE",
      weather_summary: "cloudy",
      provider_name: "stub",
      raw_payload: {}
    },
    fallback_reason: [],
    tool_trace: [],
    decision_summary: {
      scene: "weekend_trip",
      go_decision: "caution",
      decision_title: "优先考虑钱塘江滨江咖啡休息带方向",
      decision_reason: "出发区域、半天时长和江边咖啡偏好匹配。",
      confidence_notes: ["目的地：钱塘江滨江咖啡休息带", "住宿：无需过夜，按半日骑执行。"],
      equipment_advice: ["基础装备：头盔、手套、补胎工具、随身水壶。"]
    },
    roadbook: null
  } satisfies RidePlanResponse;

  render(
    <MemoryRouter>
      <PlanResultView result={result} />
    </MemoryRouter>,
  );

  expect(screen.getByText("优先考虑钱塘江滨江咖啡休息带方向")).toBeInTheDocument();
  expect(screen.getByText("钱塘江滨江咖啡休息带")).toBeInTheDocument();
  expect(screen.getByText("节奏安排")).toBeInTheDocument();
  expect(screen.getByText("返程和撤退")).toBeInTheDocument();
  expect(screen.getByText(/地铁 6 号线公共交通返程/)).toBeInTheDocument();
  expect(screen.getByText(/天气转差时缩短到奥体折返/)).toBeInTheDocument();
});
