/*
 * CN: 历史规划结果页，根据 request_no 拉取并展示已保存规划。
 * EN: Saved plan result page that loads and displays a persisted plan by request_no.
 */

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import PlanResultView from "../components/PlanResultView";
import ThemeToggle from "../components/ThemeToggle";
import { getRidePlan, type RidePlanResponse } from "../features/planner/api";

export default function PlanResultPage() {
  const { requestNo = "" } = useParams();
  const [result, setResult] = useState<RidePlanResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    void getRidePlan(requestNo)
      .then((payload) => {
        if (!active) {
          return;
        }
        setResult(payload);
        setLoading(false);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setError("结果页暂时不可用，请返回首页重新生成。");
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [requestNo]);

  return (
    <main className="page-shell">
      <ThemeToggle />
      <section className="hero-panel">
        <p className="eyebrow">Plan Result</p>
        <h1>推荐结果页</h1>
        <p className="hero-copy">已保存的本次骑行规划结果，支持直接回看主推荐、风险和路书。</p>
        <p className="hero-link-row">
          <Link to="/">返回首页</Link>
        </p>
      </section>

      <section className="result-grid">
        {loading ? (
          <article className="state-panel">
            <h2>正在加载推荐结果</h2>
            <p>系统正在读取已保存的规划结果。</p>
          </article>
        ) : null}

        {error ? (
          <article className="state-panel state-error" role="alert">
            <h2>结果读取失败</h2>
            <p>{error}</p>
          </article>
        ) : null}

        {result ? <PlanResultView result={result} /> : null}
      </section>
    </main>
  );
}
