# Daily price collection

Run all explicitly enabled source adapters once:

```powershell
cd backend
python -m app.ingestion.run_daily
```

The command uses the same validation, source attribution, duplicate protection, and run auditing as the admin **Run Source** action. Repeating it on the same day is safe. A later collection date creates a new observation even when a published rate is unchanged.

For a soft launch, schedule this command after the source's normal update window using one deployment-controlled mechanism such as cron, Windows Task Scheduler, an ECS scheduled task, or EventBridge. Do not run overlapping copies. Alert on a non-zero exit code and review `/admin/data-sources` after failures.
# Production scheduling examples

The collector is idempotent: duplicate source observations are skipped, failed sources do not delete or replace current prices, and remaining enabled sources still run. It exits `1` if any source fails and `0` when every enabled source completes.

## Windows Task Scheduler

Create a daily task using an account that can read the deployed backend and its environment file:

- Program: `C:\path\to\venv\Scripts\python.exe`
- Arguments: `-m app.ingestion.run_daily`
- Start in: `C:\path\to\scraprate\backend`
- Trigger: daily after the expected source publication time
- Enable “Run whether user is logged on or not” and record stdout/stderr in the platform logging system.
- Configure a reasonable execution timeout and alert on a non-zero exit code.

Test the exact task command manually before enabling the schedule. Do not run overlapping instances.

## Future AWS EventBridge / ECS scheduled task

Package the backend command in the same application container. Define an ECS task whose command is:

```text
python -m app.ingestion.run_daily
```

Use EventBridge Scheduler to invoke it daily. Store `DATABASE_URL` and other secrets in AWS Secrets Manager, send logs to CloudWatch, configure task retry/dead-letter handling, and alert on a non-zero container exit code. Use a single desired invocation to avoid overlapping runs. This repository does not create AWS infrastructure.
