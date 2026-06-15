"""CN: 规则优先的骑行总结服务，根据完成状态、体感和计划偏差生成总结。
EN: Rule-first ride summary builder using completion status, effort, and plan variance.
"""

from __future__ import annotations

from typing import Any


def build_ride_summary(record: dict[str, Any], *, source_plan: dict[str, Any] | None) -> dict[str, Any]:
    completion_status = str(record.get("completion_status") or "completed")
    effort_feeling = str(record.get("effort_feeling") or "steady")
    mood_after = str(record.get("mood_after") or "normal")
    ride_label = _ride_label(record, source_plan)
    planned_duration = _planned_duration_hours(source_plan)
    actual_duration = _float_or_none(record.get("actual_duration_hours"))
    materially_above_plan = _is_materially_above_planned_duration(actual_duration, planned_duration)
    body_feedback_harder = _has_harder_body_feedback(effort_feeling, mood_after)

    confidence_notes = ["基于完成状态、体感反馈和计划时长差异的规则生成。"]
    if planned_duration is not None:
        confidence_notes.append("已参考原计划时长做对齐判断。")
    else:
        confidence_notes.append("未关联原计划时长，计划对齐判断有限。")

    if completion_status == "cancelled":
        return {
            "headline": f"{ride_label}这次没骑成也没关系。",
            "summary": "这次先放下不代表掉队，重点是把下一次重新出门的门槛降下来，不要有负担。",
            "completion_assessment": "cancelled",
            "effort_assessment": "not-started",
            "recovery_advice": "今天先按休息、补水和早点收尾来安排即可。",
            "next_ride_prompt": "下次先约一次更轻松、更容易出门的短骑，把节奏重新接上就够了。",
            "plan_alignment": "not-ridden",
            "confidence_notes": confidence_notes,
        }

    if completion_status == "shortened":
        return {
            "headline": f"{ride_label}这次是部分完成，但主段已经保住。",
            "summary": "虽然没有把原计划全部走完，但已经完成了主段输出，调整收尾本身也是合理决策。",
            "completion_assessment": "partially-completed",
            "effort_assessment": _effort_assessment(effort_feeling, mood_after, materially_above_plan),
            "recovery_advice": "今天按常规恢复处理即可，补水、轻拉伸，再观察腿部和睡眠反馈。",
            "next_ride_prompt": "下次可以保留这次顺手的前半段，再把后半段拆短一点重新完成。",
            "plan_alignment": "shortened-from-plan" if source_plan else None,
            "confidence_notes": confidence_notes,
        }

    if body_feedback_harder or materially_above_plan:
        return {
            "headline": f"{ride_label}完成了，但这次比预期更顶一点。",
            "summary": _completed_harder_summary(body_feedback_harder, materially_above_plan),
            "completion_assessment": "completed-as-planned",
            "effort_assessment": "slightly-harder-than-expected",
            "recovery_advice": _completed_harder_recovery_advice(body_feedback_harder, materially_above_plan),
            "next_ride_prompt": "下次先把时长或强度略收一点，再看恢复后要不要继续往上加。",
            "plan_alignment": _completed_harder_plan_alignment(source_plan, materially_above_plan),
            "confidence_notes": confidence_notes,
        }

    return {
        "headline": f"{ride_label}这次完成得很稳。",
        "summary": "整体按计划推进，节奏和收尾反馈都比较顺，说明这次安排与你当前状态基本匹配。",
        "completion_assessment": "completed-as-planned",
        "effort_assessment": "matched-expected-effort",
        "recovery_advice": "按常规补水和轻拉伸收尾就够了，明天可轻松骑或正常休息。",
        "next_ride_prompt": "下次可以继续安排相近时长，或者只做一点点增量尝试。",
        "plan_alignment": "matched-core-plan" if source_plan else None,
        "confidence_notes": confidence_notes,
    }


def _ride_label(record: dict[str, Any], source_plan: dict[str, Any] | None) -> str:
    for value in (
        record.get("route_title"),
        record.get("destination_name"),
        _nested_get(source_plan, "recommended_plan", "route_title"),
        _nested_get(source_plan, "recommended_plan", "name"),
    ):
        if value:
            return f"{value}"
    return "这次骑行"


def _effort_assessment(effort_feeling: str, mood_after: str, materially_above_plan: bool) -> str:
    if _has_harder_body_feedback(effort_feeling, mood_after) or materially_above_plan:
        return "slightly-harder-than-expected"
    return "matched-expected-effort"


def _has_harder_body_feedback(effort_feeling: str, mood_after: str) -> bool:
    return effort_feeling == "hard" or mood_after == "tired"


def _completed_harder_summary(body_feedback_harder: bool, materially_above_plan: bool) -> str:
    if body_feedback_harder and materially_above_plan:
        return "你把这次骑行完整做完了，不过体感反馈和实际时长都提示这次比预期更吃力，恢复安排要稍微认真一点。"
    if body_feedback_harder:
        return "你把这次骑行完整做完了，不过体感反馈说明这次比预期更吃力，恢复安排要稍微认真一点。"
    return "你把这次骑行完整做完了，不过实际时长比计划拉得更长，恢复安排要比常规收得更稳一点。"


def _completed_harder_recovery_advice(body_feedback_harder: bool, materially_above_plan: bool) -> str:
    if body_feedback_harder and materially_above_plan:
        return "今晚优先补水、进食和放松恢复，明天更适合轻松转腿或直接休息。"
    if body_feedback_harder:
        return "今晚优先补水和放松恢复，明天更适合轻松转腿，先观察身体反馈再决定是否加量。"
    return "这次更像是时长拉长后的额外消耗，今晚按补水、进食和轻拉伸收尾，明天先安排轻松骑即可。"


def _completed_harder_plan_alignment(source_plan: dict[str, Any] | None, materially_above_plan: bool) -> str | None:
    if not source_plan:
        return None
    if materially_above_plan:
        return "duration-ran-long"
    return "matched-core-plan"


def _is_materially_above_planned_duration(actual_duration: float | None, planned_duration: float | None) -> bool:
    if actual_duration is None or planned_duration is None or planned_duration <= 0:
        return False
    duration_gap = actual_duration - planned_duration
    return duration_gap >= 0.5 or actual_duration >= planned_duration * 1.2


def _planned_duration_hours(source_plan: dict[str, Any] | None) -> float | None:
    if not source_plan:
        return None
    recommended_plan = source_plan.get("recommended_plan") or {}
    return _float_or_none(
        recommended_plan.get("estimated_duration_hours")
        or recommended_plan.get("total_duration_hours")
        or source_plan.get("estimated_duration_hours")
    )


def _nested_get(payload: dict[str, Any] | None, *path: str) -> Any:
    current = payload
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)
