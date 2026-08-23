from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from app.repositories import benchmark_repository

class BenchmarkNotFound(Exception): pass

def get_benchmark(session: Session, material_slug: str):
    material=benchmark_repository.get_material(session,material_slug)
    if not material: raise BenchmarkNotFound("Material not found")
    rows=benchmark_repository.latest_two(session,material.id)
    if not rows: raise BenchmarkNotFound("No benchmark data available for this material")
    current=rows[0]; metadata=current.observation_metadata or {}
    previous_close=Decimal(metadata["previous_close"]) if metadata.get("previous_close") else (Decimal(rows[1].price_average) if len(rows)>1 else None)
    change=Decimal(current.price_average)-previous_close if previous_close is not None else None
    change_percent=(change/previous_close*Decimal("100")) if change is not None and previous_close else None
    money=lambda x:x.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP) if x is not None else None
    return {"material":material.name,"slug":material.slug,"benchmark_source":current.source.name,"date":current.price_date,
        "close":current.price_average,"previous_close":money(previous_close),"change":money(change),"change_percent":money(change_percent),
        "high":current.price_high,"low":current.price_low,"contract":metadata.get("contract"),"unit":current.unit,
        "source_reference":current.raw_reference,"last_updated":current.updated_at}
