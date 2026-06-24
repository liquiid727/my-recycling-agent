"""CN: 规划审计仓库，将一次规划拆成请求、天气、风险和决策四类结构化记录。
EN: Planning audit repository that splits a run into request, weather, risk, and decision records.
"""

from __future__ import annotations

import json
from typing import Any

from app.core.ids import derive_business_no, generate_uuid_v7_like
from app.core.storage import connect


def save_planning_audit(
    database_url: str,
    *,
    request_payload: dict[str, Any],
    plan_payload: dict[str, Any],
) -> None:
    parsed_constraints = plan_payload["parsed_constraints"]
    user_profile = request_payload.get("user_profile")
    rider_state = request_payload.get("rider_state")
    weather_snapshot = plan_payload["weather_snapshot"]
    audit_payload = plan_payload.get("_audit", {})
    candidate_assessments = audit_payload.get("candidate_assessments", [])
    roadbook = plan_payload.get("roadbook")

    with connect(database_url) as connection:
        existing_ride_request = connection.execute(
            "SELECT id FROM ride_requests WHERE request_no = ?",
            (plan_payload["request_no"],),
        ).fetchone()
        existing_weather_snapshot = connection.execute(
            "SELECT id FROM weather_snapshots WHERE request_no = ?",
            (plan_payload["request_no"],),
        ).fetchone()
        existing_decision_result = connection.execute(
            "SELECT id FROM decision_results WHERE request_no = ?",
            (plan_payload["request_no"],),
        ).fetchone()
        connection.execute(
            """
            INSERT INTO ride_requests (
                id,
                request_no,
                city_code,
                raw_query,
                target_date,
                origin_region,
                available_hours,
                target_distance_km,
                fitness_level,
                ride_style,
                parsed_constraints_json,
                user_profile_json,
                rider_state_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(request_no) DO UPDATE SET
                id = excluded.id,
                city_code = excluded.city_code,
                raw_query = excluded.raw_query,
                target_date = excluded.target_date,
                origin_region = excluded.origin_region,
                available_hours = excluded.available_hours,
                target_distance_km = excluded.target_distance_km,
                fitness_level = excluded.fitness_level,
                ride_style = excluded.ride_style,
                parsed_constraints_json = excluded.parsed_constraints_json,
                user_profile_json = excluded.user_profile_json,
                rider_state_json = excluded.rider_state_json
            """,
            (
                existing_ride_request["id"] if existing_ride_request and existing_ride_request["id"] else generate_uuid_v7_like(),
                plan_payload["request_no"],
                request_payload["city_code"],
                request_payload["query"],
                request_payload["target_date"],
                parsed_constraints.get("origin_region"),
                parsed_constraints.get("available_hours"),
                parsed_constraints.get("target_distance_km"),
                (user_profile or {}).get("fitness_level"),
                parsed_constraints.get("ride_style"),
                json.dumps(parsed_constraints, ensure_ascii=False),
                json.dumps(user_profile, ensure_ascii=False) if user_profile else None,
                json.dumps(rider_state, ensure_ascii=False) if rider_state else None,
            ),
        )
        connection.execute(
            """
            INSERT INTO weather_snapshots (
                id,
                request_no,
                weather_no,
                city_code,
                region_code,
                forecast_date,
                temperature_min,
                temperature_max,
                precipitation_probability,
                wind_speed,
                wind_direction,
                weather_summary,
                provider_name,
                raw_payload_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(request_no) DO UPDATE SET
                id = excluded.id,
                weather_no = excluded.weather_no,
                city_code = excluded.city_code,
                region_code = excluded.region_code,
                forecast_date = excluded.forecast_date,
                temperature_min = excluded.temperature_min,
                temperature_max = excluded.temperature_max,
                precipitation_probability = excluded.precipitation_probability,
                wind_speed = excluded.wind_speed,
                wind_direction = excluded.wind_direction,
                weather_summary = excluded.weather_summary,
                provider_name = excluded.provider_name,
                raw_payload_json = excluded.raw_payload_json
            """,
            (
                existing_weather_snapshot["id"] if existing_weather_snapshot and existing_weather_snapshot["id"] else generate_uuid_v7_like(),
                plan_payload["request_no"],
                derive_business_no("WS", plan_payload["request_no"]),
                request_payload["city_code"],
                weather_snapshot["region_code"],
                weather_snapshot["forecast_date"],
                weather_snapshot.get("temperature_min"),
                weather_snapshot.get("temperature_max"),
                weather_snapshot.get("precipitation_probability"),
                weather_snapshot.get("wind_speed"),
                weather_snapshot.get("wind_direction"),
                weather_snapshot["weather_summary"],
                weather_snapshot["provider_name"],
                json.dumps(weather_snapshot.get("raw_payload"), ensure_ascii=False),
            ),
        )
        connection.execute("DELETE FROM risk_assessments WHERE request_no = ?", (plan_payload["request_no"],))
        for index, item in enumerate(candidate_assessments, start=1):
            risk = item["risk"]
            connection.execute(
                """
                INSERT INTO risk_assessments (
                    entity_id,
                    request_no,
                    risk_no,
                    route_code,
                    route_name,
                    recommendation_score,
                    overall_risk_score,
                    risk_level,
                    weather_risk_score,
                    climb_risk_score,
                    traffic_risk_score,
                    supply_risk_score,
                    return_risk_score,
                    crowd_risk_score,
                    reasons_json,
                    mitigation_advice_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    generate_uuid_v7_like(),
                    plan_payload["request_no"],
                    derive_business_no("RS", plan_payload["request_no"], suffix=index),
                    item["route_code"],
                    item["route_name"],
                    item["recommendation_score"],
                    risk.get("overall_risk_score", 0.0),
                    risk["risk_level"],
                    risk.get("weather_risk_score", 0.0),
                    risk.get("climb_risk_score", 0.0),
                    risk.get("traffic_risk_score", 0.0),
                    risk.get("supply_risk_score", 0.0),
                    risk.get("return_risk_score", 0.0),
                    risk.get("crowd_risk_score", 0.0),
                    json.dumps(
                        [
                            f"weather={risk.get('weather_risk_score', 0.0)}",
                            f"climb={risk.get('climb_risk_score', 0.0)}",
                            f"traffic={risk.get('traffic_risk_score', 0.0)}",
                            f"supply={risk.get('supply_risk_score', 0.0)}",
                            f"return={risk.get('return_risk_score', 0.0)}",
                            f"crowd={risk.get('crowd_risk_score', 0.0)}",
                        ],
                        ensure_ascii=False,
                    ),
                    json.dumps((roadbook or {}).get("mitigation_advice", []), ensure_ascii=False),
                ),
            )
        connection.execute(
            """
            INSERT INTO decision_results (
                id,
                request_no,
                decision_no,
                recommended_route_code,
                backup_route_codes_json,
                go_decision,
                explanation,
                roadbook_json,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(request_no) DO UPDATE SET
                id = excluded.id,
                decision_no = excluded.decision_no,
                recommended_route_code = excluded.recommended_route_code,
                backup_route_codes_json = excluded.backup_route_codes_json,
                go_decision = excluded.go_decision,
                explanation = excluded.explanation,
                roadbook_json = excluded.roadbook_json,
                status = excluded.status
            """,
            (
                existing_decision_result["id"] if existing_decision_result and existing_decision_result["id"] else generate_uuid_v7_like(),
                plan_payload["request_no"],
                derive_business_no("DC", plan_payload["request_no"]),
                plan_payload["recommended_plan"]["route_code"],
                json.dumps([item["route_code"] for item in plan_payload["alternatives"]], ensure_ascii=False),
                plan_payload["recommended_plan"]["go_decision"],
                plan_payload["recommended_plan"]["summary_reason"],
                json.dumps(roadbook, ensure_ascii=False),
                plan_payload["status"],
            ),
        )


def get_planning_audit(database_url: str, request_no: str) -> dict[str, Any] | None:
    with connect(database_url) as connection:
        ride_request = connection.execute(
            """
            SELECT id, request_no, city_code, raw_query, target_date, origin_region, available_hours, target_distance_km,
                   fitness_level, ride_style, parsed_constraints_json, user_profile_json, rider_state_json, created_at
            FROM ride_requests
            WHERE request_no = ?
            """,
            (request_no,),
        ).fetchone()
        if ride_request is None:
            return None

        weather_snapshot = connection.execute(
            """
            SELECT id, weather_no, city_code, region_code, forecast_date, temperature_min, temperature_max,
                   precipitation_probability, wind_speed, wind_direction, weather_summary, provider_name,
                   raw_payload_json, fetched_at
            FROM weather_snapshots
            WHERE request_no = ?
            """,
            (request_no,),
        ).fetchone()
        risk_assessments = connection.execute(
            """
            SELECT entity_id, risk_no, route_code, route_name, recommendation_score, overall_risk_score, risk_level,
                   weather_risk_score, climb_risk_score, traffic_risk_score, supply_risk_score,
                   return_risk_score, crowd_risk_score, reasons_json, mitigation_advice_json, created_at
            FROM risk_assessments
            WHERE request_no = ?
            ORDER BY recommendation_score DESC, id ASC
            """,
            (request_no,),
        ).fetchall()
        decision_result = connection.execute(
            """
            SELECT id, decision_no, recommended_route_code, backup_route_codes_json, go_decision,
                   explanation, roadbook_json, status, created_at
            FROM decision_results
            WHERE request_no = ?
            """,
            (request_no,),
        ).fetchone()

    return {
        "ride_request": {
            "id": ride_request["id"],
            "request_no": ride_request["request_no"],
            "city_code": ride_request["city_code"],
            "raw_query": ride_request["raw_query"],
            "target_date": ride_request["target_date"],
            "origin_region": ride_request["origin_region"],
            "available_hours": ride_request["available_hours"],
            "target_distance_km": ride_request["target_distance_km"],
            "fitness_level": ride_request["fitness_level"],
            "ride_style": ride_request["ride_style"],
            "parsed_constraints": json.loads(ride_request["parsed_constraints_json"]),
            "user_profile": json.loads(ride_request["user_profile_json"]) if ride_request["user_profile_json"] else None,
            "rider_state": json.loads(ride_request["rider_state_json"]) if ride_request["rider_state_json"] else None,
            "created_at": _normalize_datetime(ride_request["created_at"]),
        },
        "weather_snapshot": None
        if weather_snapshot is None
        else {
            "id": weather_snapshot["id"],
            "weather_no": weather_snapshot["weather_no"],
            "city_code": weather_snapshot["city_code"],
            "region_code": weather_snapshot["region_code"],
            "forecast_date": weather_snapshot["forecast_date"],
            "temperature_min": weather_snapshot["temperature_min"],
            "temperature_max": weather_snapshot["temperature_max"],
            "precipitation_probability": weather_snapshot["precipitation_probability"],
            "wind_speed": weather_snapshot["wind_speed"],
            "wind_direction": weather_snapshot["wind_direction"],
            "weather_summary": weather_snapshot["weather_summary"],
            "provider_name": weather_snapshot["provider_name"],
            "raw_payload": json.loads(weather_snapshot["raw_payload_json"]) if weather_snapshot["raw_payload_json"] else None,
            "fetched_at": _normalize_datetime(weather_snapshot["fetched_at"]),
        },
        "risk_assessments": [
            {
                "entity_id": row["entity_id"],
                "risk_no": row["risk_no"],
                "route_code": row["route_code"],
                "route_name": row["route_name"],
                "recommendation_score": row["recommendation_score"],
                "overall_risk_score": row["overall_risk_score"],
                "risk_level": row["risk_level"],
                "weather_risk_score": row["weather_risk_score"],
                "climb_risk_score": row["climb_risk_score"],
                "traffic_risk_score": row["traffic_risk_score"],
                "supply_risk_score": row["supply_risk_score"],
                "return_risk_score": row["return_risk_score"],
                "crowd_risk_score": row["crowd_risk_score"],
                "reasons": json.loads(row["reasons_json"]),
                "mitigation_advice": json.loads(row["mitigation_advice_json"]),
                "created_at": _normalize_datetime(row["created_at"]),
            }
            for row in risk_assessments
        ],
        "decision_result": None
        if decision_result is None
        else {
            "id": decision_result["id"],
            "decision_no": decision_result["decision_no"],
            "recommended_route_code": decision_result["recommended_route_code"],
            "backup_route_codes": json.loads(decision_result["backup_route_codes_json"]),
            "go_decision": decision_result["go_decision"],
            "explanation": decision_result["explanation"],
            "roadbook": json.loads(decision_result["roadbook_json"]) if decision_result["roadbook_json"] else None,
            "status": decision_result["status"],
            "created_at": _normalize_datetime(decision_result["created_at"]),
        },
    }
def _normalize_datetime(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)
