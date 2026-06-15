import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, vi } from "vitest";

import RideRecordsPage from "../pages/RideRecordsPage";

afterEach(() => {
  vi.unstubAllGlobals();
});

test("renders recent ride records with detail links", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
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
    })),
  );

  render(
    <MemoryRouter initialEntries={["/rides"]}>
      <Routes>
        <Route path="/rides" element={<RideRecordsPage />} />
      </Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByText("滨江-钱塘江休闲往返线")).toBeInTheDocument();
  expect(screen.getByText("滨江-钱塘江休闲往返线这次完成得很稳。")).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "查看记录 RR-TEST0001" })).toHaveAttribute("href", "/rides/RR-TEST0001");
});

test("shows empty state when no ride records exist", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({ items: [] })
    })),
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
    vi.fn(async () => ({
      ok: false,
      status: 503
    })),
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
