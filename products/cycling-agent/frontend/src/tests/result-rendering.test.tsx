/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import PlanResultPage from "../pages/PlanResultPage";

test("renders provider trace and poi summary in saved plan result page", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        request_no: "RQ-TEST0001",
        parsed_constraints: { planning_scene: "city_ride", origin_region: "滨江", available_hours: 3, ride_style: "scenic_relaxed" },
        clarification_prompt: null,
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
        tool_trace: [
          {
            stage_name: "route_provider",
            status: "success",
            provider_name: "local-route-stub",
            summary: "Loaded route context for HZ-RIVER-001.",
            fallback_reason: null
          },
          {
            stage_name: "poi_provider",
            status: "success",
            provider_name: "local-poi-stub",
            summary: "Loaded POI context for HZ-RIVER-001.",
            fallback_reason: null
          }
        ],
        decision_summary: {
          scene: "city_ride",
          go_decision: "go",
          decision_title: "这次可以骑，优先按主推荐执行",
          decision_reason: "时长匹配，轻松稳定。",
          confidence_notes: ["风险等级：low", "天气：cloudy"],
          equipment_advice: ["基础装备：头盔、手套、补胎工具、随身水壶。"]
        },
        roadbook: {
          departure_window: "06:30-09:30",
          key_segments: ["从闻涛路滨江段进入主路线"],
          supply_advice: ["起点附近先补水"],
          mitigation_advice: ["若风变大可提前折返"],
          shorten_options: ["奥体中途折返：保留江景主段，返程最稳"],
          poi_summary: {
            supply_count: 2,
            bailout_count: 1,
            supply_labels: ["闻涛路便利店(便利店)", "奥体观景平台补水点(补水点)"],
            bailout_labels: ["奥体中途折返"]
          },
          route_context: {
            provider_name: "local-route-stub",
            average_speed_kmh: 15,
            surface_type: "greenway",
            loop_type: "out_and_back"
          }
        }
      })
    }))
  );

  render(
    <MemoryRouter initialEntries={["/plans/RQ-TEST0001"]}>
      <Routes>
        <Route path="/plans/:requestNo" element={<PlanResultPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("推荐结果页")).toBeInTheDocument();
  expect(screen.getByText("这次可以骑，优先按主推荐执行")).toBeInTheDocument();
  expect(screen.getByText("查看识别和服务调用细节")).toBeInTheDocument();
  expect(screen.getByText("服务调用细节")).toBeInTheDocument();
  expect(screen.getByText(/route_provider: local-route-stub/)).toBeInTheDocument();
  expect(screen.getByText("补给点数量：2")).toBeInTheDocument();
});
