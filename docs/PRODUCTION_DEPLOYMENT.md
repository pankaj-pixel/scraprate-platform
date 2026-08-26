# Production configuration

Required backend variables are documented in `backend/.env.example`. In production set:

- `ENVIRONMENT=production`
- `DATABASE_URL` with a secret-managed MySQL credential
- `DATABASE_SSL=true` and the provider CA where available
- `PUBLIC_SITE_URL=https://your-domain`
- `CORS_ORIGINS=https://your-domain`
- `ALLOWED_HOSTS=your-domain,api.your-domain` as applicable
- freshness thresholds
- Urban Scrap source URL, collector user-agent and timeout
- `ANALYTICS_HASH_SALT` with a private random value of at least 24 characters
- `ADMIN_API_KEY` with a private random value of at least 24 characters

Startup fails when production uses a non-HTTPS public URL, localhost CORS origins, wildcard hosts, or an unsupported environment name. API documentation is disabled in production. Never commit `.env` or credentials.

Frontend build variables are documented in `frontend/.env.example`. Analytics is disabled unless `VITE_GA_MEASUREMENT_ID` is supplied. Configure cache headers for hashed assets, compression, HTTPS, security headers, and static-route handling at the CDN or reverse proxy.

The first-party dashboard is available at `/admin/analytics`. Its key is entered by the operator and retained only in browser session storage. Do not embed `ADMIN_API_KEY` in the frontend build. The analytics table stores hashed random identifiers and does not store raw IP addresses.
