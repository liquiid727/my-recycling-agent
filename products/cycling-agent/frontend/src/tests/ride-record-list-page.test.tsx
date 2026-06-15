import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, vi } from "vitest";

import RideRecordsPage from "../pages/RideRecordsPage";

afterEach(() => {
  vi.unstubAllGlobals();
});

test("renders recent ride records with detail links", async () => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/v1/rides/growth-review?window_days=")) {
      return {
        ok: true,
        json: async () => ({
          ride_growth_review: {
            window_days: 90,
            period_start: "2026-03-18",
            period_end: "2026-06-15",
            ride_count: 4,
            ride_day_count: 4,
            completed_count: 3,
            total_distance_km: 154,
            total_duration_hours: 8.6,
            longest_distance_km: 58,
            longest_duration_hours: 3.2,
            active_month_count: 3,
            best_weekly_streak: 3,
            planned_count: 2,
            manual_count: 2,
            matched_plan_count: 2,
            top_start_region: "滨江",
            top_tag: "周末",
            recent_vs_previous_ride_delta: 2,
            recent_vs_previous_distance_delta_km: 68,
            growth_status: "expanding",
            review_headline: "最近这段时间，你的骑行范围已经明显打开了。",
            review_body: "近 30 天的骑行次数和距离都比前一段更高，说明你不只是续上了节奏，还在往外扩。",
            next_focus: {
              action_key: "maintain_weekly_rhythm",
              title: "按这个方向继续安排",
              body: "下一次可以把周末半天骑继续保留住，不用再额外追强度。",
              suggested_scene: "weekend_trip",
              suggested_entry: "这个周末安排一次 3 到 4 小时、带一点爬升的半天骑。"
            },
            milestones: [
              {
                milestone_key: "longest_distance",
                title: "最长距离刷新到 58 km",
                body: "说明你已经能把半天骑稳定骑完。"
              },
              {
                milestone_key: "best_streak",
                title: "连续周骑行来到 3 周",
                body: "最近几周的骑行频率已经开始稳定。"
              }
            ]
          }
        })
      };
    }
    if (url.includes("/api/v1/rides/monthly-summary-events")) {
      return {
        ok: true,
        json: async () => ({
          event_no: "RME-1",
          event_type: "cta_click",
          requested_month: "2026-06",
          suggested_scene: "city_ride",
          next_action_key: "maintain_weekly_rhythm",
          source: "frontend",
          created_at: "2026-06-15"
        })
      };
    }
    if (url.includes("/api/v1/rides/growth-review-events")) {
      return {
        ok: true,
        json: async () => ({
          event_no: "RME-2",
          event_type: "growth_review_cta_click",
          requested_window_days: 90,
          suggested_scene: "weekend_trip",
          growth_status: "expanding",
          next_action_key: "maintain_weekly_rhythm",
          source: "frontend",
          created_at: "2026-06-15"
        })
      };
    }
    if (url.includes("/api/v1/rides/monthly-summary?month=")) {
      return {
        ok: true,
        json: async () => ({
          ride_monthly_summary: {
            month: "2026-06",
            period_start: "2026-06-01",
            period_end: "2026-06-30",
            ride_count: 2,
            ride_day_count: 2,
            completed_count: 1,
            shortened_count: 1,
            cancelled_count: 0,
            total_distance_km: 42,
            total_duration_hours: 2.7,
            planned_count: 1,
            manual_count: 1,
            last_ride_date: "2026-06-15",
            days_since_last_ride: 0,
            weekly_streak: 3,
            habit_status: "steady",
            next_action: {
              action_key: "maintain_weekly_rhythm",
              title: "这周再补一趟轻松骑就能把节奏续上。",
              body: "你最近的骑行频率比较稳，下一次继续安排一趟不追强度的城市骑就够了。",
              suggested_scene: "city_ride",
              suggested_entry: "这周找个傍晚，安排一次 1.5 到 2 小时的轻松骑。"
            },
            summary_headline: "这个月你已经把骑行节奏续起来了。",
            summary_body: "本月累计 2 条记录、42.0 km，整体节奏比较稳定，最近一次距离参考日 0 天。",
            top_start_region: "滨江",
            top_tag: "晚骑",
            hard_effort_count: 0,
            tired_mood_count: 0,
            matched_plan_count: 1,
            month_to_date: true,
            recent_30d_ride_count: 3
          }
        })
      };
    }
    return {
      ok: true,
      json: async () => ({
        items: [
          {
            ride_record_no: "RR-TEST0001",
            ride_date: "2026-06-15",
            route_title: "滨江-钱塘江休闲往返线",
            destination_name: "钱塘江南岸",
            completion_status: "completed",
            summary_headline: "滨江-钱塘江休闲往返线这次完成得很稳。"
          }
        ]
      })
    };
  });
  vi.stubGlobal(
    "fetch",
    fetchMock,
  );

  render(
    <MemoryRouter initialEntries={["/rides"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
        <Route path="/" element={<div>planner handoff target</div>} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("滨江-钱塘江休闲往返线")).toBeInTheDocument();
  expect(screen.getByText("这个月你已经把骑行节奏续起来了。")).toBeInTheDocument();
  expect(screen.getByText("最近这段时间，你的骑行范围已经明显打开了。")).toBeInTheDocument();
  expect(screen.getByText("最长距离刷新到 58 km")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "按这个建议去规划" })).toHaveAttribute(
    "href",
    "/?intent=ride_plan&seedQuery=%E8%BF%99%E5%91%A8%E6%89%BE%E4%B8%AA%E5%82%8D%E6%99%9A%EF%BC%8C%E5%AE%89%E6%8E%92%E4%B8%80%E6%AC%A1+1.5+%E5%88%B0+2+%E5%B0%8F%E6%97%B6%E7%9A%84%E8%BD%BB%E6%9D%BE%E9%AA%91%E3%80%82&handoffSource=monthly_summary&handoffActionKey=maintain_weekly_rhythm&handoffScene=city_ride&handoffStatus=steady&handoffRideCount=2&handoffWeeklyStreak=3&handoffRecentRideCount=3&handoffOriginRegion=%E6%BB%A8%E6%B1%9F&handoffTag=%E6%99%9A%E9%AA%91&handoffMonth=2026-06&handoffSuggestedHours=2"
  );
  expect(screen.getByRole("link", { name: "按这个方向继续安排" })).toHaveAttribute(
    "href",
    "/?intent=weekend_recommendation&seedQuery=%E8%BF%99%E4%B8%AA%E5%91%A8%E6%9C%AB%E5%AE%89%E6%8E%92%E4%B8%80%E6%AC%A1+3+%E5%88%B0+4+%E5%B0%8F%E6%97%B6%E3%80%81%E5%B8%A6%E4%B8%80%E7%82%B9%E7%88%AC%E5%8D%87%E7%9A%84%E5%8D%8A%E5%A4%A9%E9%AA%91%E3%80%82&handoffSource=growth_review&handoffActionKey=maintain_weekly_rhythm&handoffScene=weekend_trip&handoffStatus=expanding&handoffRideCount=4&handoffWeeklyStreak=3&handoffDistanceKm=154&handoffOriginRegion=%E6%BB%A8%E6%B1%9F&handoffTag=%E5%91%A8%E6%9C%AB&handoffWindowDays=90&handoffSuggestedHours=3.5"
  );
  expect(screen.getByText("滨江-钱塘江休闲往返线这次完成得很稳。")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "查看记录 RR-TEST0001" })).toHaveAttribute("href", "/rides/RR-TEST0001");

  const user = userEvent.setup();
  await user.click(screen.getByRole("link", { name: "按这个方向继续安排" }));
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/rides/growth-review-events",
    expect.objectContaining({
      method: "POST",
      keepalive: true,
    }),
  );

  render(
    <MemoryRouter initialEntries={["/rides"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
        <Route path="/" element={<div>planner handoff target</div>} />
      </Routes>
    </MemoryRouter>,
  );

  await screen.findByText("滨江-钱塘江休闲往返线");
  await user.click(screen.getByRole("link", { name: "按这个建议去规划" }));
  expect(fetchMock).toHaveBeenCalledWith(
    "/api/v1/rides/monthly-summary-events",
    expect.objectContaining({
      method: "POST",
      keepalive: true,
    }),
  );
});

test("shows empty state when no ride records exist", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/rides/growth-review?window_days=")) {
        return {
          ok: true,
          json: async () => ({
            ride_growth_review: {
              window_days: 90,
              period_start: "2026-03-18",
              period_end: "2026-06-15",
              ride_count: 0,
              ride_day_count: 0,
              completed_count: 0,
              total_distance_km: 0,
              total_duration_hours: 0,
              longest_distance_km: 0,
              longest_duration_hours: 0,
              active_month_count: 0,
              best_weekly_streak: 0,
              planned_count: 0,
              manual_count: 0,
              matched_plan_count: 0,
              top_start_region: null,
              top_tag: null,
              recent_vs_previous_ride_delta: 0,
              recent_vs_previous_distance_delta_km: 0,
              growth_status: "building",
              review_headline: "最近这段时间还没有形成新的骑行节奏。",
              review_body: "先把下一次轻松出门接上，比看更大的统计更重要。",
              next_focus: {
                action_key: "resume_with_short_ride",
                title: "先恢复下一次出门",
                body: "这周先接上一条容易执行的短骑。",
                suggested_scene: "city_ride",
                suggested_entry: "这周找个傍晚，先安排一趟 1 到 2 小时的轻松骑。"
              },
              milestones: []
            }
          })
        };
      }
      if (url.includes("/api/v1/rides/monthly-summary?month=")) {
        return {
          ok: true,
          json: async () => ({
            ride_monthly_summary: {
              month: "2026-06",
              period_start: "2026-06-01",
              period_end: "2026-06-30",
              ride_count: 0,
              ride_day_count: 0,
              completed_count: 0,
              shortened_count: 0,
              cancelled_count: 0,
              total_distance_km: 0,
              total_duration_hours: 0,
              planned_count: 0,
              manual_count: 0,
              last_ride_date: null,
              days_since_last_ride: null,
              weekly_streak: 0,
              habit_status: "starting",
              next_action: {
                action_key: "resume_with_short_ride",
                title: "先把下一次出门门槛降下来。",
                body: "先安排一次短而轻松的城市骑，把节奏重新接上。",
                suggested_scene: "city_ride",
                suggested_entry: "这周找个傍晚，安排一次 1.5 到 2 小时的轻松骑。"
              },
              summary_headline: "这个月还没把骑行重新接起来。",
              summary_body: "这个月还没有实际骑行记录，下一次先安排一趟容易出门的短骑就够了。",
              top_start_region: null,
              top_tag: null,
              hard_effort_count: 0,
              tired_mood_count: 0,
              matched_plan_count: 0,
              month_to_date: true,
              recent_30d_ride_count: 0
            }
          })
        };
      }
      return {
        ok: true,
        json: async () => ({ items: [] })
      };
    }),
  );

  render(
    <MemoryRouter initialEntries={["/rides"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("还没有骑行记录")).toBeInTheDocument();
});

test("shows error state when ride records fail to load", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/rides/growth-review?window_days=")) {
        return {
          ok: true,
          json: async () => ({
            ride_growth_review: {
              window_days: 90,
              period_start: "2026-03-18",
              period_end: "2026-06-15",
              ride_count: 2,
              ride_day_count: 2,
              completed_count: 2,
              total_distance_km: 38,
              total_duration_hours: 2.2,
              longest_distance_km: 20,
              longest_duration_hours: 1.2,
              active_month_count: 1,
              best_weekly_streak: 1,
              planned_count: 0,
              manual_count: 2,
              matched_plan_count: 0,
              top_start_region: null,
              top_tag: null,
              recent_vs_previous_ride_delta: 1,
              recent_vs_previous_distance_delta_km: 18,
              growth_status: "building",
              review_headline: "最近又开始把骑行接回来了。",
              review_body: "这段时间已经重新出门了两次，继续把门槛维持低一点更容易稳住。",
              next_focus: {
                action_key: "schedule_easy_city_ride",
                title: "这周再补一趟轻松骑",
                body: "下一次继续保持轻量节奏。",
                suggested_scene: "city_ride",
                suggested_entry: "这周再安排一次 2 小时内的轻松骑。"
              },
              milestones: []
            }
          })
        };
      }
      if (url.includes("/api/v1/rides/monthly-summary?month=")) {
        return {
          ok: true,
          json: async () => ({
            ride_monthly_summary: {
              month: "2026-06",
              period_start: "2026-06-01",
              period_end: "2026-06-30",
              ride_count: 1,
              ride_day_count: 1,
              completed_count: 1,
              shortened_count: 0,
              cancelled_count: 0,
              total_distance_km: 20,
              total_duration_hours: 1,
              planned_count: 0,
              manual_count: 1,
              last_ride_date: "2026-06-15",
              days_since_last_ride: 0,
              weekly_streak: 1,
              habit_status: "rebuilding",
              next_action: {
                action_key: "schedule_easy_city_ride",
                title: "这周再补一趟轻松骑会更稳。",
                body: "你已经在恢复节奏了，再补一次低压力短骑最合适。",
                suggested_scene: "city_ride",
                suggested_entry: "这周再安排一次 2 小时内、不追强度的轻松骑。"
              },
              summary_headline: "你已经在把骑行节奏慢慢找回来了。",
              summary_body: "本月累计 1 条记录、20.0 km，说明你已经在恢复骑行习惯，最近一次距离参考日 0 天。",
              top_start_region: null,
              top_tag: null,
              hard_effort_count: 0,
              tired_mood_count: 0,
              matched_plan_count: 0,
              month_to_date: true,
              recent_30d_ride_count: 1
            }
          })
        };
      }
      return {
        ok: false,
        status: 503
      };
    }),
  );

  render(
    <MemoryRouter initialEntries={["/rides"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByRole("alert")).toHaveTextContent("最近骑行记录暂时不可用，请稍后再试。");
});

test("shows summary error without blocking recent ride list", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/rides/growth-review?window_days=")) {
        return {
          ok: true,
          json: async () => ({
            ride_growth_review: {
              window_days: 90,
              period_start: "2026-03-18",
              period_end: "2026-06-15",
              ride_count: 1,
              ride_day_count: 1,
              completed_count: 1,
              total_distance_km: 20,
              total_duration_hours: 1.0,
              longest_distance_km: 20,
              longest_duration_hours: 1.0,
              active_month_count: 1,
              best_weekly_streak: 1,
              planned_count: 0,
              manual_count: 1,
              matched_plan_count: 0,
              top_start_region: null,
              top_tag: null,
              recent_vs_previous_ride_delta: 1,
              recent_vs_previous_distance_delta_km: 20,
              growth_status: "building",
              review_headline: "最近先把骑行重新接起来就对了。",
              review_body: "你已经重新出门了，先把频率稳住。",
              next_focus: {
                action_key: "schedule_easy_city_ride",
                title: "继续安排一趟轻松骑",
                body: "先不要追强度。",
                suggested_scene: "city_ride",
                suggested_entry: "这周安排一次轻松骑。"
              },
              milestones: []
            }
          })
        };
      }
      if (url.includes("/api/v1/rides/monthly-summary?month=")) {
        return {
          ok: false,
          status: 503
        };
      }
      return {
        ok: true,
        json: async () => ({
          items: [
            {
              ride_record_no: "RR-TEST0002",
              ride_date: "2026-06-12",
              route_title: "西湖轻松骑",
              destination_name: "西湖",
              completion_status: "shortened",
              summary_headline: "西湖轻松骑这次缩短了，但仍然完成了主要路段。"
            }
          ]
        })
      };
    }),
  );

  render(
    <MemoryRouter initialEntries={["/rides"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("西湖轻松骑")).toBeInTheDocument();
  expect(screen.getByText("本月骑行总结暂时不可用，请稍后再试。")).toBeInTheDocument();
});

test("shows growth review error without blocking monthly summary and recent ride list", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/api/v1/rides/growth-review?window_days=")) {
        return {
          ok: false,
          status: 503
        };
      }
      if (url.includes("/api/v1/rides/monthly-summary?month=")) {
        return {
          ok: true,
          json: async () => ({
            ride_monthly_summary: {
              month: "2026-06",
              period_start: "2026-06-01",
              period_end: "2026-06-30",
              ride_count: 2,
              ride_day_count: 2,
              completed_count: 1,
              shortened_count: 1,
              cancelled_count: 0,
              total_distance_km: 42,
              total_duration_hours: 2.7,
              planned_count: 1,
              manual_count: 1,
              last_ride_date: "2026-06-15",
              days_since_last_ride: 0,
              weekly_streak: 3,
              habit_status: "steady",
              next_action: {
                action_key: "maintain_weekly_rhythm",
                title: "这周再补一趟轻松骑就能把节奏续上。",
                body: "你最近的骑行频率比较稳，下一次继续安排一趟不追强度的城市骑就够了。",
                suggested_scene: "city_ride",
                suggested_entry: "这周找个傍晚，安排一次 1.5 到 2 小时的轻松骑。"
              },
              summary_headline: "这个月你已经把骑行节奏续起来了。",
              summary_body: "本月累计 2 条记录、42.0 km，整体节奏比较稳定，最近一次距离参考日 0 天。",
              top_start_region: "滨江",
              top_tag: "晚骑",
              hard_effort_count: 0,
              tired_mood_count: 0,
              matched_plan_count: 1,
              month_to_date: true,
              recent_30d_ride_count: 3
            }
          })
        };
      }
      return {
        ok: true,
        json: async () => ({
          items: [
            {
              ride_record_no: "RR-TEST0003",
              ride_date: "2026-06-11",
              route_title: "滨江夜骑",
              destination_name: "钱塘江",
              completion_status: "completed",
              summary_headline: "滨江夜骑这次完成得很稳。"
            }
          ]
        })
      };
    }),
  );

  render(
    <MemoryRouter initialEntries={["/rides"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("这个月你已经把骑行节奏续起来了。")).toBeInTheDocument();
  expect(screen.getByText("增长回顾暂时不可用，请稍后再试。")).toBeInTheDocument();
  expect(screen.getByText("滨江夜骑")).toBeInTheDocument();
});

test("switches growth review window without blocking other sections", async () => {
  const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.includes("/api/v1/rides/growth-review?window_days=180")) {
      return {
        ok: true,
        json: async () => ({
          ride_growth_review: {
            window_days: 180,
            period_start: "2025-12-18",
            period_end: "2026-06-15",
            ride_count: 6,
            ride_day_count: 6,
            completed_count: 5,
            total_distance_km: 220,
            total_duration_hours: 12.6,
            longest_distance_km: 62,
            longest_duration_hours: 3.6,
            active_month_count: 5,
            best_weekly_streak: 4,
            planned_count: 2,
            manual_count: 4,
            matched_plan_count: 2,
            top_start_region: "滨江",
            top_tag: "周末",
            recent_vs_previous_ride_delta: 1,
            recent_vs_previous_distance_delta_km: 24,
            growth_status: "steady",
            review_headline: "拉长到半年看，你的骑行节奏还是稳的。",
            review_body: "近 180 天里已经形成持续输出，不需要再额外放大动作。",
            next_focus: {
              action_key: "maintain_weekly_rhythm",
              title: "按现在的节奏继续",
              body: "保持每周至少一次出门就够了。",
              suggested_scene: "city_ride",
              suggested_entry: "这周继续安排一次 2 小时左右的轻松骑。"
            },
            milestones: []
          }
        })
      };
    }
    if (url.includes("/api/v1/rides/growth-review?window_days=")) {
      return {
        ok: true,
        json: async () => ({
          ride_growth_review: {
            window_days: 90,
            period_start: "2026-03-18",
            period_end: "2026-06-15",
            ride_count: 4,
            ride_day_count: 4,
            completed_count: 3,
            total_distance_km: 154,
            total_duration_hours: 8.6,
            longest_distance_km: 58,
            longest_duration_hours: 3.2,
            active_month_count: 3,
            best_weekly_streak: 3,
            planned_count: 2,
            manual_count: 2,
            matched_plan_count: 2,
            top_start_region: "滨江",
            top_tag: "周末",
            recent_vs_previous_ride_delta: 2,
            recent_vs_previous_distance_delta_km: 68,
            growth_status: "expanding",
            review_headline: "最近这段时间，你的骑行范围已经明显打开了。",
            review_body: "近 30 天的骑行次数和距离都比前一段更高，说明你不只是续上了节奏，还在往外扩。",
            next_focus: {
              action_key: "maintain_weekly_rhythm",
              title: "按这个方向继续安排",
              body: "下一次可以把周末半天骑继续保留住，不用再额外追强度。",
              suggested_scene: "weekend_trip",
              suggested_entry: "这个周末安排一次 3 到 4 小时、带一点爬升的半天骑。"
            },
            milestones: []
          }
        })
      };
    }
    if (url.includes("/api/v1/rides/monthly-summary?month=")) {
      return {
        ok: true,
        json: async () => ({
          ride_monthly_summary: {
            month: "2026-06",
            period_start: "2026-06-01",
            period_end: "2026-06-30",
            ride_count: 2,
            ride_day_count: 2,
            completed_count: 1,
            shortened_count: 1,
            cancelled_count: 0,
            total_distance_km: 42,
            total_duration_hours: 2.7,
            planned_count: 1,
            manual_count: 1,
            last_ride_date: "2026-06-15",
            days_since_last_ride: 0,
            weekly_streak: 3,
            habit_status: "steady",
            next_action: {
              action_key: "maintain_weekly_rhythm",
              title: "这周再补一趟轻松骑就能把节奏续上。",
              body: "你最近的骑行频率比较稳，下一次继续安排一趟不追强度的城市骑就够了。",
              suggested_scene: "city_ride",
              suggested_entry: "这周找个傍晚，安排一次 1.5 到 2 小时的轻松骑。"
            },
            summary_headline: "这个月你已经把骑行节奏续起来了。",
            summary_body: "本月累计 2 条记录、42.0 km，整体节奏比较稳定，最近一次距离参考日 0 天。",
            top_start_region: "滨江",
            top_tag: "晚骑",
            hard_effort_count: 0,
            tired_mood_count: 0,
            matched_plan_count: 1,
            month_to_date: true,
            recent_30d_ride_count: 3
          }
        })
      };
    }
    return {
      ok: true,
      json: async () => ({
        items: [
          {
            ride_record_no: "RR-TEST0004",
            ride_date: "2026-06-15",
            route_title: "滨江-钱塘江休闲往返线",
            destination_name: "钱塘江南岸",
            completion_status: "completed",
            summary_headline: "滨江-钱塘江休闲往返线这次完成得很稳。"
          }
        ]
      })
    };
  });
  vi.stubGlobal("fetch", fetchMock);

  render(
    <MemoryRouter initialEntries={["/rides"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("最近这段时间，你的骑行范围已经明显打开了。")).toBeInTheDocument();

  const user = userEvent.setup();
  await user.click(screen.getByRole("button", { name: "近 180 天" }));

  expect(await screen.findByText("拉长到半年看，你的骑行节奏还是稳的。")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalledWith("/api/v1/rides/growth-review?window_days=180");
});
