import { Link, useParams } from "react-router-dom";

import { ErrorCard, LoadingCard } from "../components/EditorialStates";
import { useExperienceRouteDetail } from "../features/experience/hooks";

export default function RouteDetailPage() {
  const { routeCode = "" } = useParams();
  const { routeDetail, loading, error } = useExperienceRouteDetail(routeCode);

  if (loading) {
    return (
      <main className="paper-shell">
        <LoadingCard title="正在展开这一页路线手账" body="路线摘要、停靠点和撤退节点正在整理中。" />
      </main>
    );
  }

  if (error || !routeDetail) {
    return (
      <main className="paper-shell">
        <ErrorCard title="路线详情暂时不可用" body={error ?? "请回首页换一条路线看看。"} />
      </main>
    );
  }

  return (
    <main className="paper-shell space-y-6">
      <section className="paper-section">
        <p className="eyebrow">ROUTE NOTE</p>
        <h1 className="display-title max-w-[14ch]">{routeDetail.headline}</h1>
        <p className="body-copy mt-4 max-w-3xl">{routeDetail.summary}</p>
        <div className="mt-4 flex flex-wrap gap-2">
          {routeDetail.tags.map((tag) => (
            <span className="pill-tag" key={tag}>{tag}</span>
          ))}
        </div>
        <p className="mt-5">
          <Link className="secondary-button" to="/">回到首页</Link>
        </p>
      </section>

      <section className="grid gap-6 lg:grid-cols-2">
        <article className="paper-section">
          <p className="eyebrow">BEST TIME</p>
          <h2 className="section-title">推荐出发时间</h2>
          <ul className="body-copy mt-4 space-y-2 pl-5">
            {routeDetail.best_time_slots.map((slot) => (
              <li key={slot}>{slot}</li>
            ))}
          </ul>
        </article>
        <article className="paper-section">
          <p className="eyebrow">SUPPLY & BAILOUT</p>
          <h2 className="section-title">补给和撤退</h2>
          <div className="mt-4 space-y-4">
            {routeDetail.supply_points.map((point) => (
              <div key={`${point.name}-${point.km_mark}`}>
                <h3 className="font-semibold text-ink">{point.name}</h3>
                <p className="body-copy">{point.km_mark} km · {point.type}</p>
              </div>
            ))}
            {routeDetail.bailout_options.map((option) => (
              <div key={`${option.name}-${option.km_mark}`}>
                <h3 className="font-semibold text-ink">{option.name}</h3>
                <p className="body-copy">{option.km_mark} km · {option.reason}</p>
              </div>
            ))}
          </div>
        </article>
      </section>
    </main>
  );
}
