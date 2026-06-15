/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, vi } from "vitest";

import HomePage from "../pages/HomePage";

beforeEach(() => {
  document.documentElement.removeAttribute("data-theme");
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("renders planning input", () => {
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  expect(screen.getByLabelText("骑行规划对话")).toBeInTheDocument();
  expect(screen.getAllByText("AAA骑车帮帮").length).toBeGreaterThan(0);
  expect(screen.getByText(/像和朋友聊天一样/)).toBeInTheDocument();
  expect(within(screen.getByLabelText("骑行意图")).getByRole("button", { name: "今天适合骑吗" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "今晚轻松骑" })).toBeInTheDocument();
  expect(screen.getByPlaceholderText("例如：我今天晚上想出去骑行一下")).toBeInTheDocument();
});

test("renders three intent-first entry modes", () => {
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  const intentGroup = within(screen.getByLabelText("骑行意图"));
  expect(intentGroup.getByRole("button", { name: "今天适合骑吗" })).toHaveAttribute("aria-pressed", "true");
  expect(intentGroup.getByRole("button", { name: "帮我安排一次骑行" })).toHaveAttribute("aria-pressed", "false");
  expect(intentGroup.getByRole("button", { name: "周末去哪骑" })).toHaveAttribute("aria-pressed", "false");
  expect(screen.getByText("先判断今天值不值得骑，再给保守建议")).toBeInTheDocument();
});

test("switches between cycling themes", async () => {
  const user = userEvent.setup();

  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  expect(screen.getByRole("button", { name: "城市骑行运动极简" })).toHaveAttribute("aria-pressed", "true");

  await user.click(screen.getByRole("button", { name: "户外路线手账" }));

  expect(document.documentElement).toHaveAttribute("data-theme", "trail-journal");
  expect(screen.getByRole("button", { name: "户外路线手账" })).toHaveAttribute("aria-pressed", "true");
});

test("applies planner seed from rides summary handoff", () => {
  render(
    <MemoryRouter initialEntries={["/?intent=ride_plan&seedQuery=%E8%BF%99%E5%91%A8%E5%86%8D%E5%AE%89%E6%8E%92%E4%B8%80%E6%AC%A1%E8%BD%BB%E6%9D%BE%E9%AA%91&handoffSource=monthly_summary&handoffActionKey=maintain_weekly_rhythm&handoffScene=city_ride&handoffStatus=steady&handoffRideCount=2&handoffWeeklyStreak=3&handoffRecentRideCount=3&handoffOriginRegion=%E6%BB%A8%E6%B1%9F&handoffMonth=2026-06&handoffSuggestedHours=2"]}>
      <HomePage />
    </MemoryRouter>,
  );

  expect(screen.getByRole("button", { name: "帮我安排一次骑行" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByDisplayValue("这周再安排一次轻松骑")).toBeInTheDocument();
  expect(screen.getByText("已从月度总结带入这次规划上下文")).toBeInTheDocument();
  expect(screen.getByText("来源：月度总结")).toBeInTheDocument();
  expect(screen.getByText("连续 3 周")).toBeInTheDocument();
});

test("prefills structured planner fields from rides handoff context", async () => {
  const user = userEvent.setup();

  render(
    <MemoryRouter initialEntries={["/?intent=ride_plan&seedQuery=%E8%BF%99%E5%91%A8%E5%86%8D%E5%AE%89%E6%8E%92%E4%B8%80%E6%AC%A1%E8%BD%BB%E6%9D%BE%E9%AA%91&handoffSource=monthly_summary&handoffActionKey=maintain_weekly_rhythm&handoffScene=city_ride&handoffStatus=steady&handoffRideCount=2&handoffWeeklyStreak=3&handoffRecentRideCount=3&handoffOriginRegion=%E6%BB%A8%E6%B1%9F&handoffMonth=2026-06&handoffSuggestedHours=2"]}>
      <HomePage />
    </MemoryRouter>,
  );

  await user.click(screen.getByRole("button", { name: "表单规划" }));

  expect(screen.getByLabelText("出发片区")).toHaveValue("滨江");
  expect(screen.getByLabelText("可骑时长")).toHaveValue(2);
});

test("submits planner request with structured handoff context", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/v1/ride/chat/turn") {
      return {
        ok: true,
        json: async () => ({
          assistant_name: "AAA骑车帮帮",
          intent: "ride_plan",
          assistant_message: "好的，我直接按这个方向给你规划。",
          slot_state: {},
          missing_slots: [],
          ready_to_plan: true,
          planner_request: {
            intent: "ride_plan",
            query: "这周再安排一次轻松骑",
            target_date: "2026-05-30",
            planning_mode: "route",
            planning_scene: "city_ride",
            input_mode: "natural",
          },
          ui_hints: {},
        }),
      };
    }
    if (url === "/api/v1/ride/plan/stream") {
      return {
        ok: false,
        status: 503,
      };
    }
    if (url === "/api/v1/ride/plan") {
      return {
        ok: true,
        json: async () => ({
          status: "success",
          request_no: "RQ-TEST-1",
          intent: "ride_plan",
          planning_mode: "route",
          parsed_constraints: {
            intent: "ride_plan",
            planning_mode: "route",
            planning_scene: "city_ride",
            start_point: "闻涛路滨江段",
            origin_region: "滨江",
            available_hours: 2,
          },
          input_summary: {
            intent: "ride_plan",
            input_mode: "natural",
            target_date: "2026-05-30",
            city_code: "hangzhou",
            defaults_applied: [],
          },
          recommended_plan: {
            go_decision: "go",
            route_name: "滨江轻松骑",
            route_code: "HZ-RIVER-001",
            distance_km: 28,
            elevation_gain_m: 120,
            estimated_duration_hours: 2,
            risk_level: "low",
            summary_reason: "适合轻松续节奏",
          },
          alternatives: [],
          weather_snapshot: {
            region_code: "binjiang",
            forecast_date: "2026-05-30",
            temperature_min: 22,
            temperature_max: 30,
            precipitation_probability: 0.1,
            wind_speed: 3.2,
            wind_direction: "SE",
            weather_summary: "cloudy",
            provider_name: "stub",
            raw_payload: {},
          },
          fallback_reason: [],
          tool_trace: [],
          decision: {
            intent: "ride_plan",
            scene: "city_ride",
            go_decision: "go",
            title: "这次可以骑，优先按主推荐执行",
            summary: "按轻松续节奏来安排",
          },
          plan: {
            kind: "route",
            code: "HZ-RIVER-001",
            title: "滨江轻松骑",
            summary: "按轻松续节奏来安排",
            distance_km: 28,
            elevation_gain_m: 120,
            estimated_duration_hours: 2,
            risk_level: "low",
          },
          alternative_plans: [],
          explanation: {
            headline: "按轻松续节奏来安排",
            summary: "按轻松续节奏来安排",
            confidence_notes: [],
          },
          risk: {
            level: "low",
            items: [],
            fallback_plan: "无",
          },
          equipment: {
            items: ["水壶"],
          },
          fallback: {
            status: "stable",
            reasons: [],
            message: null,
          },
          decision_summary: {
            scene: "city_ride",
            go_decision: "go",
            decision_title: "这次可以骑，优先按主推荐执行",
            decision_reason: "适合轻松续节奏",
            confidence_notes: [],
            equipment_advice: ["水壶"],
          },
        }),
      };
    }
    throw new Error(`unexpected fetch:${url}`);
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter initialEntries={["/?intent=ride_plan&seedQuery=%E8%BF%99%E5%91%A8%E5%86%8D%E5%AE%89%E6%8E%92%E4%B8%80%E6%AC%A1%E8%BD%BB%E6%9D%BE%E9%AA%91&handoffSource=monthly_summary&handoffActionKey=maintain_weekly_rhythm&handoffScene=city_ride&handoffStatus=steady&handoffRideCount=2&handoffWeeklyStreak=3&handoffRecentRideCount=3&handoffOriginRegion=%E6%BB%A8%E6%B1%9F&handoffMonth=2026-06&handoffSuggestedHours=2"]}>
      <HomePage />
    </MemoryRouter>,
  );

  await user.click(screen.getByRole("button", { name: "发送" }));

  await waitFor(() => {
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/ride/plan",
      expect.objectContaining({
        method: "POST",
      }),
    );
  });

  const planCall = fetchMock.mock.calls.find(([input]) => String(input) === "/api/v1/ride/plan");
  expect(planCall).toBeDefined();
  const requestBody = JSON.parse(String(planCall?.[1]?.body));
  expect(requestBody.handoff_context).toMatchObject({
    source: "monthly_summary",
    action_key: "maintain_weekly_rhythm",
    suggested_scene: "city_ride",
    status_key: "steady",
    ride_count: 2,
    weekly_streak: 3,
    recent_ride_count: 3,
    origin_region: "滨江",
    suggested_duration_hours: 2,
  });
});
