from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.models import IngestionRun, PriceSource, SourceAdapterConfig

def list_sources(session: Session):
    return list(session.scalars(select(PriceSource).options(joinedload(PriceSource.city), joinedload(PriceSource.adapter_config)).order_by(PriceSource.name)).unique())

def get_source(session: Session, source_id: int):
    return session.scalar(select(PriceSource).options(joinedload(PriceSource.city), joinedload(PriceSource.adapter_config)).where(PriceSource.id == source_id))

def latest_runs(session: Session, source_ids: list[int]):
    if not source_ids: return {}
    runs = list(session.scalars(select(IngestionRun).where(IngestionRun.source_id.in_(source_ids)).order_by(IngestionRun.source_id, IngestionRun.started_at.desc())))
    result = {}
    for run in runs: result.setdefault(run.source_id, run)
    return result

def create_run(session: Session, source_id: int):
    run = IngestionRun(source_id=source_id, status="running")
    session.add(run); session.commit(); return run

def enabled_automated_sources(session: Session):
    return list(session.scalars(select(PriceSource).join(SourceAdapterConfig).options(joinedload(PriceSource.adapter_config)).where(PriceSource.is_active.is_(True), SourceAdapterConfig.enabled.is_(True)).order_by(PriceSource.id)).unique())
