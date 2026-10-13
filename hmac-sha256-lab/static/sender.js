/*
 * sender.js -- logic for the Sender page.
 * Sends the key, message and receiver address to /api/send. The server
 * computes the HMAC and emails the message and MAC (never the key).
 */

const el = (id) => document.getElementById(id);

const ui = {
  receiverEmail: el("receiverEmail"),
  key: el("key"),
  message: el("message"),
  send: el("send"),
  randomKey: el("randomKey"),
  error: el("error"),
  sentPanel: el("sentPanel"),
  sentDetail: el("sentDetail"),
  macPanel: el("macPanel"),
  macValue: el("macValue"),
  copyMac: el("copyMac"),
  tracePanel: el("tracePanel"),
  traceList: el("traceList"),
  toggleTrace: el("toggleTrace"),
};

const groupHex = (hex) => hex.replace(/(.{8})/g, "$1 ").trim();

function showError(text) {
  ui.error.textContent = text;
  ui.error.hidden = false;
}

function clearOutput() {
  ui.error.hidden = true;
  ui.sentPanel.hidden = true;
  ui.macPanel.hidden = true;
  ui.tracePanel.hidden = true;
}

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

function renderMac(mac) {
  ui.macValue.textContent = groupHex(mac);
  ui.macPanel.hidden = false;
}

ui.send.addEventListener("click", async () => {
  clearOutput();
  ui.send.disabled = true;
  ui.send.textContent = "Sending…";

  try {
    const response = await fetch("/api/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        receiverEmail: ui.receiverEmail.value,
        key: ui.key.value,
        keyEncoding: "text",
        message: ui.message.value,
      }),
    });
    const data = await response.json();

    // The MAC is computed even when the email fails, so still show it.
    if (data.mac) renderMac(data.mac);
    if (data.steps) renderTrace(data.steps);

    if (!response.ok) {
      showError(data.error || "The request failed.");
    } else {
      ui.sentDetail.textContent =
        `Sent to ${data.sentTo}. Now give the receiver the key through a different channel.`;
      ui.sentPanel.hidden = false;
    }
  } catch {
    showError("Could not reach the server. Is it still running?");
  } finally {
    ui.send.disabled = false;
    ui.send.textContent = "Seal and send email";
  }
});

ui.randomKey.addEventListener("click", async () => {
  try {
    const response = await fetch("/api/random-key");
    ui.key.value = (await response.json()).key;
  } catch {
    showError("Could not reach the server to generate a key.");
  }
});

ui.copyMac.addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(ui.macValue.textContent.replace(/\s/g, ""));
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
