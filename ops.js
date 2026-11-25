const health = document.querySelector("#health");
const total = document.querySelector("#total");
const list = document.querySelector("#services-list");
const refresh = document.querySelector("#refresh");

async function update() {
  refresh.disabled = true;
  try {
    if (!["localhost", "127.0.0.1"].includes(location.hostname)) throw new Error();
    const [healthResponse, metricsResponse] = await Promise.all([
      fetch("/api/health"),
      fetch("/api/metrics"),
    ]);
    if (!healthResponse.ok || !metricsResponse.ok) throw new Error();
    const { mode } = await healthResponse.json();
    if (mode !== "local-demo") throw new Error();
    const { metrics } = await metricsResponse.json();
    health.textContent = "Local API online";
    total.textContent = String(metrics.total);
    list.replaceChildren(...metrics.by_service.map(({ service, count }) => {
      const item = document.createElement("li");
      item.textContent = `${service}: ${count}`;
      return item;
    }));
  } catch {
    health.textContent = "Local API unavailable. Start the Python server to see saved counts.";
    total.textContent = "—";
    list.replaceChildren();
  } finally {
    refresh.disabled = false;
  }
}

refresh.addEventListener("click", update);
update();
