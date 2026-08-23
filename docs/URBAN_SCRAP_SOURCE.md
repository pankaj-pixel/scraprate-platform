# Urban Scrap dealer-rate source

Source page: <https://urbanscrap.co/scrap-rates/>

Urban Scrap publishes its own Delhi NCR buying rates. These observations are classified as `dealer` + `local_scrap`; they are not an official or comprehensive Delhi market price.

## Geography decision

The page publishes one common Delhi NCR rate list rather than separate rates for Delhi, Gurgaon, Noida, Faridabad, and Ghaziabad. ScrapRate therefore stores each observation once against its existing default Delhi market record and preserves `region=Delhi NCR` in observation metadata. It does not copy one quote into five city histories.

## Setup

From `backend/`:

```powershell
python scripts/setup_urban_scrap_source.py
```

The script is idempotent. It creates an initially unverified dealer source with trust score 50 and a disabled `urban_scrap` adapter. Review a live preview before explicitly enabling the adapter configuration.

## Initial mappings

| Published item | ScrapRate material |
|---|---|
| Iron | Iron / MS |
| Aluminium | Aluminium |
| Brass | Brass |
| Copper | Copper |
| Newspaper | Newspaper |
| Cardboard | Cardboard |

Generic Steel is not treated as Stainless Steel. Generic Plastic is not treated as PET. Wires, appliances, batteries, e-waste, and per-piece items remain excluded pending explicit material/grade modeling.

Each run uses the collection date because the page does not currently display a rate date. A repeated run on the same date is duplicate-safe; the following date creates a new history point even if the published value is unchanged.
