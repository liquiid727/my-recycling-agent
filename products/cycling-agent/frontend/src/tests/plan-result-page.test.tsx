import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";

import PlanResultPage from "../pages/PlanResultPage";

test("renders the editorial result page", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        request_no: "RQ-EXP-001",
        scene: "city_ride",
        editorial_intro: "今晚适合轻松骑，我先给你留一条江边的小计划。",
        decision: {
          title: "今晚适合轻松骑",
          reason: "风向和温度都比较稳，路线也容易收得住。",
          confidence_notes: ["实时天气正常", "路线补给稳定"],
        },
        route_story: {
          route_code: "HZ-RIVER-001",
          route_name: "河边拿铁停靠点",
          summary: "风景轻松，也适合停下来喝口水。",
          tags: ["low"],
          distance_km: 12,
          estimated_duration_hours: 1.2,
        },
        support_notes: ["带一瓶水", "薄外套"],
        ride_journal_prompt: "如果这趟骑行只留下一个片段，你会想把哪一幕写进今天的日记？",
        alternative_routes: [],
      }),
    })),
  );

  render(
    <MemoryRouter initialEntries={["/plans/RQ-EXP-001"]}>
      <Routes>
        <Route path="/plans/:requestNo" element={<PlanResultPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("今晚适合轻松骑")).toBeInTheDocument();
  expect(screen.getByText("河边拿铁停靠点")).toBeInTheDocument();
  expect(screen.getByText("如果这趟骑行只留下一个片段，你会想把哪一幕写进今天的日记？")).toBeInTheDocument();
});
