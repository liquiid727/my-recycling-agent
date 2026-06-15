/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import HomePage from "../pages/HomePage";

test("submits query and shows loading state", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url === "/api/v1/ride/chat/turn") {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            assistant_name: "AAA骑车帮帮",
            intent: "ride_plan",
            assistant_message: "收到，滨江出发，骑 3 小时。我先帮你看今晚适不适合骑。",
            slot_state: { start_point: "滨江", available_hours: 3 },
            missing_slots: [],
            ready_to_plan: true,
            planner_request: {
              query: "周六从滨江出发骑3小时，不想太累",
              target_date: "2026-05-30",
              planning_mode: "route",
              planning_scene: "city_ride",
              input_mode: "structured",
              structured_constraints: { start_point: "滨江", available_hours: 3 }
            },
            ui_hints: { planning_status_label: "我在看天气和路线难度" }
          })
        });
      }
      return new Promise(() => {});
    }),
  );

  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  fireEvent.change(screen.getByLabelText("骑行需求"), {
    target: { value: "周六从滨江出发骑3小时，不想太累" }
  });
  fireEvent.click(screen.getByRole("button", { name: "发送" }));

  expect((await screen.findAllByText("我在看天气和路线难度")).length).toBeGreaterThan(0);
});

test("shows staged planner feedback while stream is active", async () => {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      controller.enqueue(
        encoder.encode(
          'event: planning_started\ndata: {"summary":"started"}\n\n' +
            'event: stage_update\ndata: {"stage_name":"query_parser","status":"success","provider_name":"rule-fallback","summary":"Parsed query.","fallback_reason":null}\n\n',
        ),
      );
    }
  });

  vi.stubGlobal(
    "fetch",
    vi.fn((url: string) => {
      if (url === "/api/v1/ride/chat/turn") {
        return Promise.resolve({
          ok: true,
          json: async () => ({
            assistant_name: "AAA骑车帮帮",
            intent: "ride_plan",
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
          })
        });
      }
      return Promise.resolve(
        new Response(stream, {
          status: 200,
          headers: { "Content-Type": "text/event-stream" }
        }),
      );
    }),
  );

  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  fireEvent.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByRole("listitem")).toHaveTextContent("Parsed query.");
});
