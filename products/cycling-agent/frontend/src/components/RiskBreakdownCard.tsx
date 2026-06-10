/*
 * CN: 风险拆解卡片，按维度展示总风险和各项风险分。
 * EN: Risk breakdown card that displays total risk and per-dimension risk scores.
 */

type RiskSummary = {
  overall_risk_score?: number;
  weather_risk_score?: number;
  climb_risk_score?: number;
  traffic_risk_score?: number;
  supply_risk_score?: number;
  return_risk_score?: number;
  risk_level?: string;
};

type Props = {
  risk: RiskSummary;
};

export default function RiskBreakdownCard({ risk }: Props) {
  return (
    <section className="detail-panel">
      <div className="section-heading">
        <p className="section-kicker">Risk View</p>
        <h3>风险拆解</h3>
      </div>
      <div className="risk-grid">
        <span>综合：{risk.overall_risk_score ?? "-"}</span>
        <span>天气：{risk.weather_risk_score ?? "-"}</span>
        <span>爬升：{risk.climb_risk_score ?? "-"}</span>
        <span>道路：{risk.traffic_risk_score ?? "-"}</span>
        <span>补给：{risk.supply_risk_score ?? "-"}</span>
        <span>返程：{risk.return_risk_score ?? "-"}</span>
      </div>
    </section>
  );
}
