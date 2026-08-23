"""Run every enabled adapter once. Invoke with: python -m app.ingestion.run_daily"""
import logging
from datetime import datetime, timezone

from app.database import SessionLocal
from app.repositories.data_source_repository import enabled_automated_sources
from app.services.data_source_service import DataSourceError, run_source

logging.basicConfig(level=logging.INFO, format="%(asctime)sZ %(levelname)s %(message)s", datefmt="%Y-%m-%dT%H:%M:%S")
logger = logging.getLogger("scraprate.collector")


def run_daily() -> dict:
    results=[]; failures=[]
    with SessionLocal() as session:
        source_ids=[source.id for source in enabled_automated_sources(session)]
        for source_id in source_ids:
            try:
                logger.info("Starting source_id=%s", source_id)
                result = run_source(session, source_id)
                results.append({"source_id": source_id, "run": result})
                logger.info("Finished source_id=%s status=%s inserted=%s duplicates=%s rejected=%s", source_id, result["status"], result["records_inserted"], result["duplicates"], result["rejected"])
            except DataSourceError as error:
                failures.append({"source_id": source_id, "error": str(error)})
                logger.error("Failed source_id=%s error=%s", source_id, error)
    return {"completed_at": datetime.now(timezone.utc).isoformat(), "sources_attempted":len(source_ids),"results":results,"failures":failures}

if __name__ == "__main__":
    outcome=run_daily()
    for item in outcome["results"]:
        run=item["run"]; print(f"source={item['source_id']} status={run['status']} inserted={run['records_inserted']} duplicates={run['duplicates']} rejected={run['rejected']}")
    for item in outcome["failures"]: print(f"source={item['source_id']} status=failed error={item['error']}")
    raise SystemExit(1 if outcome["failures"] else 0)
