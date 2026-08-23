from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError
from app.schemas import PriceSubmissionCreate
from app.services import price_submission_service as service

def payload(**changes):
    values = dict(source="trusted-dealer", city="delhi", material="copper", grade=None,
        date=date(2026, 8, 22), low=Decimal("700"), average=Decimal("710"), high=Decimal("720"), unit="kg")
    values.update(changes); return PriceSubmissionCreate(**values)

def refs(source_type="dealer", active=True, source_city=None):
    source = SimpleNamespace(id=1, slug="trusted-dealer", name="Trusted Dealer", source_type=source_type,
        is_active=active, city_id=source_city, trust_score=Decimal("80"))
    city = SimpleNamespace(id=2, slug="delhi", name="Delhi")
    material = SimpleNamespace(id=3, slug="copper", name="Copper", unit="kg")
    grade = SimpleNamespace(id=4, slug="a", name="A")
    return source, city, material, grade

def wire(monkeypatch, *, source_type="dealer", active=True, city=True, material=True, grade=True, source_city=None):
    source, city_obj, material_obj, grade_obj = refs(source_type, active, source_city)
    monkeypatch.setattr(service.material_service, "find_price_source", lambda *_: source)
    monkeypatch.setattr(service.material_service, "find_city", lambda *_: city_obj if city else None)
    monkeypatch.setattr(service.material_service, "find_material", lambda *_: material_obj if material else None)
    monkeypatch.setattr(service.material_service, "find_grade", lambda *_: grade_obj if grade else None)
    monkeypatch.setattr(service.price_submission_repository, "find_pending_duplicate", lambda *a, **k: None)
    item = SimpleNamespace(id=9, source=source, city=city_obj, material=material_obj, material_grade=None,
        price_date=date(2026,8,22), low_price=Decimal("700"), average_price=Decimal("710"), high_price=Decimal("720"),
        unit="kg", status="pending", submitted_at=datetime.now(), reviewed_at=None, review_notes=None, approved_price_observation_id=None,
        price_source_id=1, city_id=2, material_id=3, material_grade_id=None)
    monkeypatch.setattr(service.price_submission_repository, "add", lambda *a, **k: item)
    return item

@pytest.mark.parametrize("source_type", ["dealer", "recycler"])
def test_valid_eligible_submission(monkeypatch, source_type):
    wire(monkeypatch, source_type=source_type)
    assert service.create(MagicMock(), payload())["status"] == "pending"

def test_admin_source_rejected(monkeypatch):
    wire(monkeypatch, source_type="admin")
    with pytest.raises(service.SubmissionValidation, match="dealer or recycler"): service.create(MagicMock(), payload())

def test_inactive_source_rejected(monkeypatch):
    wire(monkeypatch, active=False)
    with pytest.raises(service.SubmissionValidation, match="inactive"): service.create(MagicMock(), payload())

def test_invalid_price_range():
    with pytest.raises(ValidationError): payload(low=Decimal("730"), average=Decimal("710"))

def test_invalid_city(monkeypatch):
    wire(monkeypatch, city=False)
    with pytest.raises(service.SubmissionValidation, match="Invalid city"): service.create(MagicMock(), payload())

def test_invalid_grade(monkeypatch):
    wire(monkeypatch, grade=False)
    with pytest.raises(service.SubmissionValidation, match="Invalid grade"): service.create(MagicMock(), payload(grade="bad"))

def test_duplicate_pending(monkeypatch):
    item = wire(monkeypatch)
    monkeypatch.setattr(service.price_submission_repository, "find_pending_duplicate", lambda *a, **k: item)
    with pytest.raises(service.SubmissionConflict, match="pending submission"): service.create(MagicMock(), payload())

def test_approval_creates_one_real_observation(monkeypatch):
    item = wire(monkeypatch); session = MagicMock()
    monkeypatch.setattr(service.price_submission_repository, "get", lambda *a, **k: item)
    monkeypatch.setattr(service.price_submission_repository, "find_observation", lambda *a, **k: None)
    session.flush.side_effect = lambda: setattr(session.add.call_args.args[0], "id", 77)
    result = service.approve(session, 9, "verified")
    observation = session.add.call_args.args[0]
    assert observation.is_demo is False and observation.source_id == 1
    assert result["approved_price_observation_id"] == 77

def test_double_approval_is_idempotent(monkeypatch):
    item = wire(monkeypatch); item.status = "approved"; item.approved_price_observation_id = 77
    session = MagicMock(); monkeypatch.setattr(service.price_submission_repository, "get", lambda *a, **k: item)
    service.approve(session, 9, None)
    session.add.assert_not_called()

def test_equivalent_observation_conflicts(monkeypatch):
    item = wire(monkeypatch); session = MagicMock()
    monkeypatch.setattr(service.price_submission_repository, "get", lambda *a, **k: item)
    monkeypatch.setattr(service.price_submission_repository, "find_observation", lambda *a, **k: object())
    with pytest.raises(service.SubmissionConflict, match="equivalent"): service.approve(session, 9, None)

def test_rejection_creates_no_observation(monkeypatch):
    item = wire(monkeypatch); session = MagicMock()
    monkeypatch.setattr(service.price_submission_repository, "get", lambda *a, **k: item)
    result = service.reject(session, 9, "insufficient evidence")
    assert result["status"] == "rejected" and result["approved_price_observation_id"] is None
    session.add.assert_not_called()
