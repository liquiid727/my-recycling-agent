/*
 * CN: 备选路线列表组件，展示非主推荐路线的风险和推荐理由。
 * EN: Alternative route list component showing non-primary route risk and recommendation reasons.
 */

type AlternativePlan = {
  routeName: string;
  distanceKm: number;
  elevationGainM: number;
  estimatedDurationHours: number;
  riskLevel: string;
  summaryReason: string;
};

type Props = {
  plans: AlternativePlan[];
};

export default function AlternativeRouteList({ plans }: Props) {
  return (
    <section className="detail-panel">
      <div className="section-heading">
        <p className="section-kicker">可选路线</p>
        <h3>不想选主路线，可以看这几条</h3>
      </div>
      <div className="alternative-list">
        {plans.map((plan) => (
          <article className="alternative-card" key={plan.routeName}>
            <strong>{plan.routeName}</strong>
            <p>为什么可以选：{plan.summaryReason}</p>
            <span>
              约 {plan.estimatedDurationHours} h / {plan.distanceKm} km / {plan.elevationGainM > 120 ? "有坡度" : "坡度友好"} / 风险 {plan.riskLevel}
            </span>
            <div className="route-action-row" aria-label={`${plan.routeName} 操作`}>
              <button type="button">选这条</button>
              <button type="button">换轻松点</button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
