import argparse
import logging
import sys
import traceback

import config
import db
import filters
import email_sender
from sources.adzuna import AdzunaSource
from sources.jobspy_source import JobSpySource

_FORMAT = "%(asctime)s %(levelname)s %(message)s"

# Log lines of the run currently going in this process (read by the website).
current_log: list[str] = []


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format=_FORMAT,
        handlers=[
            logging.FileHandler(config.LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


class _ListHandler(logging.Handler):
    """Collects one run's log lines so they can be saved with the run."""

    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []
        self.setFormatter(logging.Formatter(_FORMAT))

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append(self.format(record))


def main(force: bool = False) -> int:
    _setup_logging()
    logger = logging.getLogger(__name__)
    db.init_db(config.DB_PATH)

    if db.run_in_progress(config.DB_PATH):
        logger.info("Another run is already in progress — skipping")
        return 0
    if not force:
        hours = db.hours_since_last_success(config.DB_PATH)
        if hours is not None and hours < config.MIN_HOURS_BETWEEN_RUNS:
            logger.info("Last successful run was %.1fh ago (< %dh) — skipping",
                        hours, config.MIN_HOURS_BETWEEN_RUNS)
            return 0

    run_id = db.start_run(config.DB_PATH)
    global current_log
    capture = _ListHandler()
    current_log = capture.lines
    logging.getLogger().addHandler(capture)
    counts: dict = {}
    try:
        sources = [AdzunaSource(), JobSpySource()]
        all_jobs: list[dict] = []
        for source in sources:
            logger.info("Fetching from %s ...", source.name)
            try:
                fetched = source.fetch()
            except Exception:
                logger.error("Source %s failed:\n%s", source.name, traceback.format_exc())
                continue
            logger.info("  %d listings fetched", len(fetched))
            all_jobs.extend(fetched)
        counts["fetched"] = len(all_jobs)

        filtered = filters.apply_filters(all_jobs)
        counts["filtered"] = len(filtered)
        logger.info("%d listings after filtering (from %d total)", len(filtered), len(all_jobs))

        new_jobs = db.filter_new(filtered, config.DB_PATH)
        counts["new_count"] = len(new_jobs)
        logger.info("%d new listings (not previously seen)", len(new_jobs))

        # Save before emailing: the website is the record, the email is a nudge.
        db.mark_seen(new_jobs, config.DB_PATH)

        if not new_jobs:
            logger.info("No new listings found — skipping email")
        else:
            try:
                email_sender.send_digest(new_jobs)
                logger.info("Digest sent: %d new listings", len(new_jobs))
            except Exception:
                logger.error("Email failed (jobs are still on the website):\n%s",
                             traceback.format_exc())
        status, code = "ok", 0

    except Exception:
        logger.error("Pipeline failed:\n%s", traceback.format_exc())
        status, code = "failed", 1
    finally:
        logging.getLogger().removeHandler(capture)

    db.finish_run(config.DB_PATH, run_id, status, "\n".join(capture.lines), **counts)
    return code


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch, filter, store and email new job listings.")
    parser.add_argument("--force", action="store_true",
                        help=f"run even if the last run was under {config.MIN_HOURS_BETWEEN_RUNS}h ago")
    sys.exit(main(force=parser.parse_args().force))
