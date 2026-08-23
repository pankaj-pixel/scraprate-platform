from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.ingestion.adapters.registry import adapter_registry
from app.ingestion.base import ParsedPriceRow
from app.ingestion import service as ingestion_service
from app.repositories import data_source_repository, ingestion_repository

class DataSourceError(Exception): pass
class DataSourceNotFound(DataSourceError): pass
class AdapterUnsupported(DataSourceError): pass
class DataSourceDisabled(DataSourceError): pass

def _run_dict(run):
    if not run: return None
    return {"id": run.id, "started_at": run.started_at, "completed_at": run.completed_at, "status": run.status,
        "records_received": run.records_received, "records_valid": run.records_valid, "records_inserted": run.records_inserted,
        "duplicates": run.duplicates, "rejected": run.rejected, "error_message": run.error_message}

def list_sources(session: Session):
    sources = data_source_repository.list_sources(session); latest = data_source_repository.latest_runs(session, [x.id for x in sources])
    return [{"id": x.id, "name": x.name, "slug": x.slug, "source_type": x.source_type, "city": x.city.name if x.city else None,
        "is_active": x.is_active, "is_verified": x.is_verified, "trust_score": x.trust_score,
        "adapter_name": x.adapter_config.adapter_name if x.adapter_config else None, "adapter_enabled": x.adapter_config.enabled if x.adapter_config else False,
        "polling_frequency": x.adapter_config.polling_frequency if x.adapter_config else None,
        "last_success_at": x.adapter_config.last_success_at if x.adapter_config else None, "last_attempt_at": x.adapter_config.last_attempt_at if x.adapter_config else None,
        "last_error": x.adapter_config.last_error if x.adapter_config else None, "consecutive_failures": x.adapter_config.consecutive_failures if x.adapter_config else 0,
        "adapter_registered": bool(x.adapter_config and adapter_registry.create(x.adapter_config.adapter_name)), "latest_run": _run_dict(latest.get(x.id))} for x in sources]

def run_source(session: Session, source_id: int):
    source = data_source_repository.get_source(session, source_id)
    if not source: raise DataSourceNotFound("Price source not found")
    config = source.adapter_config
    if not config: raise AdapterUnsupported("No adapter is configured for this source")
    if not source.is_active or not config.enabled: raise DataSourceDisabled("Source or adapter is disabled")
    adapter = adapter_registry.create(config.adapter_name)
    if not adapter: raise AdapterUnsupported(f"Adapter '{config.adapter_name}' is not registered")
    if adapter.source_identifier != source.slug: raise AdapterUnsupported("Registered adapter source identifier does not match this source")
    run = data_source_repository.create_run(session, source.id); now = datetime.now(timezone.utc); config.last_attempt_at = now; session.commit()
    try:
        observations = adapter.collect(); run.records_received = len(observations)
        parsed=[]; metadata={}; rejected=0
        for number, observation in enumerate(observations, 1):
            errors = adapter.validate(observation)
            if observation.source.strip().lower() != source.slug.lower(): errors.append("Observation source does not match configured source")
            if errors: rejected += 1; continue
            raw={"raw_reference": observation.raw_reference or "", **{str(k): str(v) for k,v in observation.metadata.items()}}
            parsed.append(ParsedPriceRow(number, observation.date, observation.city, observation.material, observation.grade,
                Decimal(observation.low_price), Decimal(observation.average_price), Decimal(observation.high_price), observation.unit, source.slug, raw, observation.price_context))
            metadata[number]=(observation.raw_reference, observation.metadata)
        normalized, categories = ingestion_service._normalize(session, parsed)
        valid, duplicates = ingestion_service._separate_duplicates(session, normalized)
        rejected += len(categories["invalid"]); run.records_valid = len(valid); run.duplicates = len(duplicates); run.rejected = rejected
        values=[]
        for row in valid:
            raw_reference, extra = metadata[row.row_number]
            values.append({"material_id":row.material_id,"material_grade_id":row.grade_id,"city_id":row.city_id,"price_date":row.date,
                "price_low":row.low_price,"price_average":row.average_price,"price_high":row.high_price,"unit":row.unit,"source_id":row.source_id,
                "source_type":row.source_type,"confidence_score":row.confidence_score,"is_demo":False,"raw_reference":raw_reference,"observation_metadata":extra or None,"price_context":row.price_context})
        try: ids=ingestion_repository.insert_real_observations(session, values) if values else []
        except IntegrityError as exc: session.rollback(); raise DataSourceError("Concurrent duplicate prevented ingestion") from exc
        run.records_inserted=len(ids); run.status="success" if not rejected and not duplicates else "partial"; run.completed_at=datetime.now(timezone.utc)
        config.last_success_at=run.completed_at; config.last_error=None; config.consecutive_failures=0; session.commit()
        return _run_dict(run)
    except Exception as exc:
        session.rollback(); run=session.get(type(run), run.id); config=session.get(type(config), config.id)
        run.status="failed"; run.completed_at=datetime.now(timezone.utc); run.error_message=str(exc)[:2000]
        config.last_error=run.error_message; config.consecutive_failures += 1; session.commit()
        if isinstance(exc, DataSourceError): raise
        raise DataSourceError(f"Adapter run failed: {exc}") from exc
