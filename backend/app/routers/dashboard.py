from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from ..services.auth_service import get_current_user
from ..services.dashboard_service import DashboardService

from ..services.time_service import TimeService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/today")
async def get_today_dashboard(
    date: Optional[str] = Query(None, description="Date YYYY-MM-DD"),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    date_str = date or TimeService.get_current_local_date_str()
    return await DashboardService.get_today_dashboard(user_id, date_str)

@router.get("/week")
async def get_week_dashboard(
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    return await DashboardService.get_trend_history(user_id, days=7)

@router.get("/month")
async def get_month_dashboard(
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user.get("id") or str(current_user.get("_id"))
    return await DashboardService.get_trend_history(user_id, days=30)
