# Dice Chess Bot — Python Starter

[![CI](https://github.com/fortemate/dicechess-bot-python/actions/workflows/ci.yml/badge.svg)](https://github.com/fortemate/dicechess-bot-python/actions/workflows/ci.yml)
[![Play Live](https://img.shields.io/badge/Play-Live-success)](https://fortemate.com/)
[![Leaderboard](https://img.shields.io/badge/Ladder-Leaderboard-1E90FF)](https://fortemate.com/leaderboard)
[![License: MIT](https://img.shields.io/badge/License-MIT-lightgrey)](./LICENSE)

A complete, **runnable** Dice Chess bot in dependency-free Python using only the standard library. It mints an
anonymous identity, challenges the house sparring bot, and plays full games by
walking the legal-move tree the server sends each turn — so **you never implement
a single rule of the variant.**

MIT-licensed: copy it into a closed-source bot with no strings attached. Playing
over the wire imposes no obligation, and this starter links no engine.

## Quickstart

[**Use this template**](https://github.com/fortemate/dicechess-bot-python/generate) → clone your copy → run:

```bash
python bot.py
```

That's it. No dependencies, no signup — it mints an anonymous token and starts
playing `house/greedy` immediately. You'll see moves land in the log:

```
INFO minted anonymous identity bot:team:anon:python-starter-…
INFO game c0f0…: played e2e3 d1f3 b1c3 (v11)
```

Requires Python 3.9+ (Python 3.12+ recommended).

## Make it yours

The only decision the bot makes is in **`choose_move`** (`bot.py`) — the baseline
walks a random root-to-leaf path of the legal-move tree. Replace it with your
strategy; everything else (auth, discovery, the activity loop, retries) is
transport you can leave alone.

```python
def choose_move(legal_moves: dict) -> list[str]:
    # legal_moves is a prefix tree of UCI micro-moves; a leaf ({}) is a full turn.
    # Return the path you want to play, or [] for a forced pass.
    ...
```

## Going further

- **A durable identity** (survives restarts, joins the rating ladder): set
  `DICECHESS_TOKEN` to a registered token instead of minting anonymously.
- **Environment overrides:** `DICECHESS_TOKEN`, `DICECHESS_BASE_URL`,
  `DICECHESS_OPPONENT` (`team/name`, default `house/greedy`), `DICECHESS_NAME`,
  `DICECHESS_POLL_SECONDS`.
- **[Play against it yourself](https://fortemate.com/)**
  from the public lobby, before joining the ladder — confirms it plays a legal game end to end.

## Serverless: webhook mode

Instead of polling, you can run as a **webhook**: register one HTTPS callback and the server
POSTs when it's your turn — your HTTP response body is the move. The handler is stateless (it
needs only the signing secret, never a token), so it drops into a cloud function.

```bash
# 1. Deploy webhook.py at a public HTTPS URL, then register it (needs a REGISTERED token):
DICECHESS_TOKEN=<registered-token> python register.py https://your-url/
#    → prints DICECHESS_WEBHOOK_SECRET=…

# 2. Run the handler with that secret:
DICECHESS_WEBHOOK_SECRET=<secret> python webhook.py
```

For local testing, expose it with a tunnel (`cloudflared tunnel --url http://localhost:8080`)
and register the tunnel URL. To deploy to AWS Lambda / Cloudflare Workers / Azure Functions,
call `dicechess.webhook.handle_delivery` from your platform's request handler — it is pure and
verifies the HMAC signature for you. Same `choose_move` as the poll bot.

## What's inside

| File | Role |
| --- | --- |
| `bot.py` | The runnable poll-only bot and its `choose_move` — **edit this**. |
| `dicechess/client.py` | Thin transport client: auth, REST calls, retry/backoff, `Retry-After`, 401 re-mint. |
| `webhook.py` · `register.py` | Serverless webhook handler and one-time registration helper. |
| `dicechess/webhook.py` | Pure delivery logic: HMAC verification + move selection (reuse it in any function runtime). |

## Connection modes

This starter uses **polling** — the simplest mode, ideal for a cron/serverless
function. For pure serverless register a **webhook** (the server POSTs your turns).
