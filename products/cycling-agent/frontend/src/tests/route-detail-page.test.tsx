import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import RouteDetailPage from "../pages/RouteDetailPage";

test("renders the editorial route detail page", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        route_code: "HZ-RIVER-001",
        route_name: "河边拿铁停靠点",
        headline: "河边拿铁停靠点：给今天留一段顺风和空白",
        summary: "顺着江边慢慢骑，路上留一个不赶时间的窗口。",
        tags: ["江边", "咖啡"],
        best_time_slots: ["06:30-09:30"],
        supply_points: [{ name: "闻涛路便利店", km_mark: 4, type: "便利店" }],
        bailout_options: [{ name: "奥体中途折返", km_mark: 18, reason: "保留江景主段" }],
      }),
    })),
  );

  render(
    <MemoryRouter initialEntries={["/routes/HZ-RIVER-001"]}>
      <Routes>
        <Route path="/routes/:routeCode" element={<RouteDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("河边拿铁停靠点：给今天留一段顺风和空白")).toBeInTheDocument();
  expect(screen.getByText("闻涛路便利店")).toBeInTheDocument();
  expect(screen.getByText("奥体中途折返")).toBeInTheDocument();
});
