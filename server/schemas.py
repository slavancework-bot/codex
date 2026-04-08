"""Pydantic schemas used by the FastAPI server."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReminderCreateRequest(BaseModel):
    message: str = Field(min_length=1)
    scheduled_time: datetime
    created_by: str = "admin"
    repeat_type: Literal["one_time", "weekly"]
    day_of_week: int | None = Field(default=None, ge=0, le=6)
    user_ids: list[int] = Field(min_length=1)


class ReminderStatusUpdateRequest(BaseModel):
    reminder_id: int
    user_id: int
    action: Literal["done", "snooze"]
    snooze_minutes: int | None = Field(default=None, ge=1, le=120)


class ReminderDue(BaseModel):
    reminder_id: int
    assignment_id: int
    message: str
    repeat_type: str
    scheduled_time: str
    due_at: str


class UserOut(BaseModel):
    id: int
    name: str
    computer_name: str
