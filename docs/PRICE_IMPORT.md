# Real price CSV import

`sample_real_prices.csv` is a formatting template only. Its dates, prices, and
source values are fictional and must not be treated as real market data.

Before importing, replace `replace-with-active-source` with the slug or name of
an existing active price source configured in ScrapRate. Preview the file in
the internal admin page and review every accepted and rejected row before
committing it.

Required columns, in any order, are:

`date, city, material, grade, low_price, average_price, high_price, unit, source`

Dates use `YYYY-MM-DD`. Grade may be empty for a base material observation.
