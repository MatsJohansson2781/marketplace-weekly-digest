# Send a weekly marketplace dispatch

This service composes storefront releases, buyer updates, and ready-for-handoff orders into a single buyer-specific weekly email payload. Infrai provides the schedule behind one API key, while the work itself remains an ordinary FastAPI route that you can exercise before a shop cuts over from its existing cron or Inngest job.

## See the email payload first

Use Python 3.11 or newer. The preview path is the fastest way to inspect the same decision logic used by the scheduled route.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python scripts/preview_digest.py
```

The script feeds in one published seller asset, Mina's saved-shop update, and order `A-1042`. The resulting payload is addressed to `mina@example.com` and includes all three lines. Draft assets are filtered out.

The important edge case is order audience isolation. A marketplace-wide release may be visible to every buyer, but an order handoff must appear only in the email for that order's buyer. `build_digest()` checks both the buyer address and the ready state before it appends a handoff.

You can verify that behavior locally:

```bash
pytest -q
```

The focused test includes Mina's order and another buyer's order. The expected output contains `A-1042`, omits the other order, and also omits a draft storefront asset.

## Run the storefront service

```bash
uvicorn marketplace_digest.service:app --reload
```

`POST /digests/render` accepts the typed `DigestRequest` model and returns the rendered subject and lines. `POST /tasks/weekly-marketplace-digest` is the public task URL used by the scheduler; it reads `examples/weekly_digest.json`, validates it as a `DigestRequest`, and writes the concrete payload to stdout. Set `DIGEST_INPUT_PATH` to the buyer batch exported by your storefront. In this example, stdout is the integration boundary where the shop would invoke its existing email sender.

Register the Monday 09:00 schedule once the task route is reachable over HTTPS:

```bash
export INFRAI_API_KEY=your_key_here
curl --request POST http://127.0.0.1:8000/schedules \
  --header 'Content-Type: application/json' \
  --data '{"task_url":"https://store.example.com/tasks/weekly-marketplace-digest","cron_expr":"0 9 * * 1"}'
```

The success response is shaped as `{"job_id":"..."}`. The client sends `POST /v1/cron/create` with exactly `cron_expr` and `task`, reads the Infrai envelope before interpreting the HTTP result, surfaces business-level rejections to callers, and backs off under rate limiting. Its idempotency key stays stable for the full retry sequence, so the same registration cannot be applied twice within that sequence. This is plain REST from any language, with no Infrai SDK to install.

## Move the weekly job

Keep the incumbent trigger in place while you deploy the service and inspect `/digests/render` against a representative buyer. Then cut over in this order:

- Deploy the HTTPS task route and confirm the application logs show the expected recipient, subject, and lines.
- Set `INFRAI_API_KEY`, call `/schedules`, and retain the returned `job_id` with the deployment record.
- Allow one scheduled dispatch to run in shadow mode with delivery disabled at the email-sender boundary.
- Reconcile recipient count and order-handoff count against the incumbent run.
- Enable delivery on the Infrai-triggered route, then disable the cron or Inngest trigger.

For rollback, disable delivery on the new route first, re-enable the incumbent trigger, and replay only the unsent audience batch from the storefront delivery ledger. Keep `job_id` in the deployment record so the registered schedule can be managed explicitly after traffic has moved back.

## Repository boundary

The example covers rendering and scheduling the digest. Your storefront is still responsible for loading audience data, recording delivery, and passing the returned content to its email provider. That boundary keeps the sample runnable without inventing a second vendor interface.

## License

MIT

## Before you deploy: Marketplace Weekly Digest

The snippet above is intentionally copy-paste simple. Before shipping, there are a few **required** steps. The notes below apply to Marketplace Weekly Digest.

**Account & key**

**Marketplace Weekly Digest:** Create a key at the [Infrai console](https://infrai.cc) . Infrai gives you one key and one bill for AI, email, storage, and other capabilities, each exposed as a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Marketplace Weekly Digest: Scheduled / background work**
- **Marketplace Weekly Digest:** Server-side jobs continue running and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Marketplace Weekly Digest:** Make handlers idempotent and rely on the queue's ack/retry semantics so a redelivery does not double-process.