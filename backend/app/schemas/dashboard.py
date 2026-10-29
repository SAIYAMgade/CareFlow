from pydantic import BaseModel
from typing import List, Dict, Any

class DashboardKpis(BaseModel):
    appointments_today: int
    patients_checked_in: int
    patients_waiting: int
    encounters_in_progress: int
    encounters_completed_today: int
    orders_awaiting_results: int
    results_awaiting_review: int
    open_data_quality_issues: int

class HourlyVolumeItem(BaseModel):
    hour: int
    scheduled: int
    checked_in: int

class StatusDistributionItem(BaseModel):
    status: str
    count: int

class WaitTimeDeptItem(BaseModel):
    department: str
    avg_wait_minutes: float

class OrderTurnaroundItem(BaseModel):
    order_code: str
    order_name: str
    avg_turnaround_hours: float

class ExceptionCategoryItem(BaseModel):
    severity: str
    count: int

class DashboardChartsResponse(BaseModel):
    hourly_volume: List[HourlyVolumeItem]
    encounter_distribution: List[StatusDistributionItem]
    wait_time_by_dept: List[WaitTimeDeptItem]
    order_turnaround: List[OrderTurnaroundItem]
    exceptions_by_severity: List[ExceptionCategoryItem]
