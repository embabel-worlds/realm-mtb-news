# Mountain-biking news

Answer MTB questions from the views, not from hand-written Cypher and not from memory. A bike,
a race result or a product launch you recognise is a trap — this realm reads what the sources are
publishing today, and your recollection is months out of date.

## Pick the view

| The question | View | Params |
|---|---|---|
| "what's new in MTB", or anything topic-shaped | `mtb-news` | `topic`, `limit` |
| "who's covering X" / "is anyone writing about X" | `mtb-news-by-source` | `topic` |
| the user names a site — "what does Pinkbike say" | `mtb-news-from-site` | `topic`, `site`, `limit` |
| "what am I following" | `mtb-tracked-topics` | — |

Run one with `view_run({ name, params })`.

## Phrasing the topic

`topic` goes to the sources verbatim, so it is a search box, not a category. Phrase it as the
user would type it. A bare component word (`brakes`, `forks`, `tyres`) pulls in road cycling and
motorsport — for those, say what kind: `mtb brakes`, `mountain bike fork service`.

The web source appends "mountain biking" to the query on its own; the site-scoped ones do not
need to, because the site already constrains it.

## Reading the rows

- **`source` is the feed that carried it**, and one story can appear under two sources. That is
  not duplication in the data — items dedupe on URL — it is two feeds carrying one link, and it
  is worth saying when it happens.
- **`published` can be raw text** when a feed's date does not parse. Do not sort a list by hand
  and present it as chronological if some dates came back unparsed; the view already ordered it.
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
