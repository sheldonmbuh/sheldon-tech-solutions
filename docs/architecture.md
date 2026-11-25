# Inquiry demo architecture

The portfolio uses semantic HTML, responsive CSS, and small JavaScript modules. A static visitor can submit predefined examples to an in-memory summary with no API dependency. On loopback, the frontend checks `/api/health` before selecting the local API. The Python server binds to `127.0.0.1` and serves a fixed set of assets.

| Method | Endpoint | Result |
| --- | --- | --- |
| GET | `/api/health` | JSON status and the `local-demo` mode |
| GET | `/api/services` | Available sample identifiers and display labels |
| POST | `/api/inquiries` | Accepts a JSON object like `{"sample":"website"}` and returns the aggregate after storing the sample |
| GET | `/api/metrics` | Total and grouped service counts |

The POST accepts at most 1 KiB of JSON and validates the shape and sample ID before opening a write transaction. SQLite serializes writes and keeps accepted samples across restarts. The response includes counts from the same transaction. The diagnostics page reads the current counts and supports a manual refresh.

The data model contains just the sample identifier per submission. Each submission is an independent event. If a response is interrupted, check diagnostics before retrying. There is no intake for contact information, no email delivery, and no connection to a production CRM or campaign account.
