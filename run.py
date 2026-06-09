import logging
import sys
import traceback

import config
import db
import filters
import email_sender
from sources.adzuna import AdzunaSource


def _setup_logging() -> None:
    fmt = "%(asctime)s %(levelname)s %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            logging.FileHandler(config.LOG_PATH, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def main() -> int:
    _setup_logging()
    logger = logging.getLogger(__name__)
    try:
        db.init_db(config.DB_PATH)

        sources = [AdzunaSource()]
        all_jobs: list[dict] = []
        for source in sources:
            logger.info("Fetching from %s ...", source.name)
            fetched = source.fetch()
            logger.info("  %d listings fetched", len(fetched))
            for j in fetched:
                logger.info(j.get("title",""))
            all_jobs.extend(fetched)

        filtered = filters.apply_filters(all_jobs)
        logger.info("%d listings after filtering (from %d total)", len(filtered), len(all_jobs))

        new_jobs = db.filter_new(filtered, config.DB_PATH)
        logger.info("%d new listings (not previously seen)", len(new_jobs))

        if not new_jobs:
            logger.info("No new listings found — skipping email")
            return 0

        db.mark_seen(new_jobs, config.DB_PATH)
        email_sender.send_digest(new_jobs)
        logger.info("Digest sent: %d new listings", len(new_jobs))
        return 0

    except Exception:
        logging.error("Pipeline failed:\n%s", traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
