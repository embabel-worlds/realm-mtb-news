# realm-mtb-news

Mountain-biking news for an Embabel world. Ask "what's new in enduro" and six sources answer.

Needs **no API key**. Nothing is mirrored, nothing is scheduled, nothing is stored except the
topics you choose to follow.

## What it gives the world

| | |
|---|---|
| **Types** | `MtbTopic` (stored) and `MtbNewsItem` with six per-source subtypes (virtual) |
| **Producers** | six `kind: feed` keyed RSS searches |
| **Views** | `mtb-news`, `mtb-news-by-source`, six per-source views, `mtb-tracked-topics` |
| **Skill** | `mtb-news` — routes a question to the right view and how to read the rows |

## Using it

```
view_run({ name: "mtb-news",       params: { topic: "enduro world cup" } })
view_run({ name: "mtb-pinkbike",   params: { topic: "dropper post" } })
view_run({ name: "mtb-news-by-source", params: { topic: "trail building" } })
```

`topic` is a search box, not a category — it goes to the sources verbatim. A bare component word
(`brakes`, `forks`) pulls in road cycling and motorsport; say `mtb brakes` instead.

Following a topic is optional. Every news view works on an ad-hoc phrase; saving one only makes
`mtb-tracked-topics` able to answer "what am I following".

```js
gateway.repository.createEntry({ type: 'MtbTopic', data: { topic: 'Rotorua trails' } })
```

## The sources, and what each is actually worth

Probed from this host on 2026-08-24.

| Source | Fetched via | Depth |
|---|---|---|
| open web | Google News search | current to the hour |
| Pinkbike | Google News, `site:` scoped | current to the day |
| Singletracks | **its own WordPress search feed** | current to the day; real urls, real prose summaries |
| r/MTB | Google News, `site:` scoped | patchy; opinion, not reporting |
| Vital MTB | Google News, `site:` scoped | thin — often returns archive material years old |
| BikeRadar | Google News, `site:` scoped | thin — same |

Why Google News rather than each site's own feed: `pinkbike.com/pages/rss.php` answers **403**
behind Cloudflare, `vitalmtb.com/rss` answers a JS challenge, `bikeradar.com/feed` is **404**, and
`reddit.com/r/MTB/search.rss` **429**s from a datacenter IP without OAuth (`old.reddit` serves an
interstitial instead of the feed). All are indexed by Google News, and a `site:` query against it
is a keyed search feed with no key and no bot wall. Singletracks is the exception — its own feed
answers cleanly, so it is read direct and the aggregator is not in that path.

The cost of going through Google for five of the six is that `url` is a `news.google.com` redirect
rather than the article link, and `summary` is an anchor tag rather than prose. The views report
an unusable summary as **null** rather than passing the markup off as the story's gist.

## Two things that were measured, not assumed

Both are documented at length in `types/mtb.yml` and `views/mtb.yml`, because both look like
working code and fail silently.

1. **One type per source, not one type with six relationships.** Two traversals onto a shared
   label fetch the first producer and then re-match the nodes it just materialized for the
   second — Pinkbike's stories, reported as Singletracks', with no warning. Distinct labels are
   what the engine plans a separate fetch for.
2. **One view per source, not one view with a `site` parameter.** A `WHERE $site = …` on an
   `OPTIONAL MATCH` filters after the traversal, so asking for one site fetched all six feeds and
   cost 8s instead of 0.9s. Cypher cannot gate a virtual fetch on a runtime parameter.

## Developing it

Mounted checkout — the files on disk are the realm.

```
edit  ->  realm_validate_path({ realm: "realm-mtb-news" })  ->  realm_refresh  ->  view_run
```

`scripts/test-views.py` is the battery. Read its docstring before trusting it: it needs the
appliance's admin credentials and has not yet completed a pass here, so the cases in it were
verified individually through `view_run` instead.

## Not in scope

No notifications, no digest, no sweep. News is fetched when a query asks for it. Being told when
something lands is a change to this realm — an `events/` poll source and a signal type — not
something to fake by polling on the user's behalf.
