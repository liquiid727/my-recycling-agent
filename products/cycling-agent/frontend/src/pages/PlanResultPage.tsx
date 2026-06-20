import { Link, useParams } from "react-router-dom";

import { ErrorCard, LoadingCard } from "../components/EditorialStates";
import { useExperienceResult } from "../features/experience/hooks";

export default function PlanResultPage() {
  const { requestNo = "" } = useParams();
  const { result, loading, error } = useExperienceResult(requestNo);

  if (loading) {
    return (
      <main className="paper-shell">
        <LoadingCard title="正在翻开这次骑行结果" body="路线、结论和停靠提示正在落到这一页。" />
      </main>
    );
  }

  if (error || !result) {
    return (
      <main className="paper-shell">
        <ErrorCard title="这页骑行结果暂时翻不开" body={error ?? "请回首页重新生成一次。"} />
      </main>
    );
  }

  return (
    <main className="paper-shell space-y-6">
      <section className="paper-section">
        <p className="eyebrow">RESULT JOURNAL</p>
        <h1 className="display-title max-w-[12ch]">{result.decision.title}</h1>
        <p className="body-copy mt-4 max-w-3xl text-base">{result.editorial_intro}</p>
        <p className="body-copy mt-3 max-w-3xl">{result.decision.reason}</p>
        <p className="mt-4">
          <Link className="secondary-button" to="/">回到首页</Link>
        </p>
      </section>

      <section className="grid gap-6 lg:grid-cols-[1fr_0.8fr]">
        <article className="paper-section">
          <p className="eyebrow">ROUTE STORY</p>
          <h2 className="section-title">{result.route_story.route_name}</h2>
          <p className="body-copy mt-4">{result.route_story.summary}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {result.route_story.tags.map((tag) => (
              <span className="pill-tag" key={tag}>{tag}</span>
            ))}
            <span className="pill-tag">{result.route_story.distance_km} km</span>
            <span className="pill-tag">{result.route_story.estimated_duration_hours} h</span>
          </div>
          <p className="mt-5">
            <Link className="secondary-button" to={`/routes/${result.route_story.route_code}`}>打开路线详情</Link>
          </p>
        </article>

        <article className="paper-section">
          <p className="eyebrow">CONFIDENCE NOTES</p>
          <ul className="body-copy mt-4 space-y-3 pl-5">
            {result.decision.confidence_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
            {result.support_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </article>
      </section>

      {result.alternative_routes.length > 0 ? (
        <section className="paper-section">
          <p className="eyebrow">ALTERNATIVES</p>
          <h2 className="section-title">如果你想把这页翻得更轻一点</h2>
          <div className="mt-6 grid gap-4 lg:grid-cols-2">
            {result.alternative_routes.map((item) => (
              <article className="rounded-[22px] border border-line bg-white/80 p-5" key={item.route_code}>
                <h3 className="font-display text-2xl">{item.route_name}</h3>
                <p className="body-copy mt-3">{item.summary}</p>
              </article>
            ))}
          </div>
        </section>
      ) : null}

      <section className="paper-section">
        <p className="eyebrow">RIDE JOURNAL</p>
        <h2 className="section-title">{result.ride_journal_prompt}</h2>
      </section>
    </main>
  );
}
