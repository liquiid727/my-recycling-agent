"""CN: 路书生成兜底服务，基于结构化路线和风险事实生成可解释行程建议。
EN: Fallback roadbook service that turns structured route and risk facts into explainable ride guidance.
"""

from __future__ import annotations


def build_roadbook(route: dict, risk: dict) -> dict:
    risk_level = risk.get("risk_level", "low")
    best_time_slots = route.get("best_time_slots", [])
    supply_points = route.get("supply_points", [])
    bailout_options = route.get("bailout_options", [])
    climb_segments = route.get("climb_segments", [])

    if risk_level == "high":
        departure_window = best_time_slots[0] if best_time_slots else "06:00-07:30"
        mitigation_advice = ["尽量缩短里程", "高温或降雨条件下建议改线或取消"]
    elif risk_level == "medium":
        departure_window = best_time_slots[0] if best_time_slots else "06:30-08:30"
        mitigation_advice = ["优先选择早出发", "中段补给后根据体感决定是否折返"]
    else:
        departure_window = best_time_slots[0] if best_time_slots else "06:30-09:00"
        mitigation_advice = ["若风变大可提前折返", "保持每 45 分钟一次补水节奏"]

    key_segments = [f"从{route.get('start_point_name') or route.get('district_tags', ['杭州'])[0]}进入主路线"]
    if climb_segments:
        key_segments.extend(
            [
                f"{segment['name']}：约 {segment['distance_km']} km，爬升 {segment['elevation_gain_m']} m，{segment['gradient_note']}"
                for segment in climb_segments[:2]
            ]
        )
    else:
        key_segments.append("前半程节奏以舒适巡航为主，避免在江边逆风段一次性拉爆。")

    supply_advice = ["起点附近先补水"]
    if supply_points:
        supply_advice.extend(
            [f"{point['km_mark']} km 左右可在{point['name']}做{point['type']}补给" for point in supply_points[:2]]
        )
    else:
        supply_advice.append("中段补给一次即可")

    shorten_options = [f"{option['name']}：{option['reason']}" for option in bailout_options[:2]]
    if not shorten_options:
        shorten_options = ["如状态下滑，可在中段折返，保留主要风景段。"]

    return {
        "departure_window": departure_window,
        "key_segments": key_segments,
        "supply_advice": supply_advice,
        "mitigation_advice": mitigation_advice,
        "shorten_options": shorten_options,
        "poi_summary": route.get("poi_summary"),
        "route_context": route.get("route_context"),
    }


def build_equipment_advice(route: dict, risk: dict, weather_snapshot: dict, constraints: dict) -> list[str]:
    advice = ["基础装备：头盔、手套、补胎工具、随身水壶。"]
    if constraints.get("duration_bucket") == "evening" or constraints.get("departure_time", "") >= "17:00":
        advice.append("夜骑装备：前后车灯、反光装备和轻薄防风层。")
    precipitation_probability = weather_snapshot.get("precipitation_probability")
    if precipitation_probability is not None and float(precipitation_probability) >= 0.35:
        advice.append("雨天准备：带轻量雨衣；若降雨升高，优先缩短或取消。")
    if route.get("climb_segments") or risk.get("climb_risk_score", 0) >= 2:
        advice.append("爬坡准备：额外补水和能量胶 / 能量棒，避免空腹上坡。")
    if risk.get("risk_level") == "high":
        advice.append("高风险提醒：不要强行按原路线执行，优先改短线或改天。")
    return advice
