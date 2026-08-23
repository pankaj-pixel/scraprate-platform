# Real Price Source Requirements

ScrapRate currently has no verified external provider configured. Provider names, endpoints, and commercial terms are **TBD** until independently verified. No URL or feed should be added merely because it appears plausible.

## Price concepts

- **Benchmark price:** a broader commodity or reference-market signal. It is not a local scrap quote.
- **Local scrap price:** a dated dealer or recycler quote for a material, grade, and city.
- **Transaction price:** a completed, evidenced ScrapRate transaction in a future marketplace.

These must retain distinct source types and trust scores. A benchmark must never be represented as a confirmed local or transaction price.

## Metals

| Material | Required evidence | Provider |
|---|---|---|
| Copper | Commodity benchmark plus verified local dealer/recycler quotes | TBD |
| Brass | Verified dealer/recycler quotes and local market observations | TBD |
| Aluminium | Commodity benchmark plus grade-specific local quotes | TBD |
| Iron / Steel | Regional recycler/dealer quotes and grade-specific local observations | TBD |
| Stainless Steel | Alloy/grade-specific recycler quotes and reference benchmarks | TBD |

### MCX benchmark adapter

ScrapRate supports official MCX contract-level end-of-day Bhavcopy data for the full `COPPER` and `ALUMINIUM` futures symbols. MCX describes Bhavcopy as end-of-day, contract-wise open/high/low/close data with volume, value, and open interest. It is a derivatives benchmark—not a Delhi NCR dealer quote.

Official references:

- Bhavcopy: <https://www.mcxindia.com/market-data/bhavcopy>
- Historical data: <https://www.mcxindia.com/market-data/historical-data>
- MCX data-feed description: <https://www.mcxindia.com/technology/datafeed>

MCX does not publish a stable unauthenticated download API contract on these pages. Therefore ScrapRate does not guess or hardcode an internal endpoint. Configure `MCX_BHAVCOPY_URL` with the exact official HTTPS CSV/ZIP download URL obtained from MCX. The adapter rejects every non-`mcxindia.com` host.

Explicit setup—this is never run by seed or startup:

```powershell
cd backend
python scripts/setup_mcx_source.py
```

This creates, if absent, a verified national `market_reference` source with trust score 85 and a disabled `mcx_bhavcopy` adapter configuration. Review the official file and set `MCX_BHAVCOPY_URL`, then explicitly enable the adapter configuration before using the admin **Run** action.

Mapping is deliberately narrow:

- `COPPER` → base material `copper`
- `ALUMINIUM` → base material `aluminium`
- Mini contracts, options, and scrap grades are ignored

For each commodity/trading date, the adapter selects the nearest non-expired full futures contract. Benchmark observations have no city and use `price_context=benchmark`; local indicative and historical queries only use `price_context=local_scrap`.

## Paper

| Material | Required evidence | Provider |
|---|---|---|
| Cardboard | Local recycler/dealer quotes by quality and quantity | TBD |
| Newspaper | Local dealer/recycler quotes and grade/condition observations | TBD |

## Plastics

| Material | Required evidence | Provider |
|---|---|---|
| PET | Grade/condition-specific recycler quotes and local observations | TBD |

## Electronics

| Material | Required evidence | Provider |
|---|---|---|
| E-waste | Authorized recycler quotes with category and condition detail | TBD |

## Adapter onboarding checklist

1. Verify provider identity, authority, license, and usage terms.
2. Create an appropriate price source with a conservative trust score.
3. Keep secrets in environment variables or managed secret storage; store only a configuration reference in MySQL.
4. Implement and test a registered adapter that emits normalized observations.
5. Validate units, locations, grades, price ranges, dates, and duplicates through the shared ingestion service.
6. Review run health and sample raw references before enabling recurring invocation.

## Future scheduling

The ingestion service remains an ordinary callable operation. A future deployment may invoke the admin/service command using cron, AWS EventBridge, a scheduled Lambda, or an ECS scheduled task. No scheduler is selected or implemented yet.
