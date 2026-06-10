/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach } from "vitest";

import HomePage from "../pages/HomePage";

beforeEach(() => {
  document.documentElement.removeAttribute("data-theme");
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
  expect(screen.getByRole("button", { name: "今晚轻松骑" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "骑 2 小时" })).toBeInTheDocument();
  expect(screen.getByPlaceholderText("例如：我今天晚上想出去骑行一下")).toBeInTheDocument();
});

test("renders city ride and weekend trip planning scenes separately", () => {
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>,
  );

  expect(screen.getByRole("button", { name: "今晚 / 下午骑一下" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByRole("button", { name: "周末骑行出行" })).toHaveAttribute("aria-pressed", "false");
  expect(screen.getByText("市区内即时骑行决策")).toBeInTheDocument();
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
