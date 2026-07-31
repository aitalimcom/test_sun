"""Cron job scheduler for KrishiMitra agents.

Simple in-memory scheduler that runs agent tasks on schedules.
For demo: uses asyncio tasks with sleep intervals.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class CronJob:
    """A scheduled task."""

    def __init__(
        self,
        name: str,
        agent_name: str,
        interval_seconds: int,
        description: str = "",
        description_np: str = "",
        enabled: bool = True,
    ):
        self.name = name
        self.agent_name = agent_name
        self.interval_seconds = interval_seconds
        self.description = description
        self.description_np = description_np
        self.enabled = enabled
        self.last_run: datetime | None = None
        self.next_run: datetime | None = None
        self.run_count = 0
        self.last_result: str = ""
        self._task: asyncio.Task | None = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "agent": self.agent_name,
            "interval_seconds": self.interval_seconds,
            "description": self.description,
            "description_np": self.description_np,
            "enabled": self.enabled,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "run_count": self.run_count,
            "last_result": self.last_result,
        }


class CronScheduler:
    """Manages and runs cron jobs."""

    def __init__(self) -> None:
        self.jobs: dict[str, CronJob] = {}
        self._running = False
        self._loop_task: asyncio.Task | None = None

    def register(
        self,
        name: str,
        agent_name: str,
        interval_seconds: int,
        description: str = "",
        description_np: str = "",
    ) -> CronJob:
        """Register a new cron job."""
        job = CronJob(
            name=name,
            agent_name=agent_name,
            interval_seconds=interval_seconds,
            description=description,
            description_np=description_np,
        )
        self.jobs[name] = job
        logger.info(f"Cron job registered: {name} (every {interval_seconds}s)")
        return job

    async def start(self) -> None:
        """Start the cron scheduler."""
        if self._running:
            return
        self._running = True
        self._loop_task = asyncio.create_task(self._run_loop())
        logger.info("Cron scheduler started")

    async def stop(self) -> None:
        """Stop the cron scheduler."""
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        logger.info("Cron scheduler stopped")

    async def _run_loop(self) -> None:
        """Main loop that checks and runs jobs."""
        while self._running:
            now = datetime.now()
            for job in self.jobs.values():
                if not job.enabled:
                    continue
                if job.next_run is None or now >= job.next_run:
                    await self._run_job(job)
                    job.next_run = now + timedelta(seconds=job.interval_seconds)
            await asyncio.sleep(10)  # Check every 10 seconds

    async def _run_job(self, job: CronJob) -> None:
        """Execute a cron job."""
        logger.info(f"Running cron job: {job.name}")
        job.last_run = datetime.now()
        job.run_count += 1

        try:
            from agents.registry import dispatch_to_agent
            result = await dispatch_to_agent(
                agent_name=job.agent_name,
                query=f"Execute scheduled task: {job.name}",
                state={"language": "ne-NP", "cron": True},
            )
            job.last_result = str(result)[:200]
            logger.info(f"Cron job {job.name} completed")
        except Exception as e:
            job.last_result = f"Error: {str(e)[:100]}"
            logger.error(f"Cron job {job.name} failed: {e}")

    def get_status(self) -> list[dict]:
        """Get status of all cron jobs."""
        return [job.to_dict() for job in self.jobs.values()]

    def enable(self, name: str) -> None:
        """Enable a cron job."""
        if name in self.jobs:
            self.jobs[name].enabled = True

    def disable(self, name: str) -> None:
        """Disable a cron job."""
        if name in self.jobs:
            self.jobs[name].enabled = False


# Global scheduler instance
cron_scheduler = CronScheduler()


def setup_default_jobs() -> None:
    """Set up the default cron jobs."""
    cron_scheduler.register(
        name="daily_briefing",
        agent_name="daily",
        interval_seconds=86400,  # 24 hours
        description="Generate morning briefing with weather, tasks, alerts",
        description_np="बिहानको ब्रिफिङ: मौसम, कार्य, सूचना",
    )
    cron_scheduler.register(
        name="weather_sync",
        agent_name="weather",
        interval_seconds=21600,  # 6 hours
        description="Sync weather data from OpenWeatherMap",
        description_np="मौसम डेटा सिंक",
    )
    cron_scheduler.register(
        name="price_sync",
        agent_name="market",
        interval_seconds=3600,  # 1 hour
        description="Sync market prices from Kalimati",
        description_np="बजार मूल्य सिंक",
    )
    cron_scheduler.register(
        name="iot_check",
        agent_name="iot_status",
        interval_seconds=3600,  # 1 hour
        description="Check IoT device health and trigger actions",
        description_np="आईओटी उपकरण स्वास्थ्य जाँच",
    )
    cron_scheduler.register(
        name="calendar_sync",
        agent_name="calendar",
        interval_seconds=86400,  # 24 hours
        description="Generate today's task list",
        description_np="आजको कार्य सूची बनाउने",
    )
    cron_scheduler.register(
        name="bajar_analysis",
        agent_name="bajar",
        interval_seconds=86400,  # 24 hours
        description="Analyze market trends and generate insights",
        description_np="बजार विश्लेषण र अन्तर्दृष्टि",
    )
