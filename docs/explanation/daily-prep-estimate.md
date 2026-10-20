# How the daily PRE+ is calculated

This page explains where the **Estimated daily PRE+** figure comes from and why it is only an estimate. For the French version, see [daily-prep-estimate.fr.md](daily-prep-estimate.fr.md).

> Based on the community explanation published in [this gist](https://gist.github.com/mathieucarbou/8d83d25247821e85a693dea61fe4f0d2).

## Context

3ERL publishes every evening (around 22:00) the price that will be used to remunerate the surplus injected during the day. For ACI contracts, that price is **not** the latest quarter-hour PRE+. It is a daily average of the PRE+ values, weighted by the national solar generation profile.

## The formula

For each 15-minute slot of the day, Enedis computes:

```text
Adjusted PRE+ (slot) = PRE+ (slot) × PRD3 factor (slot)
```

- **PRE+** (Prix de Règlement positif des Écarts, positive imbalance settlement price) is published by RTE for every quarter-hour of the day.
- **PRD3** is a dynamic profile coefficient published by Enedis. It describes the shape of the national solar generation curve for the day: near zero at night, peaking around solar noon.

At the end of the day, the remuneration price is:

```text
Daily PRE+ = SUM(Adjusted PRE+ over all slots) / SUM(PRD3 factors over all slots)
```

In other words, the PRE+ of each quarter-hour only counts in proportion to how much solar power France was generating at that moment. Cheap midday hours weigh a lot; evening hours weigh almost nothing.

## Why the integration shows an *estimate*

The PRD3 profile of the current day is only known after the fact. Enedis publishes it the next morning. To display a live estimate during the day, the integration therefore combines:

- today's quarter-hourly PRE+ values from the [RTE open data API](https://www.services-rte.com/), and
- the PRD3 profile from a **past day** (default: 2 days ago, because yesterday's profile only appears late in the morning). This is the `prd3_day_offset` option.

```text
estimated_daily_PREP = SUM(today's PRE+ × past-day PRD3 factor) / SUM(PRD3 factors)
```

The PRE+ slots and the PRD3 slots are aligned by time of day (hour and minute), not by date.

## How to read the estimate during the day

- Before sunrise and after sunset, the estimate is meaningless or absent: the PRD3 factors are zero, so nothing weighs into the average yet.
- Through the morning, the estimate moves a lot, because each new slot adds a large share of the daily weight.
- From early afternoon onwards it stabilizes: most of the day's generation weight is already known, so additional slots barely change the average.

The value exposed by the integration converges towards the figure 3ERL announces in the evening. Differences remain possible because the real calculation uses the PRD3 profile of the same day, not of a past day.

## ACC contracts

For collective self-consumption (ACC), there is no daily weighting: each quarter-hour of surplus is valued at the PRE+ of that same slot. The integration exposes the current quarter-hour PRE+ for that purpose and does not use the PRD3 profile.

## Related pages

- [Concepts: how 3ERL zero-injection works](concepts.md)
- [API field reference](../reference/api-fields.md)
- [Entities reference](../reference/entities.md)
