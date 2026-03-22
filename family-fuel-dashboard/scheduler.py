"""
Cross-platform daily scheduler for the Family Fuel ETL pipeline.

Run this process to keep data fresh automatically:
    python scheduler.py

It will run the pipeline once at startup, then daily at 06:00.
Keep the process alive (e.g., in a tmux session or systemd service).

Alternative: use cron (Mac/Linux)
    0 6 * * * cd /path/to/family-fuel-dashboard && python etl/run_pipeline.py >> logs/etl.log 2>&1
"""
import logging
import sys
from pathlib import Path

import schedule
import time

sys.path.insert(0, str(Path(__file__).parent))

from etl.run_pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def scheduled_run() -> None:
    log.info("Scheduled pipeline run triggered")
    try:
        run_pipeline()
    except Exception as exc:
        log.error(f"Pipeline run failed: {exc}")


if __name__ == "__main__":
    log.info("Scheduler starting — pipeline will run daily at 06:00")

    # Run immediately on startup so data is fresh right away
    log.info("Running pipeline now (startup run)...")
    scheduled_run()

    # Then schedule daily at 06:00
    schedule.every().day.at("06:00").do(scheduled_run)

    log.info("Waiting for next scheduled run at 06:00 daily...")
    while True:
        schedule.run_pending()
        time.sleep(60)
