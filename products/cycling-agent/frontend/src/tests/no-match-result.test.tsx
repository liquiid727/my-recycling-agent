/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import PlanResultPage from "../pages/PlanResultPage";

test("renders no-match state for extreme query result", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        status: "no_match",
        request_no: "RQ-NOMATCH001",
        parsed_constraints: {
          origin_region: "滨江",
          available_hours: 12,
          ride_style: "scenic_relaxed",
          missing_fields: [],
          confidence: 0.92
        },
        clarification_prompt: null,
        no_match_reason: "当前约束下没有足够匹配的杭州路线模板，建议补充时长或放宽偏好后再试。",
        recommended_plan: {
          go_decision: "no_go",
          route_name: "当前没有合适路线",
          route_code: "NO-MATCH",
          distance_km: 0,
          elevation_gain_m: 0,
          estimated_duration_hours: 0,
          risk_level: "unknown",
          summary_reason: "现有模板库下没有足够匹配的候选路线。"
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
    }))
  );

  render(
    <MemoryRouter initialEntries={["/plans/RQ-NOMATCH001"]}>
      <Routes>
        <Route path="/plans/:requestNo" element={<PlanResultPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("当前没有合适路线")).toBeInTheDocument();
  expect(screen.getByText(/建议补充时长或放宽偏好后再试/)).toBeInTheDocument();
});

test("shows popular route fallback only when dynamic route service is unavailable", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/routes/recommended")) {
        return {
          ok: true,
          json: async () => [
            {
              route_code: "HZ-RIVER-001",
              route_name: "滨江-钱塘江休闲往返线",
              distance_km: 42,
              elevation_gain_m: 180,
              estimated_duration_hours: 2.8,
              difficulty_level: "easy",
              ride_style_tags: ["relaxed", "scenic"],
              district_tags: ["滨江"]
            }
          ]
        };
      }
      return {
        ok: true,
        json: async () => ({
          status: "no_match",
          request_no: "RQ-DYNFAIL001",
          parsed_constraints: {
            start_point: "沈塘桥",
            available_hours: 2,
            ride_style: "scenic_relaxed",
            missing_fields: [],
            confidence: 0.92
          },
          clarification_prompt: null,
          no_match_reason: "动态路线服务暂时不可用，未使用固定模板生成本次推荐。",
          recommended_plan: {
            go_decision: "no_go",
            route_name: "当前没有合适路线",
            route_code: "NO-MATCH",
            distance_km: 0,
            elevation_gain_m: 0,
            estimated_duration_hours: 0,
            risk_level: "unknown",
            summary_reason: "动态路线服务暂时不可用。"
          },
          alternatives: [],
          weather_snapshot: {
            region_code: "hangzhou",
            forecast_date: "2026-06-06",
            temperature_min: 22,
            temperature_max: 31,
            precipitation_probability: 0.15,
            wind_speed: 4.8,
            wind_direction: "SE",
            weather_summary: "cloudy",
            provider_name: "stub",
            raw_payload: {}
          },
          fallback_reason: ["nearby-route-discovery-unavailable"],
          tool_trace: [
            {
              stage_name: "nearby_route_discovery",
              status: "fallback",
              provider_name: "dynamic-nearby-route",
              summary: "Nearby route discovery failed, falling back to route templates.",
              fallback_reason: "nearby-route-discovery-unavailable"
            }
          ],
          roadbook: null
        })
      };
    })
  );

  render(
    <MemoryRouter initialEntries={["/plans/RQ-DYNFAIL001"]}>
      <Routes>
        <Route path="/plans/:requestNo" element={<PlanResultPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("当前没有合适路线")).toBeInTheDocument();
  expect(screen.getByText("不妨看看最近的热门和精品路线吧")).toBeInTheDocument();
  expect(await screen.findByText("滨江-钱塘江休闲往返线")).toBeInTheDocument();
});
