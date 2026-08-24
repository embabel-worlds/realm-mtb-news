---
name: mtb-news
description: 'Mountain-biking news — what is new in MTB, on a discipline, a race series, a component or a trail network, and what a named site (Pinkbike, Singletracks, Vital MTB, BikeRadar, r/MTB) is saying about it. Activate for any question about current mountain-biking news, race results, product launches or rider opinion, and before running any mtb-* view. Answers come from live feeds, never from recollection.'
---

# Mountain-biking news

Answer MTB questions from the views, not from hand-written Cypher and not from memory. A bike,
a race result or a product launch you recognise is a trap — this realm reads what the sources are
publishing today, and your recollection is months out of date.

## Pick the view

| The question | View | Params |
|---|---|---|
| "what's new in MTB", or anything topic-shaped | `mtb-news` | `topic`, `limit` |
| "who's covering X" / "is anyone writing about X" | `mtb-news-by-source` | `topic` |
| the user names a site | `mtb-pinkbike`, `mtb-singletracks`, `mtb-vitalmtb`, `mtb-bikeradar`, `mtb-reddit`, `mtb-web` | `topic`, `limit` |
| "what am I following" | `mtb-tracked-topics` | — |

Run one with `view_run({ name, params })`.

**Reach for a per-source view whenever the user names a site.** `mtb-news` fetches six feeds and
takes seconds; a per-source view fetches one and takes under a second. The saving is real and the
answer is the same.

## Phrasing the topic

`topic` goes to the sources verbatim, so it is a search box, not a category. Phrase it as the
user would type it. A bare component word (`brakes`, `forks`, `tyres`) pulls in road cycling and
motorsport — for those, say what kind: `mtb brakes`, `mountain bike fork service`.

The web source appends "mountain biking" to the query on its own; the site-scoped ones do not
need to, because the site already constrains it.

## Reading the rows

- **`sources` lists every feed carrying that link** (in `mtb-news`; the per-source views have no
  such column, since the source is the view). Two entries is not duplication — items dedupe on
  URL — it is two feeds running one story, which is worth saying when it happens.
- **The same story can still appear twice under different urls**, when one source links the
  article directly and another carries an aggregator link to it. Recognise it by title.
- **`published` is normalised to ISO by the view**, from two different feed formats. Null means
  the date was unparseable — say the date is unknown rather than guessing from position.
- **Coverage depth varies sharply by source.** Pinkbike, Singletracks and the open web are current
  to within a day; Vital MTB and BikeRadar are indexed thinly and often return archive material
  years old. Check `published` before calling something new.
- **`summary` is often empty.** A thin feed is not a thin story — don't summarise absence.
- **Read `warnings` before the rows.** A `PRODUCER_ERROR` on one source means that source failed,
  not that it has nothing. Say which source was unavailable rather than answering as though the
  sweep were complete. Zero rows with a warning is a broken fetch; zero rows without one is a
  genuinely quiet topic.

## Following a topic

Saving a topic is `gateway.repository.createEntry({ type: 'MtbTopic', data: { topic, notes } })`
from `code_mode`. It is not a prerequisite for anything — every news view works on an ad-hoc
phrase. Save one when the user says they want something followed, not merely because they asked
about it once.

## What this realm does not do

It does not notify. There is no sweep and no digest — news is fetched when a query asks for it and
is never stored, so there is nothing that arrives on its own. If the user wants to be told when
something lands, that is a change to the realm, not something to fake by polling on their behalf.
