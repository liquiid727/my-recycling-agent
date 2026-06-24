"""CN: 骑前状态评估服务，用确定性规则把天气、画像和当下状态归一成可解释的出发建议。
EN: Ride-readiness service that turns weather, rider profile, and current state into a deterministic pre-ride recommendation.
"""

from __future__ import annotations

from typing import Any


def build_ride_readiness(
    *,
    planning_scene: str,
    weather_snapshot: dict[str, Any],
    constraints: dict[str, Any],
    rider_profile: dict[str, Any] | None = None,
    rider_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = rider_profile or {}
    state = rider_state or {}
    score = 0.78 if planning_scene == "city_ride" else 0.72
    reasons: list[str] = []
    caution_flags: list[str] = []

    temperature_max = _coerce_float(weather_snapshot.get("temperature_max"))
    precipitation_probability = _coerce_float(weather_snapshot.get("precipitation_probability"))
    wind_speed = _coerce_float(weather_snapshot.get("wind_speed"))
    available_hours = _coerce_float(constraints.get("available_hours"))
    target_distance_km = _coerce_float(constraints.get("target_distance_km"))

    if temperature_max is not None:
        if temperature_max >= 35:
            score -= 0.32
            reasons.append(f"最高温 {temperature_max:g} C，热负担偏高。")
            caution_flags.append("heat")
        elif temperature_max >= 33:
            score -= 0.22
            reasons.append(f"最高温 {temperature_max:g} C，适合缩短强度。")
            caution_flags.append("heat")
        elif temperature_max <= 5:
            score -= 0.18
            reasons.append(f"最高温只有 {temperature_max:g} C，体感偏冷。")
            caution_flags.append("cold")

    if precipitation_probability is not None:
        if precipitation_probability >= 0.6:
            score -= 0.3
            reasons.append(f"降雨概率 {precipitation_probability:.0%}，更适合保守安排。")
            caution_flags.append("rain")
        elif precipitation_probability >= 0.4:
            score -= 0.18
            reasons.append(f"降雨概率 {precipitation_probability:.0%}，要预留缩短方案。")
            caution_flags.append("rain")

    if wind_speed is not None:
        if wind_speed >= 8:
            score -= 0.18
            reasons.append(f"风速 {wind_speed:g} m/s，逆风和横风都会更吃力。")
            caution_flags.append("wind")
        elif wind_speed >= 6:
            score -= 0.1
            reasons.append(f"风速 {wind_speed:g} m/s，体感会比平时更耗。")
            caution_flags.append("wind")

    fatigue_level = state.get("fatigue_level")
    if fatigue_level == "tired":
        score -= 0.22
        reasons.append("你现在偏累，今天更适合轻一点。")
        caution_flags.append("fatigue")
    elif fatigue_level == "fresh":
        score += 0.04
        reasons.append("你现在状态比较新鲜，可以正常安排。")

    last_ride_days_ago = state.get("last_ride_days_ago")
    if isinstance(last_ride_days_ago, int):
        if last_ride_days_ago == 0:
            score -= 0.08
            reasons.append("你今天已经骑过或刚骑完不久，更适合恢复节奏。")
            caution_flags.append("recovery")
        elif last_ride_days_ago >= 14:
            score -= 0.06
            reasons.append("最近两周没怎么骑，先别把计划拉太满。")
            caution_flags.append("long_break")

    if profile.get("fitness_level") == "low":
        if available_hours is not None and available_hours >= 3:
            score -= 0.12
            reasons.append("当前体能档位偏保守，长时长安排要收一点。")
            caution_flags.append("low_fitness")
        elif target_distance_km is not None and target_distance_km >= 50:
            score -= 0.12
            reasons.append("当前体能档位偏保守，长距离安排要收一点。")
            caution_flags.append("low_fitness")

    if planning_scene == "weekend_trip" and fatigue_level == "tired":
        score -= 0.08
        reasons.append("周末出行比城市短骑更吃整体恢复，今天不适合把节奏拉满。")

    if available_hours is not None and available_hours < 1:
        reasons.append("这次可用时间不长，更适合把目标放在轻松出门。")
    if not reasons:
        reasons.append("天气和当前条件整体平稳，可以按正常节奏安排。")

    score = round(max(0.0, min(score, 1.0)), 2)
    status = "go" if score >= 0.67 else "light" if score >= 0.45 else "rest"
    recommended_intensity = _recommended_intensity(status, caution_flags)
    summary = _build_summary(planning_scene, status, recommended_intensity)

    return {
        "status": status,
        "score": score,
        "summary": summary,
        "reasons": reasons,
        "caution_flags": caution_flags,
        "recommended_intensity": recommended_intensity,
    }


def _recommended_intensity(status: str, caution_flags: list[str]) -> str:
    if status == "rest":
        return "rest"
    if status == "light" or any(flag in caution_flags for flag in ("fatigue", "rain", "heat", "recovery", "long_break")):
        return "light"
    return "steady"


def _build_summary(planning_scene: str, status: str, recommended_intensity: str) -> str:
    if planning_scene == "weekend_trip":
        if status == "go":
            return "这个周末整体可以按计划安排。"
        if status == "light":
            return "这个周末更适合轻一点或保留缩短方案。"
        return "这次更适合不要按原计划直接出行。"

    if status == "go" and recommended_intensity == "steady":
        return "今天整体适合按计划骑。"
    if status in {"go", "light"}:
        return "今天更适合轻一点骑，先把强度收住。"
    return "今天更适合休息，或者只做非常短的恢复骑。"


def _coerce_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None
