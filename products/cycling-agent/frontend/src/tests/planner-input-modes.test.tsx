/*
 * CN: 前端测试文件，验证规划输入模式、缺失信息补全和结构化提交载荷。
 * EN: Frontend tests for planner input modes, missing-field completion, and structured payloads.
 */

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import HomePage from "../pages/HomePage";

test("switches between natural language and structured planner inputs", async () => {
  const user = userEvent.setup();

  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  expect(screen.getByRole("button", { name: "一句话描述" })).toHaveAttribute("aria-pressed", "true");
  await user.click(screen.getByRole("button", { name: "表单规划" }));

  expect(screen.getByLabelText("出发片区")).toBeInTheDocument();
  expect(screen.getByLabelText("准确出发地点")).toBeInTheDocument();
  expect(screen.getByLabelText("目标日期")).toBeInTheDocument();
});

test("structured planner treats exact start point as primary and can fill it from suggestions", async () => {
  const user = userEvent.setup();

  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  await user.click(screen.getByRole("button", { name: "表单规划" }));

  expect(screen.getByText("准确出发地点")).toBeInTheDocument();
  expect(screen.getByLabelText("出发片区")).toHaveDisplayValue("滨江");
  await user.click(screen.getByRole("button", { name: "杨公堤南口" }));

  expect(screen.getByLabelText("准确出发地点")).toHaveValue("杨公堤南口");
  expect(screen.getByLabelText("出发片区")).toHaveDisplayValue("西湖");
});

test("natural chat asks warm follow-up when key ride slots are missing", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn(async (url: string) => {
    if (url === "/api/v1/ride/chat/turn") {
      return {
        ok: true,
        json: async () => ({
          assistant_name: "AAA骑车帮帮",
          intent: "ride_today",
          assistant_message: "可以呀～今晚轻松骑挺合适。我先确认两件事：你现在从哪里出发？大概想骑多久？",
          slot_state: { planning_scene: "city_ride", duration_bucket: "evening" },
          missing_slots: ["start_point", "available_hours"],
          ready_to_plan: false,
          planner_request: null,
          ui_hints: { quick_replies: ["沈塘桥出发", "骑 2 小时", "轻松点"] }
        })
      };
    }
    throw new Error(`unexpected fetch ${url}`);
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  await user.clear(screen.getByLabelText("骑行需求"));
  await user.type(screen.getByLabelText("骑行需求"), "我今天晚上想出去骑行一下");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("我今天晚上想出去骑行一下")).toBeInTheDocument();
  expect(await screen.findByText("可以呀～今晚轻松骑挺合适。我先确认两件事：你现在从哪里出发？大概想骑多久？")).toBeInTheDocument();
  expect(screen.queryByText("我先看一下这句话里够不够生成方案。")).not.toBeInTheDocument();
  expect(screen.queryByText(/当前还缺少关键信息/)).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "沈塘桥出发" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "发送" })).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("natural follow-up replies stay in chat and ready turn submits planner request", async () => {
  const user = userEvent.setup();
  let chatTurnCount = 0;
  const fetchMock = vi.fn(async (url: string) => {
    if (url === "/api/v1/ride/chat/turn") {
      chatTurnCount += 1;
      if (chatTurnCount === 1) {
        return {
          ok: true,
          json: async () => ({
            assistant_name: "AAA骑车帮帮",
            intent: "ride_today",
            assistant_message: "可以呀～今晚轻松骑挺合适。我先确认两件事：你现在从哪里出发？大概想骑多久？",
            slot_state: { planning_scene: "city_ride", duration_bucket: "evening" },
            missing_slots: ["start_point", "available_hours"],
            ready_to_plan: false,
            planner_request: null,
            ui_hints: { quick_replies: ["沈塘桥出发", "骑 2 小时", "不要爬坡"] }
          })
        };
      }
      return {
        ok: true,
        json: async () => ({
          assistant_name: "AAA骑车帮帮",
          intent: "ride_plan",
          assistant_message: "收到，沈塘桥出发，骑 2 小时，轻松一点。我先帮你看今晚适不适合骑，再给你 2-3 条稳妥路线。",
          slot_state: {
            planning_scene: "city_ride",
            start_point: "沈塘桥",
            available_hours: 2,
            slope_tolerance: "avoid"
          },
          missing_slots: [],
          ready_to_plan: true,
          planner_request: {
            intent: "ride_plan",
            query: "我今天晚上想出去骑行一下；沈塘桥，我这里想要骑行2h",
            target_date: "2026-05-30",
            planning_mode: "route",
            planning_scene: "city_ride",
            input_mode: "structured",
            structured_constraints: {
              start_point: "沈塘桥",
              available_hours: 2,
              slope_tolerance: "avoid",
              ride_style: "scenic_relaxed"
            }
          },
          ui_hints: { quick_replies: ["换轻松点", "缩短到 1 小时", "避开爬坡"], planning_status_label: "我在看天气和路线难度" }
        })
      };
    }
    if (url === "/api/v1/ride/plan/stream") {
      return { ok: false, body: null, status: 503 };
    }
    return {
      ok: true,
      json: async () => ({
        request_no: "RQ-CHAT",
        status: "success",
        parsed_constraints: { planning_scene: "city_ride", start_point: "沈塘桥", available_hours: 2 },
        input_summary: {
          planning_scene: "city_ride",
          input_mode: "natural",
          target_date: "2026-05-30",
          city_code: "hangzhou",
          start_point: "沈塘桥",
          available_hours: 2,
          defaults_applied: []
        },
        clarification_prompt: null,
        no_match_reason: null,
        recommended_plan: {
          go_decision: "go",
          route_name: "滨江-钱塘江休闲往返线",
          route_code: "HZ-RIVER-001",
          distance_km: 32,
          elevation_gain_m: 80,
          estimated_duration_hours: 2,
          risk_level: "low",
          summary_reason: "今晚两小时轻松可骑。"
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
        decision_summary: {
          scene: "city_ride",
          go_decision: "go",
          decision_title: "这次可以骑，优先按主推荐执行",
          decision_reason: "今晚两小时轻松可骑。",
          confidence_notes: ["风险等级：low"],
          equipment_advice: ["夜骑装备：前后车灯、反光装备和轻薄防风层。"]
        },
        route_map: null,
        roadbook: null
      })
    };
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  await user.clear(screen.getByLabelText("骑行需求"));
  await user.type(screen.getByLabelText("骑行需求"), "我今天晚上想出去骑行一下");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("可以呀～今晚轻松骑挺合适。我先确认两件事：你现在从哪里出发？大概想骑多久？")).toBeInTheDocument();
  expect(screen.getByLabelText("骑行需求")).toHaveValue("");

  await user.type(screen.getByLabelText("骑行需求"), "沈塘桥，我这里想要骑行2h");
  await user.click(screen.getByRole("button", { name: "发送" }));

  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/v1/ride/plan", expect.anything()));
  expect(await screen.findByText("收到，沈塘桥出发，骑 2 小时，轻松一点。我先帮你看今晚适不适合骑，再给你 2-3 条稳妥路线。")).toBeInTheDocument();
  const secondChatTurnCall = fetchMock.mock.calls.filter(([url]) => url === "/api/v1/ride/chat/turn")[1] as unknown as
    | [string, RequestInit]
    | undefined;
  const chatBody = JSON.parse(secondChatTurnCall?.[1].body as string);
  expect(chatBody.intent).toBe("ride_today");
  expect(chatBody.messages.map((message: { content: string }) => message.content).join("；")).toContain("我今天晚上想出去骑行一下");
  expect(chatBody.messages.map((message: { content: string }) => message.content).join("；")).toContain("沈塘桥，我这里想要骑行2h");
  expect(chatBody.slot_state).toMatchObject({ planning_scene: "city_ride", duration_bucket: "evening" });

  const planCall = fetchMock.mock.calls.find(([url]) => url === "/api/v1/ride/plan") as [string, RequestInit] | undefined;
  const planBody = JSON.parse(planCall?.[1].body as string);
  expect(planBody.intent).toBe("ride_plan");
  expect(planBody.input_mode).toBe("structured");
  expect(planBody.structured_constraints).toMatchObject({ start_point: "沈塘桥", available_hours: 2 });
});

test("structured planner submits structured constraints in the request body", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn(async (url: string) => {
    if (url === "/api/v1/ride/plan/stream") {
      return { ok: false, body: null, status: 503 };
    }
    return {
      ok: true,
      json: async () => ({
        request_no: "RQ-STRUCTURED",
        status: "success",
        parsed_constraints: { origin_region: "滨江", available_hours: 3, ride_style: "scenic_relaxed" },
        input_summary: {
          planning_scene: "city_ride",
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
        decision_summary: {
          scene: "city_ride",
          go_decision: "go",
          decision_title: "这次可以骑，优先按主推荐执行",
          decision_reason: "时长匹配，轻松稳定。",
          confidence_notes: ["风险等级：low"],
          equipment_advice: ["基础装备：头盔、手套、补胎工具、随身水壶。"]
        },
        route_map: null,
        roadbook: null
      })
    };
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  await user.click(screen.getByRole("button", { name: "表单规划" }));
  await user.clear(screen.getByLabelText("准确出发地点"));
  await user.type(screen.getByLabelText("准确出发地点"), "闻涛路滨江段");
  await user.clear(screen.getByLabelText("可骑时长"));
  await user.type(screen.getByLabelText("可骑时长"), "3");
  await user.clear(screen.getByLabelText("目标距离"));
  await user.type(screen.getByLabelText("目标距离"), "42");
  await user.click(screen.getByRole("button", { name: "开始规划" }));

  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/v1/ride/plan", expect.anything()));
  const planCall = fetchMock.mock.calls.find(([url]) => url === "/api/v1/ride/plan") as
    | [string, RequestInit]
    | undefined;
  const body = JSON.parse(planCall?.[1].body as string);
  expect(body.intent).toBe("ride_today");
  expect(body.input_mode).toBe("structured");
  expect(body.planning_scene).toBe("city_ride");
  expect(body.structured_constraints).toMatchObject({
    origin_region: "滨江",
    start_point: "闻涛路滨江段",
    available_hours: 3,
    target_distance_km: 42,
    fitness_level: "medium",
    ride_style: "scenic_relaxed",
    slope_tolerance: "avoid",
    priority: "风景"
  });
});
