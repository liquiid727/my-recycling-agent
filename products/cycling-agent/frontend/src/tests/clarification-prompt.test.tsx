import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import HomePage from "../pages/HomePage";

test("renders clarification reply when the companion still needs more context", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url === "/api/v1/experience/home") {
      return {
        ok: true,
        json: async () => ({
          hero: { eyebrow: "LIFESTYLE JOURNAL", title: "今天不训练，只是在城市里收集一点阳光。", lead: "lead", primary_cta: "让 AI 伙伴帮我安排", secondary_cta: "看看周末建议" },
          today_nudges: [],
          curated_routes: [],
          companion_persona: { headline: "不是教练，是替你翻开周末的人。", description: "desc", quick_prompts: ["推荐附近安静一点的公园"] },
          weekend_plan_templates: [],
          journal_cards: [],
          cta_footer: { quote: "quote", lead: "lead", button_label: "从一句心情开始" },
        }),
      };
    }
    if (url === "/api/v1/experience/companion/plan") {
      return {
        ok: true,
        json: async () => ({
          status: "clarification",
          assistant_message: "告诉我你从哪里出发，想骑多久，我就能给你一页轻计划。",
          suggested_prompts: ["推荐附近安静一点的公园"],
          editorial_intro: null,
          request_no: null,
          featured_plan: null,
        }),
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

  await user.type(await screen.findByLabelText("今天的对话输入"), "今天想出去骑一下");
  await user.click(screen.getByRole("button", { name: "发送" }));

  expect(await screen.findByText("告诉我你从哪里出发，想骑多久，我就能给你一页轻计划。")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "推荐附近安静一点的公园" })).toBeInTheDocument();
});
