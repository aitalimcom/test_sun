"""Cron scheduler for IoT monitoring and background tasks."""
import asyncio
import logging
from datetime import datetime
from typing import Callable, Any

logger = logging.getLogger(__name__)


class CronJob:
    def __init__(
        self,
        name: str,
        func: Callable,
        interval_seconds: int,
        description: str = "",
        enabled: bool = True,
    ):
        self.name = name
        self.func = func
        self.interval_seconds = interval_seconds
        self.description = description
        self.enabled = enabled
        self.last_run: datetime | None = None
        self.run_count = 0
        self.last_error: str | None = None


class CronScheduler:
    def __init__(self):
        self.jobs: dict[str, CronJob] = {}
        self._running = False
        self._task: asyncio.Task | None = None

    def register(
        self,
        name: str,
        func: Callable,
        interval_seconds: int,
        description: str = "",
        enabled: bool = True,
    ) -> CronJob:
        job = CronJob(name, func, interval_seconds, description, enabled)
        self.jobs[name] = job
        logger.info(f"Cron job registered: {name} (every {interval_seconds}s)")
        return job

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Cron scheduler started")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Cron scheduler stopped")

    async def _run_loop(self):
        while self._running:
            await asyncio.sleep(10)  # Check every 10 seconds
            now = datetime.now()
            for job in self.jobs.values():
                if not job.enabled:
                    continue
                if job.last_run is None:
                    # First run after 30 seconds of startup
                    elapsed = 30
                else:
                    elapsed = (now - job.last_run).total_seconds()
                if elapsed >= job.interval_seconds:
                    await self._run_job(job)

    async def _run_job(self, job: CronJob):
        try:
            logger.info(f"Running cron job: {job.name}")
            if asyncio.iscoroutinefunction(job.func):
                await job.func()
            else:
                job.func()
            job.last_run = datetime.now()
            job.run_count += 1
            job.last_error = None
            logger.info(f"Cron job completed: {job.name} (run #{job.run_count})")
        except Exception as e:
            job.last_error = str(e)
            logger.error(f"Cron job failed: {job.name} — {e}")

    def toggle(self, name: str, enabled: bool) -> bool:
        if name in self.jobs:
            self.jobs[name].enabled = enabled
            return True
        return False

    def get_status(self) -> list[dict]:
        return [
            {
                "name": job.name,
                "description": job.description,
                "interval_seconds": job.interval_seconds,
                "enabled": job.enabled,
                "last_run": job.last_run.isoformat() if job.last_run else None,
                "run_count": job.run_count,
                "last_error": job.last_error,
            }
            for job in self.jobs.values()
        ]


cron_scheduler = CronScheduler()


async def _monitor_tick():
    """Cron job: run IoT monitoring check."""
    from agents.iot_monitor.agent import run_monitor_check
    await run_monitor_check()


async def _weather_sync_tick():
    """Cron job: sync weather device data."""
    from db import iot_db
    from routes.iot import _generate_mock_reading
    import json
    device = iot_db.get_device("weather-001")
    if device:
        sensors = json.loads(device.get("sensors_json", "[]"))
        actuators = json.loads(device.get("actuators_json", "[]"))
        data = _generate_mock_reading("weather", sensors, actuators)
        iot_db.append_telemetry("weather-001", data)
        battery = int(device.get("battery", 100))
        iot_db.update_device("weather-001", {"battery": str(max(0, battery - 1))})
        logger.info(f"Weather station synced: {data}")


def setup_default_jobs():
    """Register default cron jobs."""
    cron_scheduler.register(
        name="iot_monitor",
        func=_monitor_tick,
        interval_seconds=3600,  # Every hour
        description="Check all IoT sensor readings against thresholds and generate alerts",
    )
    cron_scheduler.register(
        name="weather_sync",
        func=_weather_sync_tick,
        interval_seconds=30,  # Every 30 seconds (for demo; real would be longer)
        description="Sync weather station telemetry data",
    )
