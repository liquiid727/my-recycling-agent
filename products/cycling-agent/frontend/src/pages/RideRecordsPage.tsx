import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import ThemeToggle from "../components/ThemeToggle";
import { listRideRecords, type RideRecordListItem } from "../features/planner/api";

export default function RideRecordsPage() {
  const [items, setItems] = useState<RideRecordListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    void listRideRecords(12)
      .then((payload) => {
        if (!active) {
          return;
        }
        setItems(payload.items);
        setLoading(false);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setError("最近骑行记录暂时不可用，请稍后再试。");
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <main className="page-shell">
      <ThemeToggle />
      <section className="hero-panel">
        <p className="eyebrow">Recent Rides</p>
        <h1>最近骑行记录</h1>
        <p className="hero-copy">回看最近完成、缩短或取消的骑行记录，快速定位当时的收尾反馈和总结。</p>
        <p className="hero-link-row">
          <Link to="/rides/new">手动补录</Link>
          {" · "}
          <Link to="/">返回规划页</Link>
        </p>
      </section>

      <section className="result-grid">
        {loading ? (
          <article className="state-panel">
            <h2>正在加载最近骑行记录</h2>
            <p>系统正在读取最近保存的骑后记录。</p>
          </article>
        ) : null}

        {error ? (
          <article className="state-panel state-error" role="alert">
            <h2>最近骑行记录读取失败</h2>
            <p>{error}</p>
          </article>
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <article className="state-panel">
            <h2>还没有骑行记录</h2>
            <p>先从一条手动补录开始，后面规划页里的骑后入口也会自动接到这里。</p>
            <p className="hero-link-row">
              <Link to="/rides/new">现在去补录</Link>
            </p>
          </article>
        ) : null}

        {!loading && !error && items.length > 0 ? (
          <div className="success-layout">
            {items.map((item) => (
              <article key={item.ride_record_no} className="detail-panel">
                <div className="section-heading">
                  <p className="section-kicker">Ride Record</p>
                  <h2>{item.route_title ?? item.destination_name ?? item.ride_record_no}</h2>
                </div>
                {item.summary_headline ? <p className="summary-copy">{item.summary_headline}</p> : null}
                <div className="metric-row">
                  <span>{item.ride_date}</span>
                  <span>完成情况：{item.completion_status}</span>
                  {item.destination_name ? <span>目的地：{item.destination_name}</span> : null}
                </div>
                <div className="planner-actions">
                  <Link aria-label={`查看记录 ${item.ride_record_no}`} to={`/rides/${item.ride_record_no}`}>
                    查看详情
                  </Link>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </section>
    </main>
  );
}
