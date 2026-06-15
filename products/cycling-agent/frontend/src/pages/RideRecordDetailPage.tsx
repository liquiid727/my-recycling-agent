import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import ThemeToggle from "../components/ThemeToggle";
import { getRideRecord, type RideRecordDetailResponse } from "../features/planner/api";

export default function RideRecordDetailPage() {
  const { rideRecordNo = "" } = useParams();
  const [detail, setDetail] = useState<RideRecordDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    void getRideRecord(rideRecordNo)
      .then((payload) => {
        if (!active) {
          return;
        }
        setDetail(payload);
        setLoading(false);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setError("骑行记录详情暂时不可用，请稍后再试。");
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [rideRecordNo]);

  if (loading) {
    return (
      <main className="page-shell">
        <ThemeToggle />
        <article className="state-panel">
          <h1>骑行记录详情</h1>
          <p>正在加载这次骑后的记录和总结。</p>
        </article>
      </main>
    );
  }

  if (error || !detail) {
    return (
      <main className="page-shell">
        <ThemeToggle />
        <article className="state-panel state-error" role="alert">
          <h1>骑行记录详情</h1>
          <p>{error ?? "当前没有可展示的骑行记录。"}</p>
          <p className="hero-link-row">
            <Link to="/rides">返回最近记录</Link>
          </p>
        </article>
      </main>
    );
  }

  const { ride_record: rideRecord, ride_summary: rideSummary } = detail;

  return (
    <main className="page-shell">
      <ThemeToggle />
      <article className="detail-panel detail-panel-primary">
        <div className="section-heading">
          <p className="section-kicker">Ride Record</p>
          <h1>骑行记录详情</h1>
        </div>
        <p className="summary-copy">{rideSummary.headline}</p>
        <p className="summary-copy">{rideSummary.summary}</p>
        <div className="metric-row">
          <span>记录编号：{rideRecord.ride_record_no}</span>
          <span>{rideRecord.ride_date}</span>
          <span>完成情况：{rideRecord.completion_status}</span>
          {rideRecord.actual_duration_hours != null ? <span>{rideRecord.actual_duration_hours} h</span> : null}
          {rideRecord.actual_distance_km != null ? <span>{rideRecord.actual_distance_km} km</span> : null}
        </div>
      </article>

      <section className="success-layout">
        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Recorded Facts</p>
            <h2>{rideRecord.route_title ?? rideRecord.destination_name ?? "这次骑行"}</h2>
          </div>
          <div className="risk-grid">
            {rideRecord.destination_name ? <span>目的地：{rideRecord.destination_name}</span> : null}
            {rideRecord.start_point ? <span>起点：{rideRecord.start_point}</span> : null}
            {rideRecord.origin_region ? <span>区域：{rideRecord.origin_region}</span> : null}
            <span>体感：{rideRecord.effort_feeling}</span>
            <span>收尾：{rideRecord.mood_after}</span>
            <span>录入方式：{rideRecord.entry_mode}</span>
          </div>
          {rideRecord.notes ? <p className="summary-copy">{rideRecord.notes}</p> : null}
          {rideRecord.tags.length > 0 ? (
            <div className="metric-row">
              {rideRecord.tags.map((tag) => (
                <span key={tag}>#{tag}</span>
              ))}
            </div>
          ) : null}
        </article>

        <article className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Summary</p>
            <h3>骑后总结</h3>
          </div>
          <ul className="detail-list">
            <li>完成判断：{rideSummary.completion_assessment}</li>
            <li>体感判断：{rideSummary.effort_assessment}</li>
            <li>恢复建议：{rideSummary.recovery_advice}</li>
            <li>下次建议：{rideSummary.next_ride_prompt}</li>
            {rideSummary.plan_alignment ? <li>计划对齐：{rideSummary.plan_alignment}</li> : null}
          </ul>
          {rideSummary.confidence_notes.length > 0 ? (
            <>
              <p className="summary-copy">生成依据</p>
              <ul className="detail-list">
                {rideSummary.confidence_notes.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </>
          ) : null}
        </article>
      </section>

      <p className="hero-link-row">
        <Link to="/rides">返回最近记录</Link>
        {" · "}
        <Link to="/rides/new">手动补录一条</Link>
      </p>
    </main>
  );
}
