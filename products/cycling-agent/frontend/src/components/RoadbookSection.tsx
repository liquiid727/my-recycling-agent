/*
 * CN: 路书组件，展示分段行程、风险提示、补给点和撤退方案。
 * EN: Roadbook component for segment guidance, risk notes, supply points, and bailout options.
 */

type Roadbook = {
  departureWindow?: string;
  keySegments?: string[];
  supplyAdvice?: string[];
  mitigationAdvice?: string[];
  shortenOptions?: string[];
  poiSummary?: {
    supply_count?: number;
    bailout_count?: number;
    supply_labels?: string[];
    bailout_labels?: string[];
  } | null;
  routeContext?: {
    provider_name?: string;
    average_speed_kmh?: number | null;
    surface_type?: string | null;
    loop_type?: string | null;
  } | null;
};

type Props = {
  roadbook: Roadbook;
};

export default function RoadbookSection({ roadbook }: Props) {
  return (
    <section className="detail-panel">
      <div className="section-heading">
        <p className="section-kicker">Roadbook</p>
        <h3>解释型路书</h3>
      </div>
      <p>建议出发时段：{roadbook.departureWindow ?? "-"}</p>
      <ul className="detail-list">
        {(roadbook.keySegments ?? []).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <p>补给建议</p>
      <ul className="detail-list">
        {(roadbook.supplyAdvice ?? []).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      {roadbook.poiSummary ? (
        <>
          <p>POI 增强摘要</p>
          <ul className="detail-list">
            <li>补给点数量：{roadbook.poiSummary.supply_count ?? 0}</li>
            <li>撤退点数量：{roadbook.poiSummary.bailout_count ?? 0}</li>
            {((roadbook.poiSummary.supply_labels ?? []).slice(0, 2)).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      ) : null}
      <p>规避建议</p>
      <ul className="detail-list">
        {(roadbook.mitigationAdvice ?? []).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      <p>缩短或撤退建议</p>
      <ul className="detail-list">
        {(roadbook.shortenOptions ?? []).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
      {roadbook.routeContext ? (
        <p className="summary-copy">
          Route provider: {roadbook.routeContext.provider_name ?? "-"} / 平均速度 {roadbook.routeContext.average_speed_kmh ?? "-"} km/h
        </p>
      ) : null}
    </section>
  );
}
