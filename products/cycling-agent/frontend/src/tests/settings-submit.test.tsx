import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import SettingsPage from "../pages/SettingsPage";

test("loads and saves lifestyle preferences", async () => {
  const user = userEvent.setup();
  window.localStorage.clear();
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (!init || init.method === "GET") {
      return {
        ok: true,
        json: async () => ({
          home_region: "滨江",
          preferred_vibe: "tree_shade",
          companion_tone: "gentle",
          favorite_motifs: ["树荫", "咖啡"],
          avoid_motifs: ["刷圈"],
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
      <SettingsPage />
    </MemoryRouter>,
  );

  expect(await screen.findByDisplayValue("滨江")).toBeInTheDocument();
  expect(screen.getByDisplayValue("tree_shade")).toBeInTheDocument();

  await user.clear(screen.getByLabelText("喜欢的意象"));
  await user.type(screen.getByLabelText("喜欢的意象"), "树荫, 咖啡, 日落");
  await user.selectOptions(screen.getByLabelText("默认身体状态"), "tired");
  await user.selectOptions(screen.getByLabelText("默认这次想怎么骑"), "recover");
  await user.selectOptions(screen.getByLabelText("默认上次骑行"), "3");
  await user.click(screen.getByRole("button", { name: "保存偏好" }));

  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/profile/lifestyle",
      expect.objectContaining({
        method: "PUT",
      }),
    ),
  );

  expect(JSON.parse(window.localStorage.getItem("cycling-agent-rider-state") ?? "{}")).toEqual({
    fatigue_level: "tired",
    mood: "recover",
    last_ride_days_ago: 3,
  });
  expect(await screen.findByText("偏好已保存")).toBeInTheDocument();
});
