import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import PlannerPage from "../pages/PlannerPage";

test("renders the planner page shell with chat-first planner affordances", () => {
  render(
    <MemoryRouter>
      <PlannerPage />
    </MemoryRouter>,
  );

  expect(screen.getByText("AGENT PLANNER")).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: /把路线咨询主流程接回当前产品界面/i })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "开始规划" })).toBeInTheDocument();
  expect(screen.getByPlaceholderText("比如：我在闻涛路滨江段，今晚想轻松骑 2 小时，最好有江边和咖啡。")).toBeInTheDocument();
});

test("submits through the original ride chat and ride plan flow", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);

    if (url === "/api/v1/ride/chat/turn") {
      return {
        ok: true,
        json: async () => ({
          assistant_name: "AAA骑车帮帮",
          assistant_message: "收到，我先看天气和路线难度。",
          slot_state: { planning_scene: "city_ride", start_point: "闻涛路滨江段", available_hours: 2 },
          missing_slots: [],
          ready_to_plan: true,
          planner_request: {
            query: "AAA骑车帮帮结构化规划：闻涛路滨江段出发",
            target_date: "2026-05-30",
            planning_mode: "route",
            planning_scene: "city_ride",
            input_mode: "structured",
            structured_constraints: {
              start_point: "闻涛路滨江段",
              available_hours: 2,
              ride_style: "scenic_relaxed",
              slope_tolerance: "avoid",
              destination_preferences: ["江边", "咖啡"],
            },
          },
          ui_hints: {
            quick_replies: ["换轻松点", "缩短到 1 小时"],
            planning_status_label: "我在看天气和路线难度",
          },
        }),
      };
    }

    if (url === "/api/v1/ride/plan/stream") {
      return { ok: false, status: 500 };
    }

    if (url === "/api/v1/ride/plan") {
      return {
        ok: true,
        json: async () => ({
          request_no: "RQ-PLANNER-001",
          status: "success",
          planning_mode: "route",
          parsed_constraints: { start_point: "闻涛路滨江段", available_hours: 2, ride_style: "scenic_relaxed" },
          clarification_prompt: null,
          no_match_reason: null,
          recommended_plan: {
            go_decision: "go",
            route_name: "闻涛路-江边咖啡轻松环线",
            route_code: "DYN-HANGZHOU-LOOP",
            distance_km: 17.3,
            elevation_gain_m: 0,
            estimated_duration_hours: 1.13,
            risk_level: "low",
            summary_reason: "基于闻涛路滨江段周边多个 POI 和骑行路径动态扩张生成，更适合按计划时长休闲骑。",
          },
          alternatives: [],
          weather_snapshot: {
            region_code: "binjiang",
            forecast_date: "2026-05-30",
            temperature_min: 22,
            temperature_max: 29,
            precipitation_probability: 0.12,
            wind_speed: 3.2,
            wind_direction: "SE",
            weather_summary: "cloudy",
            provider_name: "stub",
            raw_payload: {},
          },
          fallback_reason: [],
          tool_trace: [
            {
              stage_name: "query_parser",
              status: "success",
              provider_name: "openai-compatible-llm",
              summary: "Parsed query with LLM provider.",
              fallback_reason: null,
            },
          ],
          decision_summary: {
            scene: "city_ride",
            go_decision: "go",
            decision_title: "这次可以骑，优先按主推荐执行",
            decision_reason: "基于闻涛路滨江段周边多个 POI 和骑行路径动态扩张生成，更适合按计划时长休闲骑。",
            confidence_notes: ["风险等级：low"],
            equipment_advice: [],
          },
          route_map: null,
          roadbook: null,
        }),
      };
    }

    throw new Error(`unexpected fetch ${url}`);
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <PlannerPage />
    </MemoryRouter>,
  );

  await user.click(screen.getByRole("button", { name: "开始规划" }));

  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/v1/ride/chat/turn", expect.objectContaining({ method: "POST" })));
  await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/v1/ride/plan", expect.objectContaining({ method: "POST" })));
  expect(await screen.findByText("闻涛路-江边咖啡轻松环线")).toBeInTheDocument();
});
