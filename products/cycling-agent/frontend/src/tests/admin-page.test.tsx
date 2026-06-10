/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import AdminPage from "../pages/AdminPage";

test("loads admin data and submits a new strategy rule", async () => {
  const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
    if (!init?.method || init.method === "GET") {
      if (url.includes("/api/v1/admin/routes")) {
        return {
          ok: true,
          json: async () => [
            {
              route_code: "HZ-RIVER-001",
              name: "滨江-钱塘江休闲往返线",
              city_code: "hangzhou",
              start_point_name: "闻涛路滨江段",
              district_tags: ["滨江", "钱塘江"],
              ride_style_tags: ["relaxed", "scenic"],
              best_time_slots: ["06:30-09:30"],
              distance_km: 42,
              elevation_gain_m: 180,
              estimated_duration_hours: 2.8,
              difficulty_level: "easy",
              traffic_level: "low",
              supply_score: 8,
              return_difficulty_score: 3,
              scenic_score: 8,
              training_score: 4,
              beginner_friendly: true,
              supply_points: [{ name: "闻涛路便利店", km_mark: 4, type: "便利店" }],
              bailout_options: [{ name: "奥体中途折返", km_mark: 18, reason: "保留江景主段" }],
              weather_sensitivity: { heat: "medium", rain: "medium", crosswind: "medium" },
              route_notes: "适合周末晨骑。"
            }
          ]
        };
      }
      if (url.includes("/api/v1/admin/city-strategy")) {
        return {
          ok: true,
          json: async () => [],
        };
      }
      if (url.includes("/api/v1/admin/risk-rules")) {
        return {
          ok: true,
          json: async () => [],
        };
      }
      if (url.includes("/api/v1/admin/nearby-destinations")) {
        return {
          ok: true,
          json: async () => [
            {
              destination_no: "DST-HZ-RIVER-CAFE",
              city_code: "hangzhou",
              name: "钱塘江滨江咖啡休息带",
              destination_type: "咖啡",
              region_tags: ["滨江", "钱塘江", "江边", "咖啡"],
              suitable_duration: ["half_day"],
              stay_duration_minutes: 60,
              crowd_level: { weekday: "low", weekend: "medium", holiday: "high" },
              supply_summary: "江边咖啡、便利店和奥体周边补给稳定。",
              public_transport_options: ["地铁 6 号线奥体中心站返程"],
              stay_suggestion: "到达后停留 45 到 60 分钟。"
            }
          ],
        };
      }
      if (url.includes("/api/v1/admin/trip-templates")) {
        return {
          ok: true,
          json: async () => [
            {
              trip_no: "TRIP-HZ-RIVER-CAFE",
              city_code: "hangzhou",
              route_template_id: "HZ-RIVER-001",
              destination_no: "DST-HZ-RIVER-CAFE",
              name: "钱塘江沿线亲水骑 + 江边咖啡",
              origin_region_tags: ["滨江"],
              total_duration_hours: 4.5,
              ride_duration_hours: 2.8,
              trip_style_tags: ["half_day", "江边", "咖啡"],
              return_mode_options: ["骑回", "公共交通返程"],
              fallback_plan: "天气转差时缩短到奥体折返。"
            }
          ],
        };
      }
      return {
        ok: true,
        json: async () => [
          {
            request_no: "RQ-TEST0001",
            query: "周六从滨江出发骑3小时",
            target_date: "2026-05-30",
            parsed_constraints: { origin_region: "滨江" },
            recommended_route_name: "滨江-钱塘江休闲往返线",
            fallback_reason: [],
            created_at: "2026-05-27 23:00:00"
          }
        ]
      };
    }

    return {
      ok: true,
      json: async () => JSON.parse(String(init.body))
    };
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter>
      <AdminPage />
    </MemoryRouter>,
  );

  expect((await screen.findAllByText("滨江-钱塘江休闲往返线")).length).toBeGreaterThan(0);
  expect(screen.getByText("周六从滨江出发骑3小时")).toBeInTheDocument();
  expect(screen.getByText("闻涛路滨江段")).toBeInTheDocument();
  expect(screen.getByText("钱塘江滨江咖啡休息带")).toBeInTheDocument();
  expect(screen.getByText("钱塘江沿线亲水骑 + 江边咖啡")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("规则键"), { target: { value: "longjing_heat_penalty" } });
  fireEvent.change(screen.getByLabelText("规则 JSON"), {
    target: {
      value:
        '{"target":"weather","delta":0.2,"conditions":{"district_tags_any":["龙井"],"temperature_max_gte":30,"weather_sensitivity_heat_in":["high"]}}'
    }
  });
  fireEvent.click(screen.getByRole("button", { name: "保存风险规则" }));

  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/risk-rules",
      expect.objectContaining({ method: "POST" })
    )
  );

  fireEvent.change(screen.getByLabelText("起点名称"), { target: { value: "新起点" } });
  fireEvent.change(screen.getByLabelText("推荐时间窗"), { target: { value: "07:00-09:00" } });
  fireEvent.change(screen.getByLabelText("补给点 JSON"), {
    target: { value: '[{"name":"新补给点","km_mark":6,"type":"便利店"}]' }
  });
  fireEvent.click(screen.getByRole("button", { name: "保存路线" }));

  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/routes",
      expect.objectContaining({ method: "POST" })
    )
  );

  fireEvent.change(screen.getByLabelText("目的地名称"), { target: { value: "后台江边咖啡点" } });
  fireEvent.click(screen.getByRole("button", { name: "保存目的地" }));

  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/nearby-destinations",
      expect.objectContaining({ method: "POST" })
    )
  );

  fireEvent.change(screen.getByLabelText("方案名称"), { target: { value: "后台江边咖啡半日骑" } });
  fireEvent.click(screen.getByRole("button", { name: "保存周边游模板" }));

  await waitFor(() =>
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/admin/trip-templates",
      expect.objectContaining({ method: "POST" })
    )
  );
});
