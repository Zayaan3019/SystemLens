const state = {
  cpu: [],
  mem: [],
  disk: [],
  net: [],
  maxPoints: 60,
};

const statusPill = document.getElementById("status-pill");
const authTokenInput = document.getElementById("auth-token");
const saveTokenBtn = document.getElementById("save-token");
const deviceName = document.getElementById("device-name");
const deviceOs = document.getElementById("device-os");
const deviceCores = document.getElementById("device-cores");
const headlineMetrics = document.getElementById("headline-metrics");
const headlineLog = document.getElementById("headline-log");
const processTable = document.getElementById("process-table");
const alertList = document.getElementById("alert-list");
const gpuMetrics = document.getElementById("gpu-metrics");
const thermalLog = document.getElementById("thermal-log");
const batteryMetrics = document.getElementById("battery-metrics");
const timelineList = document.getElementById("timeline-list");
const killTopBtn = document.getElementById("kill-top");
const clearTempBtn = document.getElementById("clear-temp");
const stopServiceBtn = document.getElementById("stop-service");
const serviceNameInput = document.getElementById("service-name");
const actionOutput = document.getElementById("action-output");
const exportMetricsBtn = document.getElementById("export-metrics");
const exportAlertsBtn = document.getElementById("export-alerts");
const exportReportBtn = document.getElementById("export-report");
const installBtn = document.getElementById("install-btn");

const cpuChart = document.getElementById("cpu-chart");
const memChart = document.getElementById("mem-chart");
const diskChart = document.getElementById("disk-chart");
const netChart = document.getElementById("net-chart");

const getToken = () => localStorage.getItem("systemlens_token") || "";
const setToken = (value) => localStorage.setItem("systemlens_token", value);
if (authTokenInput) {
  authTokenInput.value = getToken();
}

const authHeaders = () => {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
};

const buildUrl = (path) => {
  const token = getToken();
  if (!token || !path.startsWith("/api/stream")) {
    return path;
  }
  return `${path}?token=${encodeURIComponent(token)}`;
};

const formatBytes = (value) => {
  if (value === null || value === undefined) {
    return "-";
  }
  const units = ["B", "KB", "MB", "GB", "TB"];
  let idx = 0;
  let size = value;
  while (size >= 1024 && idx < units.length - 1) {
    size /= 1024;
    idx += 1;
  }
  return `${size.toFixed(1)} ${units[idx]}`;
};

const setStatus = (text) => {
  statusPill.textContent = text;
};

const resizeCanvas = (canvas) => {
  const ratio = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width * ratio;
  canvas.height = rect.height * ratio;
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  return ctx;
};

const drawSeries = (canvas, series, color) => {
  const ctx = resizeCanvas(canvas);
  const width = canvas.getBoundingClientRect().width;
  const height = canvas.getBoundingClientRect().height;
  ctx.clearRect(0, 0, width, height);

  if (!series.length) {
    ctx.fillStyle = "rgba(255,255,255,0.35)";
    ctx.font = "14px Space Grotesk, sans-serif";
    ctx.fillText("Waiting for data", 12, height / 2);
    return;
  }

  const padding = 16;
  const maxValue = Math.max(...series, 1);
  const minValue = 0;
  const span = maxValue - minValue || 1;

  ctx.strokeStyle = "rgba(255,255,255,0.08)";
  ctx.lineWidth = 1;
  for (let i = 0; i < 4; i += 1) {
    const y = padding + (height - padding * 2) * (i / 3);
    ctx.beginPath();
    ctx.moveTo(padding, y);
    ctx.lineTo(width - padding, y);
    ctx.stroke();
  }

  const stepX = series.length > 1 ? (width - padding * 2) / (series.length - 1) : 0;
  ctx.strokeStyle = color;
  ctx.lineWidth = 2;
  ctx.beginPath();
  series.forEach((value, idx) => {
    const x = padding + idx * stepX;
    const y = padding + (height - padding * 2) * (1 - (value - minValue) / span);
    if (idx === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();
};

const updateHeadline = (sample) => {
  headlineMetrics.innerHTML = "";
  const items = [
    { label: "CPU", value: `${sample.cpu.percent.toFixed(1)}%` },
    { label: "Memory", value: `${sample.memory.percent.toFixed(1)}%` },
    { label: "Disk", value: `${sample.disk.percent.toFixed(1)}%` },
    { label: "Net recv", value: formatBytes(sample.network.recv_rate) + "/s" },
  ];

  items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "metric-card";
    card.innerHTML = `<div class="metric-label">${item.label}</div><div class="metric-value">${item.value}</div>`;
    headlineMetrics.appendChild(card);
  });

  const topProcess = sample.processes?.[0]?.name || "-";
  headlineLog.textContent = `Top process: ${topProcess}`;
};

const updateGpu = (sample) => {
  if (!gpuMetrics) {
    return;
  }
  gpuMetrics.innerHTML = "";
  const gpu = sample.gpu || { available: false };
  if (!gpu.available) {
    gpuMetrics.innerHTML = "<div class=\"metric-card\">GPU unavailable</div>";
  } else {
    const gpuInfo = gpu.gpus?.[0] || {};
    const items = [
      { label: "GPU util", value: gpuInfo.utilization !== undefined ? `${gpuInfo.utilization}%` : "-" },
      { label: "GPU temp", value: gpuInfo.temperature !== undefined ? `${gpuInfo.temperature}°C` : "-" },
      { label: "GPU fan", value: gpuInfo.fan !== null && gpuInfo.fan !== undefined ? `${gpuInfo.fan}%` : "-" },
    ];
    items.forEach((item) => {
      const card = document.createElement("div");
      card.className = "metric-card";
      card.innerHTML = `<div class=\"metric-label\">${item.label}</div><div class=\"metric-value\">${item.value}</div>`;
      gpuMetrics.appendChild(card);
    });
  }
  const thermal = sample.thermal || { temperatures: [], fans: [] };
  const temp = thermal.temperatures?.[0];
  const fan = thermal.fans?.[0];
  if (temp || fan) {
    const tempText = temp ? `${temp.label}: ${temp.current}°C` : "";
    const fanText = fan ? `Fan ${fan.label}: ${fan.rpm} RPM` : "";
    thermalLog.textContent = [tempText, fanText].filter(Boolean).join(" | ");
  } else {
    thermalLog.textContent = "No thermal sensors detected.";
  }
};

const updateBattery = (summary) => {
  if (!batteryMetrics) {
    return;
  }
  batteryMetrics.innerHTML = "";
  const latest = summary.latest;
  const drain = summary.battery_drain;
  const percent = latest?.battery?.percent;
  const plugged = latest?.battery?.power_plugged;
  const items = [
    { label: "Battery", value: percent !== undefined ? `${percent}%` : "-" },
    { label: "Plugged", value: plugged !== undefined ? (plugged ? "Yes" : "No") : "-" },
    { label: "Drain/hr", value: drain ? `${drain.drain_per_hour}%` : "-" },
  ];
  items.forEach((item) => {
    const card = document.createElement("div");
    card.className = "metric-card";
    card.innerHTML = `<div class=\"metric-label\">${item.label}</div><div class=\"metric-value\">${item.value}</div>`;
    batteryMetrics.appendChild(card);
  });
};

const updateProcesses = (sample) => {
  const tbody = processTable.querySelector("tbody");
  tbody.innerHTML = "";
  (sample.processes || []).forEach((proc) => {
    const row = document.createElement("tr");
    row.dataset.pid = proc.pid;
    row.innerHTML = `
      <td>${proc.name}</td>
      <td>${proc.cpu.toFixed(1)}</td>
      <td>${formatBytes(proc.memory)}</td>
    `;
    tbody.appendChild(row);
  });
};

const updateAlerts = (alerts) => {
  alertList.innerHTML = "";
  if (!alerts.length) {
    const li = document.createElement("li");
    li.className = "alert-item";
    li.textContent = "No active alerts.";
    alertList.appendChild(li);
    return;
  }
  alerts.forEach((alert) => {
    const li = document.createElement("li");
    li.className = "alert-item";
    li.innerHTML = `
      <strong>${alert.category.toUpperCase()} - ${alert.message}</strong>
      <div>${alert.recommendation}</div>
    `;
    alertList.appendChild(li);
  });
};

const updateTimeline = (alerts) => {
  if (!timelineList) {
    return;
  }
  timelineList.innerHTML = "";
  if (!alerts.length) {
    const li = document.createElement("li");
    li.textContent = "No incidents recorded.";
    timelineList.appendChild(li);
    return;
  }
  alerts.forEach((alert) => {
    const li = document.createElement("li");
    li.textContent = `${alert.timestamp} | ${alert.category.toUpperCase()} | ${alert.message}`;
    timelineList.appendChild(li);
  });
};

const pushSeries = (arr, value) => {
  arr.push(value);
  if (arr.length > state.maxPoints) {
    arr.shift();
  }
};

const updateCharts = () => {
  drawSeries(cpuChart, state.cpu, "#4cc9f0");
  drawSeries(memChart, state.mem, "#f9c74f");
  drawSeries(diskChart, state.disk, "#f94144");
  drawSeries(netChart, state.net, "#4cc9f0");
};

const handleSample = (sample) => {
  pushSeries(state.cpu, sample.cpu.percent);
  pushSeries(state.mem, sample.memory.percent);
  pushSeries(state.disk, sample.disk.percent);
  pushSeries(state.net, sample.network.recv_rate / 1024);
  updateCharts();
  updateHeadline(sample);
  updateGpu(sample);
  updateProcesses(sample);
};

const loadSummary = async () => {
  try {
    const response = await fetch("/api/summary", { headers: authHeaders() });
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        setStatus("Auth required");
        return;
      }
      throw new Error("summary failed");
    }
    const data = await response.json();
    setStatus("Live");
    if (data.system) {
      deviceName.textContent = data.system.hostname || "-";
      deviceOs.textContent = data.system.os || "-";
      deviceCores.textContent = data.system.cores || "-";
    }
    if (data.latest) {
      handleSample({
        cpu: { percent: data.latest.cpu_percent },
        memory: { percent: data.latest.mem_percent },
        disk: { percent: data.latest.disk_percent },
        network: { recv_rate: data.latest.net_recv_rate },
        processes: data.latest.processes || [],
        gpu: data.latest.gpu || { available: false },
        thermal: data.latest.thermal || { temperatures: [], fans: [] },
      });
    }
    updateAlerts(data.alerts || []);
    updateBattery(data);
  } catch (err) {
    setStatus("Offline");
  }
};

const loadHistory = async () => {
  try {
    const response = await fetch("/api/metrics?limit=60", { headers: authHeaders() });
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        setStatus("Auth required");
      }
      return;
    }
    const data = await response.json();
    data.forEach((row) => {
      pushSeries(state.cpu, row.cpu_percent || 0);
      pushSeries(state.mem, row.mem_percent || 0);
      pushSeries(state.disk, row.disk_percent || 0);
      pushSeries(state.net, (row.net_recv_rate || 0) / 1024);
    });
    updateCharts();
  } catch (err) {
    // Ignore history errors
  }
};

const connectStream = () => {
  const stream = new EventSource(buildUrl("/api/stream"));
  stream.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    if (payload.sample) {
      handleSample(payload.sample);
    }
    if (payload.alerts) {
      updateAlerts(payload.alerts);
      loadTimeline();
    }
  };
  stream.onerror = () => {
    setStatus("Reconnecting...");
  };
};

const loadTimeline = async () => {
  try {
    const response = await fetch("/api/timeline?limit=30", { headers: authHeaders() });
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        setStatus("Auth required");
      }
      return;
    }
    const data = await response.json();
    updateTimeline(data);
  } catch (err) {
    // Ignore timeline errors
  }
};

const postAction = async (path, payload) => {
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    actionOutput.textContent = data.message || "Action completed.";
  } catch (err) {
    actionOutput.textContent = "Action failed.";
  }
};

if (saveTokenBtn) {
  saveTokenBtn.addEventListener("click", () => {
    setToken(authTokenInput.value.trim());
    setStatus("Token saved");
  });
}

if (killTopBtn) {
  killTopBtn.addEventListener("click", () => {
    const topRow = processTable.querySelector("tbody tr");
    if (!topRow) {
      actionOutput.textContent = "No process available.";
      return;
    }
    const pid = topRow.dataset.pid || "";
    if (!pid) {
      actionOutput.textContent = "PID unavailable.";
      return;
    }
    postAction("/api/actions/kill", { pid: Number(pid) });
  });
}

if (clearTempBtn) {
  clearTempBtn.addEventListener("click", () => {
    postAction("/api/actions/clear-temp", { max_age_hours: 24 });
  });
}

if (stopServiceBtn) {
  stopServiceBtn.addEventListener("click", () => {
    const name = serviceNameInput.value.trim();
    if (!name) {
      actionOutput.textContent = "Enter a service name.";
      return;
    }
    postAction("/api/actions/stop-service", { service: name });
  });
}

const downloadFile = async (path) => {
  const response = await fetch(path, { headers: authHeaders() });
  if (!response.ok) {
    actionOutput.textContent = "Download failed.";
    return;
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = path.split("/").pop();
  link.click();
  URL.revokeObjectURL(url);
};

if (exportMetricsBtn) {
  exportMetricsBtn.addEventListener("click", () => downloadFile("/api/exports/metrics.csv"));
}
if (exportAlertsBtn) {
  exportAlertsBtn.addEventListener("click", () => downloadFile("/api/exports/alerts.csv"));
}
if (exportReportBtn) {
  exportReportBtn.addEventListener("click", () => downloadFile("/api/exports/report.json"));
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/static/sw.js");
}

let deferredPrompt = null;
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  deferredPrompt = event;
  if (installBtn) {
    installBtn.hidden = false;
  }
});

if (installBtn) {
  installBtn.addEventListener("click", async () => {
    if (!deferredPrompt) {
      return;
    }
    deferredPrompt.prompt();
    await deferredPrompt.userChoice;
    deferredPrompt = null;
    installBtn.hidden = true;
  });
}

loadSummary();
loadHistory();
loadTimeline();
connectStream();
