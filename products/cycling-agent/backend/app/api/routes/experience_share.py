"""CN: 骑后体验分享 API，提供完成骑行、照片上传和明星片生成接口。
EN: Post-ride experience-share API for completed rides, photo upload, and postcard generation.
"""

from __future__ import annotations

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.schemas.experience import (
    CompletedRideRequestSchema,
    CompletedRideResponseSchema,
    PhotoAssetUploadResponseSchema,
    PostRideShareRequestSchema,
    PostRideShareResponseSchema,
)
from app.services.post_ride_share_service import (
    ALLOWED_IMAGE_MIME_TYPES,
    complete_ride_from_request,
    generate_post_ride_share,
    get_post_ride_share_result,
    store_ride_photo,
)


router = APIRouter(prefix="/api/v1/experience", tags=["experience-share"])


@router.post("/rides/{request_no}/complete", response_model=CompletedRideResponseSchema)
async def complete_ride(
    request_no: str,
    payload: CompletedRideRequestSchema,
    request: Request,
) -> CompletedRideResponseSchema:
    ride = complete_ride_from_request(
        request.app.state.database_url,
        request_no=request_no,
        actual_duration_hours=payload.actual_duration_hours,
        actual_distance_km=payload.actual_distance_km,
        selected_route_code=payload.selected_route_code,
        user_note=payload.user_note,
        visibility_level=payload.visibility_level,
    )
    if ride is None:
        raise HTTPException(status_code=404, detail="experience-completed-ride-plan-not-found")
    return CompletedRideResponseSchema(
        ride_no=ride["ride_no"],
        request_no=ride["request_no"],
        status="completed",
    )


@router.post("/photo-assets", response_model=PhotoAssetUploadResponseSchema)
async def upload_photo_asset(
    request: Request,
    ride_no: str = Form(...),
    photo: UploadFile = File(...),
) -> PhotoAssetUploadResponseSchema:
    if photo.content_type not in ALLOWED_IMAGE_MIME_TYPES:
        raise HTTPException(status_code=415, detail="experience-photo-unsupported-media-type")
    payload = await photo.read()
    if not payload:
        raise HTTPException(status_code=400, detail="experience-photo-empty-upload")
    if len(payload) > request.app.state.media_upload_max_bytes:
        raise HTTPException(status_code=413, detail="experience-photo-upload-too-large")
    asset = store_ride_photo(
        request.app.state.database_url,
        media_storage=request.app.state.media_storage,
        ride_no=ride_no,
        file_bytes=payload,
        mime_type=photo.content_type,
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="experience-photo-ride-not-found")
    return PhotoAssetUploadResponseSchema(
        asset_no=asset["asset_no"],
        ride_no=ride_no,
        status="uploaded",
        mime_type=asset["mime_type"],
        file_size_bytes=asset["file_size_bytes"],
        original_url=asset["original_url"],
    )


@router.post("/post-ride-shares", response_model=PostRideShareResponseSchema)
async def create_post_ride_share(
    payload: PostRideShareRequestSchema,
    request: Request,
) -> PostRideShareResponseSchema:
    try:
        share = generate_post_ride_share(
            request.app.state.database_url,
            ride_no=payload.ride_no,
            asset_no=payload.asset_no,
            style_preset=payload.style_preset,
            caption_tone=payload.caption_tone,
            channel_targets=payload.channel_targets,
            include_route_context=payload.include_route_context,
            regenerate=payload.regenerate,
            media_storage=request.app.state.media_storage,
            image_provider=request.app.state.image_provider,
            llm_provider=request.app.state.llm_provider,
        )
    except RuntimeError as exc:
        if str(exc) in {"experience-share-ride-not-found", "experience-share-asset-not-found"}:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        raise
    return PostRideShareResponseSchema.model_validate(share)


@router.get("/post-ride-shares/{share_no}", response_model=PostRideShareResponseSchema)
async def get_post_ride_share(share_no: str, request: Request) -> PostRideShareResponseSchema:
    share = get_post_ride_share_result(
        request.app.state.database_url,
        share_no=share_no,
    )
    if share is None:
        raise HTTPException(status_code=404, detail="experience-share-not-found")
    return PostRideShareResponseSchema.model_validate(share)
