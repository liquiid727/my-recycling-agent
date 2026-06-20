import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import HomePage from "../pages/HomePage";

test("renders the editorial homepage and companion preview flow", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url === "/api/v1/experience/home") {
      return {
        ok: true,
        json: async () => ({
          hero: {
            eyebrow: "LIFESTYLE JOURNAL",
            title: "今天不训练，只是在城市里收集一点阳光。",
            lead: "Over Cycling 帮偶尔骑车的人找到轻松路线和停靠点。",
            primary_cta: "让 AI 伙伴帮我安排",
            secondary_cta: "看看周末建议",
          },
          today_nudges: [{ title: "天气便签", body: "傍晚温度刚好。" }],
          curated_routes: [{ route_code: "HZ-RIVER-001", section_label: "咖啡停靠页", title: "河边拿铁停靠点", summary: "顺着江边慢慢骑。", tags: ["江边", "咖啡"] }],
          companion_persona: {
            headline: "不是教练，是替你翻开周末的人。",
            description: "它记得你喜欢树荫、咖啡和不太拥挤的路。",
            quick_prompts: ["帮我生成一个不累的周末骑行计划"],
          },
          weekend_plan_templates: [{ slug: "coffee", title: "咖啡窗口", summary: "把路线和停靠点拼成小计划。" }],
          journal_cards: [{ label: "今天看到", title: "桥下有人吹萨克斯。" }],
          cta_footer: {
            quote: "如果今天只是想换一口空气，那也已经足够了。",
            lead: "打开 Over Cycling。",
            button_label: "从一句心情开始",
          },
        }),
      };
    }
    if (url === "/api/v1/experience/companion/plan") {
      return {
        ok: true,
        json: async () => ({
          status: "planned",
          assistant_message: "今晚适合轻松骑，我先给你留一条江边的小计划。",
          suggested_prompts: ["找一个可以顺路买咖啡的路线"],
          editorial_intro: "今晚适合轻松骑，我先给你留一条江边的小计划。",
          request_no: "RQ-EXP-001",
          featured_plan: {
            route_code: "HZ-RIVER-001",
            route_name: "河边拿铁停靠点",
            distance_km: 12,
            estimated_duration_hours: 1.2,
            risk_level: "low",
            summary_reason: "风景轻松，也适合停下来喝口水。",
          },
        }),
      };
    }
    throw new Error(`unexpected fetch ${url} ${init?.method ?? "GET"}`);
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  expect(await screen.findByText("今天不训练，只是在城市里收集一点阳光。")).toBeInTheDocument();
  expect(screen.getByText("天气便签")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "帮我生成一个不累的周末骑行计划" })).toBeInTheDocument();

  await user.type(screen.getByLabelText("今天的对话输入"), "我想去树多一点的地方轻松骑一圈");
  await user.click(screen.getByRole("button", { name: "发送" }));

  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/experience/companion/plan",
      expect.objectContaining({ method: "POST" }),
    ),
  );

  expect(await screen.findByText("今晚适合轻松骑，我先给你留一条江边的小计划。")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: /查看完整结果/i })).toHaveAttribute("href", "/plans/RQ-EXP-001");
});
