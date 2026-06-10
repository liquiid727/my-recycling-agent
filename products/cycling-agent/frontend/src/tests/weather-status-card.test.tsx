/*
 * CN: 前端测试文件，验证页面渲染、提交、结果、详情、设置和状态组件。
 * EN: Frontend test file covering page rendering, submission, results, details, settings, and state components.
 */

import { render, screen } from "@testing-library/react";

import WeatherStatusCard from "../components/WeatherStatusCard";

test("renders weather summary and fallback warning", () => {
  render(
    <WeatherStatusCard
      snapshot={{
        forecastDate: "2026-05-30",
        temperatureMin: 22,
        temperatureMax: 31,
        precipitationProbability: 0.15,
        windSpeed: 4.8,
        windDirection: "SE",
        weatherSummary: "cloudy",
        providerName: "fallback"
      }}
      fallbackReason={["weather-provider-unavailable"]}
    />,
  );

  expect(screen.getByText("cloudy")).toBeInTheDocument();
  expect(screen.getByText("天气数据已降级")).toBeInTheDocument();
});
