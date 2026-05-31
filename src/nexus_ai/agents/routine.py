from datetime import date

from nexus_ai.adapters.ticketing import RoutineTask, TicketingAdapter, build_ticketing_adapter


class RoutineAgent:
    def __init__(self, ticketing_adapter: TicketingAdapter | None = None) -> None:
        self.ticketing_adapter = ticketing_adapter or build_ticketing_adapter()

    def get_daily_routine(self) -> list[RoutineTask]:
        return self.ticketing_adapter.list_routine_tasks()

    def get_routine_snapshot(self) -> dict:
        tasks = self.get_daily_routine()
        today = date.today().isoformat()
        overdue_tasks = [task for task in tasks if not task.completed and task.due_on and task.due_on < today]
        due_today_tasks = [task for task in tasks if not task.completed and task.due_on == today]
        open_tasks = [task for task in tasks if not task.completed]

        if len(overdue_tasks) >= 2:
            risk_level = "high"
        elif overdue_tasks or due_today_tasks:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "tasks": tasks,
            "open_count": len(open_tasks),
            "overdue_count": len(overdue_tasks),
            "due_today_count": len(due_today_tasks),
            "risk_level": risk_level,
            "routine_summary": (
                f"{len(open_tasks)} open tasks, {len(due_today_tasks)} due today, and {len(overdue_tasks)} overdue."
            ),
        }
