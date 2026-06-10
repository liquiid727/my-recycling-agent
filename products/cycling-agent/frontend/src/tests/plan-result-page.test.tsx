/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import HomePage from "../pages/HomePage";
import PlanResultPage from "../pages/PlanResultPage";

test("navigates from home page to saved plan result page after submit", async () => {
  const fetchMock = vi.fn(async (url: string) => {
    if (url === "/api/v1/ride/chat/turn") {
      return {
        ok: true,
        json: async () => ({
          assistant_name: "AAA骑车帮帮",
          assistant_message: "收到，我先帮你看今晚适不适合骑。",
          slot_state: { start_point: "滨江", available_hours: 3 },
          missing_slots: [],
          ready_to_plan: true,
          planner_request: {
            query: "我今天晚上想出去骑行一下",
            target_date: "2026-05-30",
            planning_mode: "route",
            planning_scene: "city_ride",
            input_mode: "structured",
            structured_constraints: { start_point: "滨江", available_hours: 3, ride_style: "scenic_relaxed" }
          },
          ui_hints: { planning_status_label: "我在看天气和路线难度" }
        })
      };
    }
    if (url === "/api/v1/ride/plan/stream") {
      return { ok: false, body: null, status: 503 };
    }
    if (url.startsWith("/api/v1/ride/plan/")) {
      return {
        ok: true,
        json: async () => ({
          request_no: "RQ-TEST0001",
          parsed_constraints: { origin_region: "滨江", available_hours: 3, ride_style: "scenic_relaxed" },
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
          roadbook: null
        })
      };
    }

    return {
      ok: true,
      json: async () => ({
        request_no: "RQ-TEST0001",
        parsed_constraints: { origin_region: "滨江", available_hours: 3, ride_style: "scenic_relaxed" },
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
        roadbook: null
      })
    };
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter initialEntries={["/"]}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/plans/:requestNo" element={<PlanResultPage />} />
      </Routes>
    </MemoryRouter>,
  );

  fireEvent.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("推荐结果页")).toBeInTheDocument();
  expect(await screen.findByText("滨江-钱塘江休闲往返线")).toBeInTheDocument();
});
