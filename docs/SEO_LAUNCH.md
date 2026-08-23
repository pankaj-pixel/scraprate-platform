# ScrapRate SEO launch checklist

## Rendering approach

The React application remains a Vite SPA. `npm run build` now creates static HTML shells for the homepage-dependent public pages and the 29 currently source-backed material routes. Each shell contains an indexable H1, description, canonical URL and Open Graph basics before JavaScript runs. React then replaces the shell with live API data. This is smaller and lower-risk than migrating the application to an SSR framework.

Set `PUBLIC_SITE_URL` or `VITE_SITE_URL` during the frontend build. The backend also uses `PUBLIC_SITE_URL` for the database-driven sitemap. Configure the web server/CDN to serve generated `route/index.html` files first. Serve `dist/404.html` with HTTP 404 for unknown routes rather than returning the homepage shell. Proxy `/api`, `/sitemap.xml` and `/robots.txt` to FastAPI.

Rebuild after the set of REAL material pages changes. The dynamic sitemap remains the source of truth and includes only materials backed by real local observations.

## Google Search Console

1. Add a Domain property for the final domain.
2. Complete the DNS TXT verification supplied by Google. Do not place verification secrets in this repository.
3. Confirm the production `PUBLIC_SITE_URL` and HTTPS canonical URLs.
4. Submit `https://YOUR_DOMAIN/sitemap.xml` in the Sitemaps report.
5. Use URL Inspection for `/`, `/scrap-prices`, and representative material pages.
6. Test the live URL, request indexing, and verify the rendered H1, canonical, description and structured data.
7. Monitor Page indexing, Core Web Vitals, HTTPS and manual-action reports after launch.

## Pre-launch checks

- Confirm admin, API, submission and demo-only routes are absent from the sitemap.
- Verify `robots.txt` references the correct absolute sitemap URL.
- Confirm every sitemap URL returns HTTP 200 directly without a redirect loop.
- Validate structured data with Google Rich Results Test where applicable.
- Check that stale rates retain their visible date and freshness warning.
- Re-run Lighthouse on desktop and mobile after deploying with production caching and compression.
