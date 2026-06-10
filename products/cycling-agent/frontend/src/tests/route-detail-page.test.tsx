/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import RouteDetailPage from "../pages/RouteDetailPage";

test("renders route detail from route api", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        route_code: "HZ-RIVER-001",
        route_name: "滨江-钱塘江休闲往返线",
        city_code: "hangzhou",
        distance_km: 42,
        elevation_gain_m: 180,
        estimated_duration_hours: 2.8,
        difficulty_level: "easy",
        ride_style_tags: ["relaxed", "scenic"],
        district_tags: ["滨江", "钱塘江"],
        start_point_name: "闻涛路滨江段",
        start_point_lng: 120.2103,
        start_point_lat: 30.2064,
        end_point_name: "钱塘江南岸观景折返点",
        loop_type: "out_and_back",
        season_tags: ["spring", "autumn"],
        best_time_slots: ["06:30-09:30", "16:30-18:30"],
        avoid_time_slots: ["11:00-15:00"],
        surface_type: "greenway",
        traffic_level: "low",
        supply_score: 8,
        return_difficulty_score: 3,
        scenic_score: 8,
        training_score: 4,
        beginner_friendly: true,
        climb_segments: [],
        supply_points: [{ name: "奥体观景平台补水点", km_mark: 18, type: "补水点" }],
        bailout_options: [{ name: "奥体中途折返", km_mark: 18, reason: "保留江景主段，返程最稳" }],
        holiday_penalty_level: "medium",
        weather_sensitivity: { heat: "medium" },
        route_notes: "适合周末晨骑，风景稳定，整体节奏轻松。"
      })
    }))
  );

  render(
    <MemoryRouter initialEntries={["/routes/HZ-RIVER-001"]}>
      <Routes>
        <Route path="/routes/:routeCode" element={<RouteDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("滨江-钱塘江休闲往返线")).toBeInTheDocument();
  expect(screen.getByText("起点：闻涛路滨江段")).toBeInTheDocument();
  expect(screen.getByText("18 km: 奥体观景平台补水点 (补水点)")).toBeInTheDocument();
  expect(screen.getByText("奥体中途折返: 保留江景主段，返程最稳")).toBeInTheDocument();
});
