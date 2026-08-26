from datetime import datetime
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session
from app.models import VisitorEvent

def create_event(session: Session, **values) -> VisitorEvent:
    event = VisitorEvent(**values); session.add(event); session.commit(); return event

def summary(session: Session, since: datetime, today: datetime, limit: int = 100) -> dict:
    base = [VisitorEvent.occurred_at >= since]
    page = [*base, VisitorEvent.event_name == "page_view"]
    scalar = lambda stmt: session.execute(stmt).scalar_one()
    totals = {
        "events": scalar(select(func.count(VisitorEvent.id)).where(*base)),
        "page_views": scalar(select(func.count(VisitorEvent.id)).where(*page)),
        "unique_visitors": scalar(select(func.count(distinct(VisitorEvent.visitor_hash))).where(*base)),
        "sessions": scalar(select(func.count(distinct(VisitorEvent.session_hash))).where(*base)),
        "today_page_views": scalar(select(func.count(VisitorEvent.id)).where(VisitorEvent.event_name == "page_view", VisitorEvent.occurred_at >= today)),
    }
    def grouped(column, filters=page, amount=10):
        rows=session.execute(select(column.label("name"),func.count(VisitorEvent.id).label("count")).where(*filters).group_by(column).order_by(func.count(VisitorEvent.id).desc()).limit(amount)).all()
        return [{"name": row.name or "Direct / unknown", "count": row.count} for row in rows]
    day=func.date(VisitorEvent.occurred_at)
    daily=session.execute(select(day.label("date"),func.count(VisitorEvent.id).label("page_views"),func.count(distinct(VisitorEvent.visitor_hash)).label("visitors")).where(*page).group_by(day).order_by(day)).all()
    recent=session.execute(select(VisitorEvent).where(*page).order_by(VisitorEvent.occurred_at.desc()).limit(limit)).scalars().all()
    return {**totals,"top_pages":grouped(VisitorEvent.path),"top_referrers":grouped(VisitorEvent.referrer_domain),"devices":grouped(VisitorEvent.device_type,base),"browsers":grouped(VisitorEvent.browser,base),"daily":[{"date":str(x.date),"page_views":x.page_views,"visitors":x.visitors} for x in daily],"recent_visits":[{"time":x.occurred_at,"visitor":x.visitor_hash[:10],"path":x.path,"referrer":x.referrer_domain,"device":x.device_type,"browser":x.browser,"operating_system":x.operating_system} for x in recent]}
