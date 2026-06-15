import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import ThemeToggle from "../components/ThemeToggle";
import {
  ApiRequestError,
  createRideRecord,
  getRidePlan,
  type CreateRideRecordRequest,
  type RidePlanResponse,
} from "../features/planner/api";

type RideRecordFormState = {
  rideDate: string;
  routeTitle: string;
  destinationName: string;
  startPoint: string;
  originRegion: string;
  completionStatus: "completed" | "shortened" | "cancelled";
  actualDurationHours: string;
  actualDistanceKm: string;
  effortFeeling: "easy" | "steady" | "hard";
  moodAfter: "refreshed" | "normal" | "tired";
  notes: string;
  tags: string;
};

export default function RideRecordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sourceRequestNo = searchParams.get("sourceRequestNo")?.trim() ?? "";
  const [sourcePlan, setSourcePlan] = useState<RidePlanResponse | null>(null);
  const [loading, setLoading] = useState(sourceRequestNo.length > 0);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [form, setForm] = useState<RideRecordFormState>({
    rideDate: todayAsDateInput(),
    routeTitle: "",
    destinationName: "",
    startPoint: "",
    originRegion: "",
    completionStatus: "completed",
    actualDurationHours: "",
    actualDistanceKm: "",
    effortFeeling: "steady",
    moodAfter: "refreshed",
    notes: "",
    tags: "",
  });

  const entryMode = sourceRequestNo ? "planned" : "manual";
  const sourcePlanContext = useMemo(() => {
    if (!sourcePlan) {
      return null;
    }
    const plan = sourcePlan.plan;
    const recommended = sourcePlan.recommended_plan;
    return {
      title: plan?.title ?? recommended.route_name ?? "关联规划",
      summary: plan?.summary ?? recommended.summary_reason ?? "已关联保存的骑行规划。",
      distanceKm: plan?.distance_km ?? recommended.distance_km ?? null,
      estimatedDurationHours: plan?.estimated_duration_hours ?? recommended.estimated_duration_hours ?? null,
      destinationName: plan?.destination_name ?? null,
    };
  }, [sourcePlan]);

  useEffect(() => {
    if (!sourceRequestNo) {
      return;
    }

    let active = true;
    setLoading(true);
    setError(null);

    void getRidePlan(sourceRequestNo)
      .then((payload) => {
        if (!active) {
          return;
        }
        setSourcePlan(payload);
        setForm((current) => ({
          ...current,
          rideDate: payload.input_summary?.target_date ?? current.rideDate,
          routeTitle: payload.plan?.title ?? payload.recommended_plan.route_name ?? current.routeTitle,
          destinationName: payload.plan?.destination_name ?? current.destinationName,
          startPoint: firstString(
            payload.input_summary?.start_point,
            readString(payload.parsed_constraints, "start_point"),
            current.startPoint,
          ),
          originRegion: firstString(
            payload.input_summary?.origin_region,
            readString(payload.parsed_constraints, "origin_region"),
            current.originRegion,
          ),
        }));
        setLoading(false);
      })
      .catch(() => {
        if (!active) {
          return;
        }
        setError("关联规划暂时不可用，请稍后再试。");
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [sourceRequestNo]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitError(null);
    const validationError = validateRideRecordForm(form, entryMode);
    if (validationError) {
      setSubmitError(validationError);
      return;
    }

    setSaving(true);

    try {
      const response = await createRideRecord(buildPayload(form, entryMode, sourceRequestNo));
      navigate(`/rides/${response.ride_record.ride_record_no}`);
    } catch (error) {
      setSubmitError(toCreateRideRecordErrorMessage(error));
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="page-shell">
        <ThemeToggle />
        <article className="state-panel">
          <h1>记录一次骑行</h1>
          <p>正在加载关联规划...</p>
        </article>
      </main>
    );
  }

  if (error) {
    return (
      <main className="page-shell">
        <ThemeToggle />
        <article className="state-panel state-error" role="alert">
          <h1>记录一次骑行</h1>
          <p>{error}</p>
          <p className="hero-link-row">
            <Link to="/rides">查看最近记录</Link>
          </p>
        </article>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <ThemeToggle />
      <section className="hero-panel">
        <p className="eyebrow">Ride Record</p>
        <h1>记录一次骑行</h1>
        <p className="hero-copy">
          {entryMode === "planned"
            ? "把这次实际完成情况、体感和收尾状态记下来，后面能直接回看骑后总结。"
            : "支持手动补录没有来源规划的骑行记录，后面也能统一回看。"}
        </p>
        <p className="hero-link-row">
          <Link to="/rides">查看最近记录</Link>
          {sourceRequestNo ? (
            <>
              {" · "}
              <Link to={`/plans/${sourceRequestNo}`}>返回原规划</Link>
            </>
          ) : null}
        </p>
      </section>

      <section className="success-layout">
        {sourcePlanContext ? (
          <article className="detail-panel detail-panel-primary">
            <div className="section-heading">
              <p className="section-kicker">Source Plan</p>
              <h2>{sourcePlanContext.title}</h2>
            </div>
            <p className="summary-copy">{sourcePlanContext.summary}</p>
            <div className="metric-row">
              {sourcePlanContext.distanceKm != null ? <span>{sourcePlanContext.distanceKm} km</span> : null}
              {sourcePlanContext.estimatedDurationHours != null ? (
                <span>{sourcePlanContext.estimatedDurationHours} h 预计骑行</span>
              ) : null}
              {sourcePlanContext.destinationName ? <span>目的地：{sourcePlanContext.destinationName}</span> : null}
              {form.startPoint ? <span>起点：{form.startPoint}</span> : null}
              {form.originRegion ? <span>区域：{form.originRegion}</span> : null}
            </div>
          </article>
        ) : null}

        <section className="detail-panel">
          <div className="section-heading">
            <p className="section-kicker">Entry Form</p>
            <h2>{entryMode === "planned" ? "补一条这次骑后的真实结果" : "手动补录一次骑行"}</h2>
          </div>
          <form className="planner-form" onSubmit={submit}>
            {entryMode === "manual" ? (
              <div className="structured-grid">
                <label className="field-label" htmlFor="ride-route-title">
                  路线标题
                  <input
                    id="ride-route-title"
                    value={form.routeTitle}
                    onChange={(event) => updateForm(setForm, "routeTitle", event.target.value)}
                  />
                </label>
                <label className="field-label" htmlFor="ride-destination-name">
                  目的地
                  <input
                    id="ride-destination-name"
                    value={form.destinationName}
                    onChange={(event) => updateForm(setForm, "destinationName", event.target.value)}
                  />
                </label>
                <label className="field-label" htmlFor="ride-start-point">
                  起点
                  <input
                    id="ride-start-point"
                    value={form.startPoint}
                    onChange={(event) => updateForm(setForm, "startPoint", event.target.value)}
                  />
                </label>
                <label className="field-label" htmlFor="ride-origin-region">
                  出发区域
                  <input
                    id="ride-origin-region"
                    value={form.originRegion}
                    onChange={(event) => updateForm(setForm, "originRegion", event.target.value)}
                  />
                </label>
              </div>
            ) : (
              <p className="summary-copy">
                本次会沿用关联规划的路线、目的地和出发上下文，只需要补实际完成情况和体感反馈。
              </p>
            )}

            <div className="structured-grid">
              <label className="field-label" htmlFor="ride-date">
                骑行日期
                <input
                  id="ride-date"
                  type="date"
                  value={form.rideDate}
                  onChange={(event) => updateForm(setForm, "rideDate", event.target.value)}
                />
              </label>
              <label className="field-label" htmlFor="ride-completion-status">
                完成情况
                <select
                  id="ride-completion-status"
                  value={form.completionStatus}
                  onChange={(event) => updateForm(setForm, "completionStatus", event.target.value as RideRecordFormState["completionStatus"])}
                >
                  <option value="completed">completed</option>
                  <option value="shortened">shortened</option>
                  <option value="cancelled">cancelled</option>
                </select>
              </label>
              <label className="field-label" htmlFor="ride-actual-duration">
                实际时长（小时）
                <input
                  id="ride-actual-duration"
                  type="number"
                  min="0"
                  step="0.1"
                  value={form.actualDurationHours}
                  onChange={(event) => updateForm(setForm, "actualDurationHours", event.target.value)}
                />
              </label>
              <label className="field-label" htmlFor="ride-actual-distance">
                实际距离（km）
                <input
                  id="ride-actual-distance"
                  type="number"
                  min="0"
                  step="0.1"
                  value={form.actualDistanceKm}
                  onChange={(event) => updateForm(setForm, "actualDistanceKm", event.target.value)}
                />
              </label>
              <label className="field-label" htmlFor="ride-effort-feeling">
                体感强度
                <select
                  id="ride-effort-feeling"
                  value={form.effortFeeling}
                  onChange={(event) => updateForm(setForm, "effortFeeling", event.target.value as RideRecordFormState["effortFeeling"])}
                >
                  <option value="easy">easy</option>
                  <option value="steady">steady</option>
                  <option value="hard">hard</option>
                </select>
              </label>
              <label className="field-label" htmlFor="ride-mood-after">
                收尾感受
                <select
                  id="ride-mood-after"
                  value={form.moodAfter}
                  onChange={(event) => updateForm(setForm, "moodAfter", event.target.value as RideRecordFormState["moodAfter"])}
                >
                  <option value="refreshed">refreshed</option>
                  <option value="normal">normal</option>
                  <option value="tired">tired</option>
                </select>
              </label>
            </div>

            <label className="field-label" htmlFor="ride-notes">
              备注
            </label>
            <textarea
              id="ride-notes"
              className="planner-input"
              rows={4}
              value={form.notes}
              onChange={(event) => updateForm(setForm, "notes", event.target.value)}
            />

            <label className="field-label" htmlFor="ride-tags">
              标签（逗号分隔）
            </label>
            <input
              id="ride-tags"
              className="planner-input"
              value={form.tags}
              onChange={(event) => updateForm(setForm, "tags", event.target.value)}
            />

            <div className="planner-actions">
              <button className="primary-button" type="submit" disabled={saving}>
                {saving ? "正在保存..." : "保存骑行记录"}
              </button>
              <Link to="/rides">取消，先看最近记录</Link>
            </div>
            {submitError ? (
              <p className="summary-copy" role="alert">
                {submitError}
              </p>
            ) : null}
          </form>
        </section>
      </section>
    </main>
  );
}

function buildPayload(
  form: RideRecordFormState,
  entryMode: "planned" | "manual",
  sourceRequestNo: string,
): CreateRideRecordRequest {
  return {
    entry_mode: entryMode,
    source_request_no: entryMode === "planned" ? sourceRequestNo : undefined,
    ride_date: form.rideDate,
    route_code: undefined,
    route_title: entryMode === "manual" ? emptyToUndefined(form.routeTitle) : undefined,
    destination_name: entryMode === "manual" ? emptyToUndefined(form.destinationName) : undefined,
    start_point: entryMode === "manual" ? emptyToUndefined(form.startPoint) : undefined,
    origin_region: entryMode === "manual" ? emptyToUndefined(form.originRegion) : undefined,
    completion_status: form.completionStatus,
    actual_duration_hours: toOptionalNumber(form.actualDurationHours),
    actual_distance_km: toOptionalNumber(form.actualDistanceKm),
    effort_feeling: form.effortFeeling,
    mood_after: form.moodAfter,
    notes: emptyToUndefined(form.notes),
    tags: parseTags(form.tags),
  };
}

function validateRideRecordForm(form: RideRecordFormState, entryMode: "planned" | "manual"): string | null {
  if (entryMode === "manual" && !hasExplicitValue(form.routeTitle) && !hasExplicitValue(form.destinationName)) {
    return "手动补录至少填写路线标题或目的地。";
  }

  if (
    form.completionStatus === "completed" &&
    !hasExplicitValue(form.actualDurationHours) &&
    !hasExplicitValue(form.actualDistanceKm)
  ) {
    return "已完成的骑行至少填写实际时长或实际距离之一。";
  }

  return null;
}

function parseTags(input: string): string[] {
  return input
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function toOptionalNumber(value: string): number | undefined {
  if (!value.trim()) {
    return undefined;
  }
  return Number(value);
}

function emptyToUndefined(value: string | null | undefined): string | undefined {
  if (!value || !value.trim()) {
    return undefined;
  }
  return value.trim();
}

function todayAsDateInput(): string {
  const date = new Date();
  const year = String(date.getFullYear());
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function readString(payload: Record<string, unknown>, key: string): string | undefined {
  const value = payload[key];
  return typeof value === "string" ? value : undefined;
}

function firstString(...values: Array<string | null | undefined>): string {
  return values.find((value) => typeof value === "string" && value.trim()) ?? "";
}

function hasExplicitValue(value: string): boolean {
  return value.trim().length > 0;
}

function toCreateRideRecordErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError) {
    switch (error.detail) {
      case "ride-record-manual-title-missing":
        return "手动补录至少填写路线标题或目的地。";
      case "ride-record-completed-metrics-missing":
        return "已完成的骑行至少填写实际时长或实际距离之一。";
      case "ride-record-source-request-missing":
        return "关联规划缺少来源编号，建议返回结果页重新进入后再记录。";
      case "ride-record-source-plan-not-found":
        return "关联的原规划不存在，建议返回结果页重新打开后再记录。";
      default:
        return "骑行记录暂时没保存成功，请稍后再试。";
    }
  }
  return "骑行记录暂时没保存成功，请稍后再试。";
}

function updateForm<Key extends keyof RideRecordFormState>(
  setForm: React.Dispatch<React.SetStateAction<RideRecordFormState>>,
  key: Key,
  value: RideRecordFormState[Key],
) {
  setForm((current) => ({ ...current, [key]: value }));
}
