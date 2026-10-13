/*
 * app.js -- frontend logic.
 * Collects the key, message and (in verify mode) the MAC, sends them to the
 * Flask backend, and renders the result. No cryptography happens here; the
 * browser only displays what the server computed.
 */

const el = (id) => document.getElementById(id);

const ui = {
  tabs: document.querySelectorAll(".tab"),
  key: el("key"),
  message: el("message"),
  mac: el("mac"),
  macField: el("macField"),
  run: el("run"),
  randomKey: el("randomKey"),
  error: el("error"),
  empty: el("emptyState"),
  macPanel: el("macPanel"),
  macHeading: el("macHeading"),
  macValue: el("macValue"),
  macMeta: el("macMeta"),
  copyMac: el("copyMac"),
  verdict: el("verdict"),
  verdictTitle: el("verdictTitle"),
  verdictReason: el("verdictReason"),
  verdictDetail: el("verdictDetail"),
  tracePanel: el("tracePanel"),
  traceList: el("traceList"),
  toggleTrace: el("toggleTrace"),
};

let mode = "generate";

/* ---------- helpers ---------- */

const encodingOf = (name) =>
  document.querySelector(`input[name="${name}"]:checked`).value;

function showError(text) {
  ui.error.textContent = text;
  ui.error.hidden = false;
}

function clearOutput() {
  ui.error.hidden = true;
  ui.macPanel.hidden = true;
  ui.verdict.hidden = true;
  ui.tracePanel.hidden = true;
  ui.empty.hidden = false;
}

/* Break a long hex string into 8-character groups so it can be read aloud
   or compared by eye without losing your place. */
function groupHex(hex) {
  return hex.replace(/(.{8})/g, "$1 ").trim();
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "The request failed.");
  return data;
}

/* ---------- mode switching ---------- */

ui.tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    mode = tab.dataset.mode;
    ui.tabs.forEach((t) => {
      const active = t === tab;
      t.classList.toggle("is-active", active);
      t.setAttribute("aria-selected", String(active));
    });
    ui.macField.hidden = mode !== "verify";
    ui.run.textContent = mode === "verify" ? "Check the MAC" : "Seal the message";
    clearOutput();
  });
});

/* ---------- rendering ---------- */

function renderTrace(steps) {
  ui.traceList.innerHTML = "";
  steps.forEach((step) => {
    const item = document.createElement("li");

    const title = document.createElement("h3");
    title.textContent = step.label;

    const detail = document.createElement("p");
    detail.className = "detail";
    detail.textContent = step.detail;

    const value = document.createElement("code");
    value.className = "value";
    value.textContent = groupHex(step.value);

    item.append(title, detail, value);
    ui.traceList.append(item);
  });
  ui.tracePanel.hidden = false;
}

function renderGenerate(data) {
  ui.macHeading.textContent = "Message authentication code";
  ui.macValue.textContent = groupHex(data.mac);
  ui.macMeta.textContent =
    `256 bits, shown as 64 hex characters. Key: ${data.keyBytes} bytes. ` +
    `Message: ${data.messageBytes} bytes. Send this alongside the message; ` +
    `never send the key.`;
  ui.macPanel.hidden = false;
  renderTrace(data.steps);
  ui.empty.hidden = true;
}

function renderVerify(data) {
  ui.verdict.classList.toggle("is-valid", data.valid);
  ui.verdict.classList.toggle("is-invalid", !data.valid);
  ui.verdictTitle.textContent = data.valid ? "Authentic" : "Not authentic";
  ui.verdictReason.textContent = data.reason;

  ui.verdictDetail.innerHTML = "";
  if (!data.valid) {
    [
      ["MAC you supplied", data.supplied],
      ["MAC recomputed from this message and key", data.expected],
    ].forEach(([label, value]) => {
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = groupHex(value);
      ui.verdictDetail.append(dt, dd);
    });
  }

  ui.verdict.hidden = false;
  ui.empty.hidden = true;
}

/* ---------- actions ---------- */

ui.run.addEventListener("click", async () => {
  clearOutput();
  const payload = {
    key: ui.key.value,
    message: ui.message.value,
    keyEncoding: encodingOf("keyEncoding"),
    messageEncoding: encodingOf("messageEncoding"),
  };

  try {
    if (mode === "generate") {
      renderGenerate(await postJson("/api/generate", payload));
    } else {
      payload.mac = ui.mac.value;
      renderVerify(await postJson("/api/verify", payload));
    }
  } catch (error) {
    showError(error.message);
  }
});

ui.randomKey.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/random-key");
    const data = await response.json();
    ui.key.value = data.key;
    document.querySelector('input[name="keyEncoding"][value="hex"]').checked = true;
  } catch {
    showError("Could not reach the server to generate a key. Is app.py still running?");
  }
});

ui.copyMac.addEventListener("click", async () => {
  const hex = ui.macValue.textContent.replace(/\s/g, "");
  try {
    await navigator.clipboard.writeText(hex);
    ui.copyMac.textContent = "Copied";
    setTimeout(() => (ui.copyMac.textContent = "Copy"), 1500);
  } catch {
    showError("Copying is blocked in this browser. Select the MAC and copy it manually.");
  }
});

ui.toggleTrace.addEventListener("click", () => {
  const open = ui.toggleTrace.getAttribute("aria-expanded") === "true";
  ui.traceList.hidden = open;
  ui.toggleTrace.setAttribute("aria-expanded", String(!open));
  ui.toggleTrace.textContent = open ? "Show" : "Hide";
});

/* Ctrl/Cmd + Enter runs the current action from anywhere in the form. */
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") ui.run.click();
});
