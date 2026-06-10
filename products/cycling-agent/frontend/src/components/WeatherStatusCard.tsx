/*
 * CN: 天气状态卡片，展示温度、风、降水、湿度和 provider 降级原因。
 * EN: Weather status card for temperature, wind, precipitation, humidity, and provider fallback reasons.
 */

type Snapshot = {
  forecastDate: string;
  temperatureMin: number | null;
  temperatureMax: number | null;
  precipitationProbability: number | null;
  windSpeed: number | null;
  windDirection: string | null;
  weatherSummary: string;
  providerName: string;
};

type Props = {
  snapshot: Snapshot;
  fallbackReason: string[];
};

export default function WeatherStatusCard({ snapshot, fallbackReason }: Props) {
  return (
    <section className="detail-panel">
      <div className="section-heading">
        <p className="section-kicker">Weather Snapshot</p>
        <h3>天气状态</h3>
      </div>
      <div className="metric-row">
        <span>{snapshot.weatherSummary}</span>
        <span>{snapshot.forecastDate}</span>
        <span>
          {snapshot.temperatureMin ?? "-"} / {snapshot.temperatureMax ?? "-"} C
        </span>
        <span>降雨 {snapshot.precipitationProbability ?? "-"}</span>
        <span>
          风 {snapshot.windSpeed ?? "-"} m/s {snapshot.windDirection ?? "-"}
        </span>
      </div>
      <p className="summary-copy">来源：{snapshot.providerName}</p>
      {fallbackReason.length > 0 ? <p className="fallback-warning">天气数据已降级</p> : null}
    </section>
  );
}
