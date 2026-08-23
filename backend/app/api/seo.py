from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db

router = APIRouter(tags=["seo"])


@router.get("/sitemap.xml", include_in_schema=False)
def sitemap(session: Session = Depends(get_db)):
    """Index only materials with at least one real local-scrap observation."""
    slugs = session.execute(text("""
        SELECT DISTINCT m.slug FROM materials m
        JOIN scrap_prices p ON p.material_id = m.id
        WHERE p.is_demo = 0 AND p.price_context = 'local_scrap' AND m.is_active = 1
        ORDER BY m.slug
    """)).scalars().all()
    base = get_settings().public_site_url.rstrip("/")
    urls = [f"{base}/", f"{base}/scrap-prices", *[f"{base}/scrap-price/{slug}" for slug in slugs]]
    body = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>{escape(url)}</loc></url>\n" for url in urls) + "</urlset>"
    return Response(body, media_type="application/xml")


@router.get("/robots.txt", include_in_schema=False, response_class=PlainTextResponse)
def robots():
    base = get_settings().public_site_url.rstrip("/")
    return f"User-agent: *\nAllow: /\nDisallow: /admin/\nDisallow: /submit-price\nDisallow: /api/\nSitemap: {base}/sitemap.xml\n"
