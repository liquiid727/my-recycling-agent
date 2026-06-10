/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import HomePage from "../pages/HomePage";
import SettingsPage from "../pages/SettingsPage";

test("submits planner request with saved user profile", async () => {
  const storage = new Map<string, string>();
  Object.defineProperty(window, "localStorage", {
    value: {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      }
    },
    configurable: true
  });

  const fetchMock = vi.fn(async (_url, init?: RequestInit) => ({
    ok: true,
    json: async () => {
      if (String(_url).includes("/api/v1/profile/default") && !init?.method) {
        return {
          fitness_level: "",
          slope_tolerance: "",
          ride_style_preferences: []
        };
      }
      if (String(_url).includes("/api/v1/profile/default") && init?.method === "PUT") {
        return JSON.parse(String(init.body));
      }
      if (String(_url) === "/api/v1/ride/chat/turn") {
        return {
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
            structured_constraints: { start_point: "滨江", available_hours: 3 }
          },
          ui_hints: { planning_status_label: "我在看天气和路线难度" }
        };
      }
      if (String(_url) === "/api/v1/ride/plan/stream") {
        return {};
      }
      return {
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
        roadbook: null
      };
    }
  }));
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <SettingsPage />
    </MemoryRouter>,
  );

  fireEvent.change(screen.getByLabelText("体力等级"), { target: { value: "medium" } });
  fireEvent.change(screen.getByLabelText("爬坡接受度"), { target: { value: "avoid" } });
  fireEvent.click(screen.getByLabelText("风景优先"));
  fireEvent.click(screen.getByRole("button", { name: "保存偏好" }));

  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  fireEvent.click(screen.getByRole("button", { name: "发送" }));

  await waitFor(() =>
    expect(fetchMock.mock.calls.some(([url]) => String(url) === "/api/v1/ride/plan")).toBe(true),
  );
  const plannerCall = fetchMock.mock.calls.find(([url]) => String(url) === "/api/v1/ride/plan");
  const [, requestInit] = plannerCall ?? [];
  const body = JSON.parse(String(requestInit?.body));

  expect(body.user_profile.fitness_level).toBe("medium");
  expect(body.user_profile.slope_tolerance).toBe("avoid");
  expect(body.user_profile.ride_style_preferences).toEqual(["scenic"]);
});
