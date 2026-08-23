from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from app.ingestion.adapters import mcx
from app.services.market_price_service import calculate_indicative_rate

HEADER="INSTRUMENT,SYMBOL,EXPIRY_DT,OPEN,HIGH,LOW,CLOSE,PREV_CLOSE,TIMESTAMP\n"
def payload(rows): return (HEADER+"\n".join(rows)+"\n").encode()

@pytest.fixture
def adapter(monkeypatch):
    monkeypatch.setattr(mcx,"get_settings",lambda:SimpleNamespace(mcx_bhavcopy_url="https://www.mcxindia.com/official/bhavcopy.csv"))
    return mcx.McxBhavcopyAdapter()

def test_copper_mapping(): assert mcx.map_commodity("COPPER")=="copper"
def test_aluminium_mapping(): assert mcx.map_commodity("ALUMINIUM")=="aluminium"
def test_unsupported_commodity():
    with pytest.raises(mcx.McxPayloadError,match="Unsupported"): mcx.map_commodity("COPPERM")

def test_mcx_normalization_and_nearest_contract(adapter):
    raw=payload(["FUTCOM,COPPER,30-Sep-2026,800,825,790,810,805,22-Aug-2026","FUTCOM,COPPER,31-Oct-2026,801,830,795,815,810,22-Aug-2026","FUTCOM,ALUMINIUM,30-Sep-2026,250,260,245,255,252,22-Aug-2026"])
    rows=adapter.normalize(adapter.parse(raw)); copper=next(x for x in rows if x.material=="copper")
    assert len(rows)==2 and copper.average_price==Decimal("810") and copper.city is None and copper.price_context=="benchmark"
    assert copper.metadata["benchmark"] is True and copper.metadata["contract"]=="COPPER-2026-09-30"

@pytest.mark.parametrize("raw",[b"",b"bad,data\n1,2\n",payload(["FUTCOM,COPPER,bad,800,825,790,810,805,22-Aug-2026"])])
def test_malformed_mcx_payload(adapter,raw):
    with pytest.raises(mcx.McxPayloadError): adapter.normalize(adapter.parse(raw)) if raw else adapter.parse(raw)

def test_benchmark_excluded_from_local_calculation():
    base=dict(low=Decimal("700"),average=Decimal("710"),high=Decimal("720"),unit="kg",trust_score=Decimal("80"),is_verified=True,is_active=True,is_demo=False,price_date=date.today(),last_updated=datetime.now())
    benchmark=SimpleNamespace(**base,price_context="benchmark")
    local=SimpleNamespace(**{**base,"average":Decimal("500")},price_context="local_scrap")
    assert calculate_indicative_rate([benchmark,local]).indicative_price==Decimal("500.00")

def test_benchmark_endpoint(monkeypatch):
    from app.main import app
    from app.services import benchmark_service
    result={"material":"Copper","slug":"copper","benchmark_source":"MCX Official Bhavcopy","date":"2026-08-22","close":810,"previous_close":805,"change":5,"change_percent":0.62,"high":825,"low":790,"contract":"COPPER-2026-09-30","unit":"kg","source_reference":"https://www.mcxindia.com/official/bhavcopy.csv","last_updated":"2026-08-22T18:00:00"}
    monkeypatch.setattr(benchmark_service,"get_benchmark",lambda *a:result)
    response=TestClient(app).get("/api/v1/benchmarks/copper")
    assert response.status_code==200 and response.json()["benchmark_source"]=="MCX Official Bhavcopy"
