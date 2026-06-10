/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import PlanResultPage from "../pages/PlanResultPage";

test("renders clarification prompt when saved plan is missing key fields", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        request_no: "RQ-TEST0002",
        parsed_constraints: {
          origin_region: null,
          available_hours: null,
          ride_style: "general",
          missing_fields: ["origin_region", "available_hours"],
          confidence: 0.52
        },
        clarification_prompt: "当前还缺少关键信息：出发区域、可骑时长。补充后推荐结果会更稳。",
        recommended_plan: {
          go_decision: "go",
          route_name: "湘湖半日郊游线",
          route_code: "HZ-LEISURE-003",
          distance_km: 30,
          elevation_gain_m: 210,
          estimated_duration_hours: 2.4,
          risk_level: "low",
          summary_reason: "先按默认轻松线给出保守推荐。"
        },
        alternatives: [],
        weather_snapshot: {
          region_code: "hangzhou",
          forecast_date: "2026-05-30",
          temperature_min: 22,
          temperature_max: 30,
          precipitation_probability: 0.1,
          wind_speed: 3.2,
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
    <MemoryRouter initialEntries={["/plans/RQ-TEST0002"]}>
      <Routes>
        <Route path="/plans/:requestNo" element={<PlanResultPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("建议补充信息")).toBeInTheDocument();
  expect(screen.getByText(/出发区域、可骑时长/)).toBeInTheDocument();
});
