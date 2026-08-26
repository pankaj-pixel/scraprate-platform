import hashlib, hmac, re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse
from sqlalchemy.orm import Session
from app.config import get_settings
from app.repositories import analytics_repository
from app.schemas import VisitorEventCreate

def _hash(value: str) -> str:
    return hmac.new(get_settings().analytics_hash_salt.encode(), value.encode(), hashlib.sha256).hexdigest()

def _client(ua: str) -> tuple[str,str,str]:
    low=ua.lower(); device="mobile" if re.search(r"mobile|android|iphone",low) else "tablet" if "ipad" in low else "desktop"
    browser="Edge" if "edg/" in low else "Chrome" if "chrome/" in low else "Firefox" if "firefox/" in low else "Safari" if "safari/" in low else "Other"
    os="Windows" if "windows" in low else "Android" if "android" in low else "iOS" if "iphone" in low or "ipad" in low else "macOS" if "mac os" in low else "Linux" if "linux" in low else "Other"
    return device,browser,os

def record(session: Session, payload: VisitorEventCreate, user_agent: str) -> None:
    settings=get_settings()
    if not settings.analytics_enabled: return
    parsed=urlparse(payload.referrer or "")
    referrer=parsed.hostname[:255] if parsed.hostname else None
    device,browser,os=_client(user_agent)
    analytics_repository.create_event(session,visitor_hash=_hash(payload.visitor_id),session_hash=_hash(payload.session_id),event_name=payload.event_name,path=payload.path,referrer_domain=referrer,device_type=device,browser=browser,operating_system=os,material_slug=payload.material_slug,city=payload.city)

def get_summary(session: Session, days: int) -> dict:
    now=datetime.now(timezone.utc); start=now-timedelta(days=days); today=now.replace(hour=0,minute=0,second=0,microsecond=0)
    return {"days":days,**analytics_repository.summary(session,start,today)}
