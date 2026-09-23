from __future__ import annotations
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class EventBase(BaseModel):
    event_id: str = Field(..., max_length=32)
    event_type: str = Field(..., max_length=64)
    camera_id: str = Field(default="cam_001", max_length=64)
    roi_name: Optional[str] = Field(None, max_length=128)
    track_ids: List[int] = Field(default_factory=list)
    explanation: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    severity: str = Field(default="medium", max_length=16)
    timestamp: float = Field(default_factory=lambda: datetime.utcnow().timestamp())

    @validator("severity")
    def check_severity(cls, v: str) -> str:
        allowed = {"info", "low", "medium", "high", "critical"}
        if v not in allowed:
            raise ValueError(f"severity must be one of {allowed}")
        return v


class EventCreate(EventBase):
    pass


class EventResponse(EventBase):
    id: int
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[float] = None
    created_at: float

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    total: int
    items: List[EventResponse]


class EventAcknowledge(BaseModel):
    acknowledged_by: str = Field(..., max_length=128)


class CameraBase(BaseModel):
    id: str = Field(..., max_length=64)
    name: str = Field(..., max_length=255)
    location: Optional[str] = None
    stream_url: Optional[str] = None
    status: str = Field(default="offline", max_length=32)


class CameraCreate(CameraBase):
    pass


class CameraResponse(CameraBase):
    created_at: float
    updated_at: float

    class Config:
        from_attributes = True


class ROIBase(BaseModel):
    camera_id: str = Field(..., max_length=64)
    name: str = Field(..., max_length=128)
    polygon: List[List[int]] = Field(..., description="[[x,y], ...]")
    loitering_threshold_sec: float = 30.0
    crowd_threshold: int = 5
    color: str = "#00ff00"
    active_hours: Optional[List[int]] = None
    enabled: bool = True


class ROICreate(ROIBase):
    pass


class ROIResponse(ROIBase):
    id: int
    created_at: float
    updated_at: float

    class Config:
        from_attributes = True


class PipelineConfigUpdate(BaseModel):
    camera_id: str = Field(..., max_length=64)
    config: Dict[str, Any] = Field(default_factory=dict)
    updated_by: Optional[str] = Field(None, max_length=128)


class NLPCommandRequest(BaseModel):
    command: str = Field(..., min_length=4, max_length=500)
    camera_id: str = Field(default="cam_001", max_length=64)


class NLPCommandResponse(BaseModel):
    raw_command: str
    parsed_action: str
    json_payload: Dict[str, Any]
    confidence: float
    explanation: str
    applied: bool = False
    warnings: List[str] = Field(default_factory=list)
