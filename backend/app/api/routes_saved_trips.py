"""
Saved trips — the itineraries behind "My trips".

These are finished plans a user pressed Save on, not planning runs. The
frontend previously kept them in localStorage under one browser-wide key,
which meant they outlived signing out and were visible to anyone else who
signed in on the same browser. Storing them against the user fixes both and
lets a trip follow the account to another device.
"""
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db import get_session
from app.db.models import SavedTrip

logger = logging.getLogger(__name__)

router_saved_trips = APIRouter(prefix="/api/v2/saved-trips", tags=["saved-trips"])


class SaveTripRequest(BaseModel):
    """A trip to keep, addressed by the planner session it came from."""
    session_id: str = Field(..., max_length=64)
    trip: Dict[str, Any]


class SavedTripSummary(BaseModel):
    """The row rendered in the trips list; the payload stays out of it."""
    id: str
    destination: Optional[str] = None
    dates: Optional[str] = None
    days: int = 0
    saved_at: str


def _summarise(trip: Dict[str, Any]) -> Dict[str, Any]:
    """Pull the list-view fields out of a trip payload.

    The payload is client-supplied, so nothing here may assume a shape.
    """
    destination = trip.get("destination")
    if not isinstance(destination, str):
        destination = None

    dates = trip.get("dates")
    if not isinstance(dates, str):
        dates = None

    itinerary = trip.get("itinerary")
    days = len(itinerary) if isinstance(itinerary, list) else 0

    return {"destination": destination, "dates": dates, "days": days}


@router_saved_trips.put("/{session_id}")
async def save_trip(
    session_id: str,
    request: SaveTripRequest,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create or replace the saved copy of one trip.

    Idempotent: saving the same session twice updates the existing row, so the
    frontend can re-save on every edit without accumulating duplicates.
    """
    if request.session_id != session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id in the body must match the URL",
        )

    fields = _summarise(request.trip)

    result = await session.execute(
        select(SavedTrip).where(
            SavedTrip.user_id == user_id,
            SavedTrip.session_id == session_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.trip = request.trip
        existing.destination = fields["destination"]
        existing.dates = fields["dates"]
        existing.days = fields["days"]
        existing.saved_at = datetime.utcnow()
    else:
        session.add(
            SavedTrip(
                id=str(uuid.uuid4()),
                user_id=user_id,
                session_id=session_id,
                trip=request.trip,
                saved_at=datetime.utcnow(),
                **fields,
            )
        )

    await session.commit()
    return {"status": "saved", "session_id": session_id}


@router_saved_trips.get("", response_model=List[SavedTripSummary])
async def list_saved_trips(
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """List this user's saved trips, newest first."""
    result = await session.execute(
        select(SavedTrip)
        .where(SavedTrip.user_id == user_id)
        .order_by(SavedTrip.saved_at.desc())
    )
    return [
        SavedTripSummary(
            id=row.session_id,
            destination=row.destination,
            dates=row.dates,
            days=row.days or 0,
            saved_at=row.saved_at.isoformat() if row.saved_at else "",
        )
        for row in result.scalars().all()
    ]


@router_saved_trips.get("/{session_id}")
async def get_saved_trip(
    session_id: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Return one saved trip in full. Scoped to the caller, so another user's
    session id reads as missing rather than forbidden."""
    result = await session.execute(
        select(SavedTrip).where(
            SavedTrip.user_id == user_id,
            SavedTrip.session_id == session_id,
        )
    )
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")

    return {"session_id": row.session_id, "trip": row.trip}


@router_saved_trips.delete("/{session_id}")
async def delete_saved_trip(
    session_id: str,
    user_id: str = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Remove a saved trip. Deleting one that is already gone is not an error."""
    await session.execute(
        delete(SavedTrip).where(
            SavedTrip.user_id == user_id,
            SavedTrip.session_id == session_id,
        )
    )
    await session.commit()
    return {"status": "deleted", "session_id": session_id}
