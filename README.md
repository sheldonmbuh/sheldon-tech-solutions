# Sheldon Tech Solutions

Founder-led web development, local search, and IT support for small businesses. Sheldon Mbuh founded the agency in Kitchener–Waterloo and works with clients in English and French. [Business website](https://sheldontechsolutions.com/) · [Public engineering portfolio](https://sheldonmbuh.github.io/sheldon-tech-solutions/)

## Selected work

- [Red River Fence & Deck](https://github.com/sheldonmbuh/red-river-fencing) covers a WordPress build, local SEO, Google Business Profile, Google Ads, and the quote-request journey.
- Akum Cleaning Solutions commissioned branding, a domain, professional email setup, and Google Business Profile work.
- PLUS+ Construction commissioned business-profile and online-presence work.
- Home and small-office engagements include networking, surveillance camera setup, and device support.

## Run the demo

Requirements are Python 3.11 or later and a modern browser. The application uses the standard library and SQLite.

```sh
python3 -m unittest discover -s tests -v
node --check demo.js
node --check ops.js
python3 server/app.py
```

Open [the local portfolio](http://127.0.0.1:8765/) and choose a sample inquiry. The service count updates after the database transaction commits. [Local diagnostics](http://127.0.0.1:8765/ops.html) shows API health and aggregate counts. The database starts empty and is created at `data/samples.sqlite3`. Use `--database` to point a run at a separate file.

The public GitHub Pages site runs an in-memory preview that clears on reload. The Python API binds to localhost and accepts only predefined sample IDs. The production business website and client systems are separate.

[Architecture and API](docs/architecture.md)
