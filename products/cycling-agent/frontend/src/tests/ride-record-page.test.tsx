import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, vi } from "vitest";

import RideRecordDetailPage from "../pages/RideRecordDetailPage";
import RideRecordPage from "../pages/RideRecordPage";

const plannedRidePlan = {
  status: "success",
  request_no: "RQ-TEST0001",
  intent: "ride_plan",
  planning_mode: "route",
  parsed_constraints: { start_point: "闻涛路滨江段", origin_region: "滨江" },
  input_summary: {
    intent: "ride_plan",
    planning_mode: "route",
    planning_scene: "city_ride",
    input_mode: "structured",
    target_date: "2026-06-15",
    city_code: "hangzhou",
    start_point: "闻涛路滨江段",
    origin_region: "滨江",
    available_hours: 3,
    defaults_applied: [],
  },
  plan: {
    kind: "route",
    code: "HZ-RIVER-001",
    title: "滨江-钱塘江休闲往返线",
    summary: "适合晚风稳态巡航的江边轻松线。",
    distance_km: 42,
    elevation_gain_m: 180,
    estimated_duration_hours: 2.8,
    destination_name: "钱塘江南岸",
  },
  recommended_plan: {
    go_decision: "go",
    route_name: "滨江-钱塘江休闲往返线",
    route_code: "HZ-RIVER-001",
    distance_km: 42,
    elevation_gain_m: 180,
    estimated_duration_hours: 2.8,
    risk_level: "low",
    summary_reason: "时长稳定，适合按计划完成。"
  },
  alternatives: [],
  weather_snapshot: {
    region_code: "binjiang",
    forecast_date: "2026-06-15",
    temperature_min: 23,
    temperature_max: 30,
    precipitation_probability: 0.1,
    wind_speed: 3.8,
    wind_direction: "SE",
    weather_summary: "cloudy",
    provider_name: "stub",
    raw_payload: {}
  },
  fallback_reason: [],
  tool_trace: [],
  roadbook: null
};

const createdRideRecord = {
  ride_record: {
    ride_record_no: "RR-TEST0001",
    entry_mode: "planned",
    source_request_no: "RQ-TEST0001",
    ride_date: "2026-06-15",
    intent: "ride_plan",
    plan_kind: "route",
    route_code: "HZ-RIVER-001",
    route_title: "滨江-钱塘江休闲往返线",
    destination_name: "钱塘江南岸",
    start_point: "闻涛路滨江段",
    origin_region: "滨江",
    completion_status: "completed",
    actual_duration_hours: 2.8,
    actual_distance_km: 41.2,
    effort_feeling: "steady",
    mood_after: "refreshed",
    notes: "后半段有点逆风，但整体稳定。",
    tags: ["晚骑", "江边"]
  },
  ride_summary: {
    headline: "滨江-钱塘江休闲往返线这次完成得很稳。",
    summary: "整体按计划推进，节奏和收尾反馈都比较顺。",
    completion_assessment: "completed-as-planned",
    effort_assessment: "matched-expected-effort",
    recovery_advice: "补水和轻拉伸即可。",
    next_ride_prompt: "下次可以继续安排相近时长。",
    plan_alignment: "matched-core-plan",
    confidence_notes: ["已参考原计划时长做对齐判断。"]
  }
};

afterEach(() => {
  vi.unstubAllGlobals();
});

test("planned entry shows estimate as reference only and does not submit fake actual duration by default", async () => {
  const user = userEvent.setup();
  let postedBody: Record<string, unknown> | null = null;
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/v1/ride/plan/RQ-TEST0001") {
        return { ok: true, json: async () => plannedRidePlan };
      }
      if (url === "/api/v1/rides/records" && init?.method === "POST") {
        postedBody = JSON.parse(String(init.body));
        return { ok: true, json: async () => createdRideRecord };
      }
      if (url === "/api/v1/rides/records/RR-TEST0001") {
        return { ok: true, json: async () => createdRideRecord };
      }
      throw new Error(`unexpected fetch: ${url}`);
    }),
  );

  render(
    <MemoryRouter initialEntries={["/rides/new?sourceRequestNo=RQ-TEST0001"]}>
      <Routes>
        <Route path="/rides/new" element={<RideRecordPage />} />
        <Route path="/rides/:rideRecordNo" element={<RideRecordDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(screen.getByText("正在加载关联规划...")).toBeInTheDocument();
  expect(await screen.findByText("滨江-钱塘江休闲往返线")).toBeInTheDocument();
  expect(screen.getByText("2.8 h 预计骑行")).toBeInTheDocument();
  expect(screen.getByLabelText("实际时长（小时）")).toHaveValue(null);

  await user.clear(screen.getByLabelText("实际距离（km）"));
  await user.type(screen.getByLabelText("实际距离（km）"), "41.2");
  await user.type(screen.getByLabelText("备注"), "后半段有点逆风，但整体稳定。");
  await user.type(screen.getByLabelText("标签（逗号分隔）"), "晚骑, 江边");
  await user.click(screen.getByRole("button", { name: "保存骑行记录" }));

  expect(await screen.findByText("滨江-钱塘江休闲往返线这次完成得很稳。")).toBeInTheDocument();
  expect(screen.getByText("记录编号：RR-TEST0001")).toBeInTheDocument();
  expect(postedBody).toMatchObject({
    entry_mode: "planned",
    source_request_no: "RQ-TEST0001",
    ride_date: "2026-06-15",
    completion_status: "completed",
    actual_distance_km: 41.2,
    effort_feeling: "steady",
    mood_after: "refreshed",
    notes: "后半段有点逆风，但整体稳定。",
    tags: ["晚骑", "江边"],
  });
  expect(postedBody).not.toHaveProperty("actual_duration_hours");
  expect(postedBody).not.toHaveProperty("route_code");
});

test("manual entry validates required fields before submit", async () => {
  const user = userEvent.setup();
  const fetchMock = vi.fn();
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter initialEntries={["/rides/new"]}>
      <Routes>
        <Route path="/rides/new" element={<RideRecordPage />} />
      </Routes>
    </MemoryRouter>,
  );

  await user.click(screen.getByRole("button", { name: "保存骑行记录" }));

  expect(screen.getByRole("alert")).toHaveTextContent("手动补录至少填写路线标题或目的地。");
  expect(fetchMock).not.toHaveBeenCalled();
});

test("manual entry submits the expected payload fields", async () => {
  const user = userEvent.setup();
  let postedBody: Record<string, unknown> | null = null;
  const manualRideRecord = {
    ...createdRideRecord,
    ride_record: {
      ...createdRideRecord.ride_record,
      ride_record_no: "RR-MANUAL001",
      entry_mode: "manual",
      source_request_no: null,
      route_code: null,
      route_title: "湘湖绕湖骑",
      destination_name: "湘湖",
      start_point: "湘湖游客中心",
      origin_region: "萧山",
      completion_status: "shortened",
      actual_duration_hours: 1.6,
      actual_distance_km: null,
      notes: "下午太晒，提前收了。",
      tags: ["补录", "短收"],
    },
  };

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/v1/rides/records" && init?.method === "POST") {
        postedBody = JSON.parse(String(init.body));
        return { ok: true, json: async () => manualRideRecord };
      }
      if (url === "/api/v1/rides/records/RR-MANUAL001") {
        return { ok: true, json: async () => manualRideRecord };
      }
      throw new Error(`unexpected fetch: ${url}`);
    }),
  );

  render(
    <MemoryRouter initialEntries={["/rides/new"]}>
      <Routes>
        <Route path="/rides/new" element={<RideRecordPage />} />
        <Route path="/rides/:rideRecordNo" element={<RideRecordDetailPage />} />
      </Routes>
    </MemoryRouter>,
  );

  const rideDate = (screen.getByLabelText("骑行日期") as HTMLInputElement).value;
  await user.type(screen.getByLabelText("路线标题"), "湘湖绕湖骑");
  await user.type(screen.getByLabelText("目的地"), "湘湖");
  await user.type(screen.getByLabelText("起点"), "湘湖游客中心");
  await user.type(screen.getByLabelText("出发区域"), "萧山");
  await user.selectOptions(screen.getByLabelText("完成情况"), "shortened");
  await user.type(screen.getByLabelText("实际时长（小时）"), "1.6");
  await user.type(screen.getByLabelText("备注"), "下午太晒，提前收了。");
  await user.type(screen.getByLabelText("标签（逗号分隔）"), "补录, 短收");
  await user.click(screen.getByRole("button", { name: "保存骑行记录" }));

  expect(await screen.findByText("记录编号：RR-MANUAL001")).toBeInTheDocument();
  expect(postedBody).toEqual({
    entry_mode: "manual",
    ride_date: rideDate,
    route_title: "湘湖绕湖骑",
    destination_name: "湘湖",
    start_point: "湘湖游客中心",
    origin_region: "萧山",
    completion_status: "shortened",
    actual_duration_hours: 1.6,
    effort_feeling: "steady",
    mood_after: "refreshed",
    notes: "下午太晒，提前收了。",
    tags: ["补录", "短收"],
  });
});

test("shows actionable validation and submit errors on planned entry", async () => {
  const user = userEvent.setup();
  let resolvePlan!: (value: {
    ok: boolean;
    json: () => Promise<typeof plannedRidePlan>;
  }) => void;

  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url === "/api/v1/ride/plan/RQ-TEST0001") {
        return new Promise((resolve) => {
          resolvePlan = resolve;
        });
      }
      if (url === "/api/v1/rides/records" && init?.method === "POST") {
        return Promise.resolve({
          ok: false,
          status: 404,
          json: async () => ({ detail: "ride-record-source-plan-not-found" }),
        });
      }
      throw new Error(`unexpected fetch: ${url}`);
    }),
  );

  render(
    <MemoryRouter initialEntries={["/rides/new?sourceRequestNo=RQ-TEST0001"]}>
      <Routes>
        <Route path="/rides/new" element={<RideRecordPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(screen.getByText("正在加载关联规划...")).toBeInTheDocument();

  resolvePlan({ ok: true, json: async () => plannedRidePlan });

  expect(await screen.findByText("滨江-钱塘江休闲往返线")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "保存骑行记录" }));

  expect(screen.getByRole("alert")).toHaveTextContent("已完成的骑行至少填写实际时长或实际距离之一。");

  await user.type(screen.getByLabelText("实际距离（km）"), "35");
  await user.click(screen.getByRole("button", { name: "保存骑行记录" }));

  await waitFor(() => {
    expect(screen.getByRole("alert")).toHaveTextContent("关联的原规划不存在，建议返回结果页重新打开后再记录。");
  });
});
