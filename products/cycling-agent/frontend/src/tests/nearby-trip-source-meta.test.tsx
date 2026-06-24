import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import PlanResultView from "../components/PlanResultView";
import type { RidePlanResponse } from "../features/planner/api";

test("renders nearby trip source metadata with route binding provenance", () => {
  const result: RidePlanResponse = {
    request_no: "RQ-TRIP-SOURCE",
    status: "success",
    planning_mode: "nearby_trip",
    parsed_constraints: {
      planning_scene: "weekend_trip"
    },
    clarification_prompt: null,
    no_match_reason: null,
    recommended_plan: {
      go_decision: "go",
      route_name: "闻涛路滨江段-湘湖游客中心休闲往返线",
      route_code: "DYN-HANGZHOU-001",
      distance_km: 28,
      elevation_gain_m: 0,
      estimated_duration_hours: 2.1,
      risk_level: "low",
      summary_reason: "动态路线和周末骨架更匹配。"
    },
    alternatives: [],
    weather_snapshot: {
      region_code: "binjiang",
      forecast_date: "2026-06-06",
      temperature_min: 23,
      temperature_max: 31,
      precipitation_probability: 0.2,
      wind_speed: 4.2,
      wind_direction: "SE",
      weather_summary: "cloudy",
      provider_name: "stub",
      raw_payload: {}
    },
    fallback_reason: [],
    tool_trace: [],
    recommended_trip: {
      trip_no: "TRIP-001",
      trip_name: "半天湘湖咖啡停留",
      destination_name: "湘湖游客中心",
      suitable_for: "适合周末半天轻松骑。",
      total_distance_km: 28,
      ride_duration_hours: 2.1,
      total_duration_hours: 3.1,
      recommended_departure_time: "08:00",
      stay_suggestion: "到达后休息 60 分钟。",
      why_recommended: "先找可行路线，再承接周末骨架。",
      risk_level: "low",
      return_options: ["原路折返", "地铁接驳"],
      duration_bucket: "half_day",
      source_meta: {
        trip_template: {
          trip_no: "TRIP-001",
          route_template_id: "HZ-RIVER-001",
          duration_bucket: "half_day"
        },
        destination_template: {
          destination_no: "DST-003",
          destination_type: "湖边停留",
          region_tags: ["湘湖", "咖啡"]
        },
        route_binding: {
          selected_route_code: "DYN-HANGZHOU-001",
          selected_route_name: "闻涛路滨江段-湘湖游客中心休闲往返线",
          selected_route_source: "dynamic_nearby",
          is_template_route_match: false,
          audit_summary:
            "未沿用模板路线 HZ-RIVER-001，改选 DYN-HANGZHOU-001；模板路线未进入 5 条可行候选。"
        },
        resolved_metrics: {
          distance_km: 28,
          ride_duration_hours: 2.1,
          metric_source: "dynamic-live"
        }
      }
    },
    trip_alternatives: [
      {
        trip_no: "TRIP-ALT-001",
        trip_name: "半天运河轻松停留",
        destination_name: "运河亚运公园",
        suitable_for: "适合半天轻松骑。",
        total_distance_km: 24,
        ride_duration_hours: 1.8,
        total_duration_hours: 2.6,
        recommended_departure_time: "08:30",
        stay_suggestion: "公园停留 45 分钟。",
        why_recommended: "距离更短，返程更稳。",
        risk_level: "low",
        return_options: ["原路折返"],
        duration_bucket: "half_day",
        source_meta: {
          trip_template: {
            trip_no: "TRIP-ALT-001",
            route_template_id: "HZ-CANAL-001",
            duration_bucket: "half_day"
          },
          route_binding: {
            selected_route_code: "DYN-HANGZHOU-ALT",
            selected_route_name: "沈塘桥-运河亚运公园休闲往返线",
            selected_route_source: "dynamic_nearby",
            is_template_route_match: false
          }
        }
      }
    ],
    trip_rhythm: null,
    trip_risks: null,
    route_map: null,
    roadbook: null
  };

  render(
    <MemoryRouter>
      <PlanResultView result={result} />
    </MemoryRouter>
  );

  expect(screen.getByText("这次怎么承接")).toBeInTheDocument();
  expect(screen.getByText("周末骨架：TRIP-001 / 半天")).toBeInTheDocument();
  expect(screen.getByText("目的地模板：DST-003 / 湖边停留")).toBeInTheDocument();
  expect(screen.getByText("实际承接路线：闻涛路滨江段-湘湖游客中心休闲往返线 / DYN-HANGZHOU-001 / 动态近场路线")).toBeInTheDocument();
  expect(screen.getByText("总量口径：动态路线实时结果")).toBeInTheDocument();
  expect(
    screen.getByText(
      "审计摘要：未沿用模板路线 HZ-RIVER-001，改选 DYN-HANGZHOU-001；模板路线未进入 5 条可行候选。"
    )
  ).toBeInTheDocument();
  expect(screen.getByText("匹配方式：没有强行沿用模板路线，改用更贴合这次出发点和约束的路线去承接。")).toBeInTheDocument();
  expect(screen.getByText("半天运河轻松停留: 运河亚运公园 / 2.6 h / low。半天骨架，沈塘桥-运河亚运公园休闲往返线承接，改用更贴当前条件的路线")).toBeInTheDocument();
});
