"""CN: C 端骑行聊天入口，负责单轮对话理解和规划请求组装。
EN: Consumer ride chat endpoint for one-turn understanding and planner request assembly.
"""

from fastapi import APIRouter, Request

from app.agents.chat_turn_agent import build_chat_turn
from app.schemas.ride_plan import ChatTurnRequestSchema, ChatTurnResponseSchema


router = APIRouter(prefix="/api/v1/ride/chat", tags=["ride-chat"])


@router.post("/turn", response_model=ChatTurnResponseSchema)
async def create_chat_turn(payload: ChatTurnRequestSchema, request: Request) -> ChatTurnResponseSchema:
    response = build_chat_turn(
        messages=[message.model_dump() for message in payload.messages],
        planning_scene=payload.planning_scene,
        target_date=payload.target_date,
        slot_state=payload.slot_state,
        user_profile=payload.user_profile.model_dump() if payload.user_profile else None,
        rider_state=payload.rider_state.model_dump() if payload.rider_state else None,
        llm_provider=request.app.state.llm_provider,
    )
    return ChatTurnResponseSchema.model_validate(response)
