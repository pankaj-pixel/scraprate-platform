from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from app.ingestion.adapters.base import AdapterObservation, PriceSourceAdapter
from app.ingestion.adapters.registry import AdapterRegistry, adapter_registry
from app.services import data_source_service as service

class MockAdapter(PriceSourceAdapter):
    def __init__(self, rows=None, error=None): self.rows=rows or []; self.error=error
    @property
    def source_identifier(self): return "test-source"
    def fetch(self):
        if self.error: raise self.error
        return self.rows
    def parse(self, raw): return raw
    def normalize(self, rows): return rows

def observation(**changes):
    values=dict(source="test-source",material="copper",city="delhi",date=date(2026,8,22),low_price=Decimal("700"),average_price=Decimal("710"),high_price=Decimal("720"),unit="kg",raw_reference="feed:1",metadata={"batch":"A"})
    values.update(changes); return AdapterObservation(**values)

def test_registered_adapter():
    registry=AdapterRegistry(); registry.register("mock", lambda: MockAdapter())
    assert isinstance(registry.create("MOCK"), MockAdapter) and registry.names()==("mock",)

def test_unknown_adapter():
    assert AdapterRegistry().create("missing") is None

def test_invalid_normalized_observation():
    adapter=MockAdapter(); bad=observation(low_price=Decimal("730"))
    assert adapter.validate(bad)==["low_price must be <= average_price <= high_price"]

class Config: pass
class Run: pass

def setup_run(monkeypatch, rows, *, duplicates=0, invalid=0, error=None):
    config=Config(); config.id=2; config.adapter_name="test-adapter"; config.enabled=True; config.last_attempt_at=None; config.last_success_at=None; config.last_error=None; config.consecutive_failures=0
    source=SimpleNamespace(id=1,slug="test-source",name="Test",is_active=True,adapter_config=config)
    run=Run(); run.id=3; run.source_id=1; run.started_at=datetime.now(); run.completed_at=None; run.status="running"; run.records_received=0; run.records_valid=0; run.records_inserted=0; run.duplicates=0; run.rejected=0; run.error_message=None
    session=MagicMock(); session.get.side_effect=lambda cls, _: run if cls is Run else config
    monkeypatch.setattr(service.data_source_repository,"get_source",lambda *a: source)
    monkeypatch.setattr(service.data_source_repository,"create_run",lambda *a: run)
    adapter_registry.register("test-adapter",lambda: MockAdapter(rows,error))
    normalized=[SimpleNamespace(row_number=i+1,material_id=10,grade_id=None,city_id=20,date=x.date,low_price=x.low_price,average_price=x.average_price,high_price=x.high_price,unit=x.unit,source_id=1,source_type="dealer",confidence_score=Decimal("0.8"),price_context=x.price_context) for i,x in enumerate(rows[:max(0,len(rows)-invalid)])]
    monkeypatch.setattr(service.ingestion_service,"_normalize",lambda *a:(normalized,{"invalid":[object()]*invalid}))
    monkeypatch.setattr(service.ingestion_service,"_separate_duplicates",lambda *a:(normalized[:max(0,len(normalized)-duplicates)],[object()]*duplicates))
    monkeypatch.setattr(service.ingestion_repository,"insert_real_observations",lambda s,v:list(range(100,100+len(v))))
    return session,run,config

def teardown_function(): adapter_registry.unregister("test-adapter")

def test_successful_ingestion_run(monkeypatch):
    session,run,config=setup_run(monkeypatch,[observation()])
    result=service.run_source(session,1)
    assert result["status"]=="success" and result["records_inserted"]==1 and config.consecutive_failures==0

def test_duplicate_observation_is_partial(monkeypatch):
    session,run,_=setup_run(monkeypatch,[observation()],duplicates=1)
    result=service.run_source(session,1)
    assert result["status"]=="partial" and result["duplicates"]==1 and result["records_inserted"]==0

def test_partial_ingestion_with_rejected_row(monkeypatch):
    rows=[observation(),observation(raw_reference="feed:2")]
    session,run,_=setup_run(monkeypatch,rows,invalid=1)
    result=service.run_source(session,1)
    assert result["status"]=="partial" and result["rejected"]==1 and result["records_inserted"]==1

def test_adapter_exception_records_failed_audit(monkeypatch):
    session,run,config=setup_run(monkeypatch,[],error=RuntimeError("feed unavailable"))
    with pytest.raises(service.DataSourceError,match="Adapter run failed"): service.run_source(session,1)
    assert run.status=="failed" and "feed unavailable" in run.error_message and config.consecutive_failures==1

def test_run_audit_counts_received_valid_inserted(monkeypatch):
    rows=[observation(),observation(raw_reference="feed:2")]
    session,run,_=setup_run(monkeypatch,rows)
    result=service.run_source(session,1)
    assert (result["records_received"],result["records_valid"],result["records_inserted"])==(2,2,2)
