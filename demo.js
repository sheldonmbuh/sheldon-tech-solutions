const form = document.querySelector("#inquiry-form");
const sample = document.querySelector("#sample");
const list = document.querySelector("#inquiry-list");
const total = document.querySelector("#demo-total");
const report = document.querySelector("#demo-report");
const status = document.querySelector("#demo-status");
const button = form.querySelector("button");
const metrics = document.querySelector("#metrics-link");
const preview = new Map();
let local = false;

function render(summary) {
  total.textContent = String(summary.total);
  list.replaceChildren(...summary.by_service.map(({ service, count }) => {
    const item = document.createElement("li");
    item.textContent = `${service}: ${count}`;
    return item;
  }));
  report.hidden = false;
}

async function connect() {
  if (["localhost", "127.0.0.1"].includes(location.hostname)) {
    try {
      const health = await fetch("/api/health");
      if (health.ok && (await health.json()).mode === "local-demo") {
        local = true;
        metrics.hidden = false;
        const response = await fetch("/api/metrics");
        if (!response.ok) throw new Error("Metrics unavailable");
        render((await response.json()).metrics);
        status.textContent = "Samples are stored in the local SQLite database.";
        return;
      }
    } catch {
      if (local) {
        status.textContent = "The local server did not return its saved counts.";
        return;
      }
    }
  }
  status.textContent = "Browser preview. Reloading clears the samples.";
}

connect().finally(() => { button.disabled = false; });

form.addEventListener("submit", async event => {
  event.preventDefault();
  if (!local) {
    const service = sample.selectedOptions[0].textContent;
    preview.set(service, (preview.get(service) ?? 0) + 1);
    render({
      total: [...preview.values()].reduce((sum, count) => sum + count, 0),
      by_service: [...preview].map(([service, count]) => ({ service, count })),
    });
    status.textContent = "Sample added to the browser preview.";
    return;
  }

  button.disabled = true;
  try {
    const response = await fetch("/api/inquiries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sample: sample.value }),
    });
    if (!response.ok) throw new Error("Unable to store inquiry");
    render((await response.json()).metrics);
    status.textContent = "Sample saved in SQLite.";
  } catch {
    status.textContent = "The local server could not confirm the sample. Check diagnostics before retrying.";
  } finally {
    button.disabled = false;
  }
});
