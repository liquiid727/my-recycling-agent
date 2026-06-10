/*
 * CN: 主推荐卡片组件，突出推荐路线、决策状态、分数和查看详情入口。
 * EN: Primary recommendation card showing route, go decision, score, and detail navigation.
 */

type Props = {
  plan: {
    routeName: string;
    distanceKm: number;
    elevationGainM: number;
    estimatedDurationHours: number;
    riskLevel: string;
    summaryReason: string;
  };
};

export default function RecommendationCard({ plan }: Props) {
  return (
    <section className="detail-panel detail-panel-primary">
      <div className="section-heading">
        <p className="section-kicker">推荐路线</p>
        <h2>{plan.routeName}</h2>
      </div>
      <p className="summary-copy">为什么推荐它：{plan.summaryReason}</p>
      <div className="metric-row">
        <span>约 {plan.estimatedDurationHours} h</span>
        <span>{plan.distanceKm} km</span>
        <span>{plan.elevationGainM > 120 ? "有坡度" : "坡度友好"}</span>
        <span>补给看路书</span>
      </div>
      <p className="risk-pill">风险：{plan.riskLevel}</p>
      <div className="route-action-row" aria-label="路线操作">
        <button type="button">选这条</button>
        <button type="button">换轻松点</button>
        <button type="button">缩短到 1 小时</button>
        <button type="button">避开爬坡</button>
      </div>
    </section>
  );
}
