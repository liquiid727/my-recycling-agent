import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import AdminPage from "../pages/AdminPage";

test("loads and saves experience content orchestration data", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn(async (_url: string, init?: RequestInit) => {
    if (!init?.method || init.method === "GET") {
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

    return {
      ok: true,
      json: async () => JSON.parse(String(init.body)),
    };
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <AdminPage />
    </MemoryRouter>,
  );

  expect(await screen.findByDisplayValue("今天不训练，只是在城市里收集一点阳光。")).toBeInTheDocument();
  expect(screen.getByDisplayValue("从一句心情开始")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "进入 Planner" })).toHaveAttribute("href", "/planner");

  await user.clear(screen.getByLabelText("首页标题"));
  await user.type(screen.getByLabelText("首页标题"), "今天不训练，只是在城市里收集一点晚风。");
  await user.click(screen.getByRole("button", { name: "保存内容" }));

  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/experience-content",
      expect.objectContaining({ method: "PUT" }),
    ),
  );
});
