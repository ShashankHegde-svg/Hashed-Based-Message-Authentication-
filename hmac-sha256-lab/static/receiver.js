/*
 * receiver.js -- logic for the Receiver page.
 * Extracts the message and MAC from a pasted email, then asks the server to
 * verify them against the shared key the receiver typed in.
 */

const el = (id) => document.getElementById(id);

const ui = {
  key: el("key"),
  pasted: el("pasted"),
  message: el("message"),
  mac: el("mac"),
  extract: el("extract"),
  verify: el("verify"),
  error: el("error"),
  verdict: el("verdict"),
  verdictTitle: el("verdictTitle"),
  verdictReason: el("verdictReason"),
  verdictDetail: el("verdictDetail"),
};

const groupHex = (hex) => hex.replace(/(.{8})/g, "$1 ").trim();

function showError(text) {
  ui.error.textContent = text;
  ui.error.hidden = false;
}

function clearOutput() {
  ui.error.hidden = true;
  ui.verdict.hidden = true;
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

ui.extract.addEventListener("click", async () => {
  clearOutput();
  try {
    const data = await postJson("/api/parse-email", { body: ui.pasted.value });
    ui.message.value = data.message;
    ui.mac.value = data.mac;
  } catch (error) {
    showError(error.message);
  }
});

ui.verify.addEventListener("click", async () => {
  clearOutput();
  try {
    const data = await postJson("/api/verify", {
      key: ui.key.value,
      keyEncoding: "text",
      message: ui.message.value,
      messageEncoding: "text",
      mac: ui.mac.value,
    });

    ui.verdict.classList.toggle("is-valid", data.valid);
    ui.verdict.classList.toggle("is-invalid", !data.valid);
    ui.verdictTitle.textContent = data.valid ? "Authentic" : "Not authentic";
    ui.verdictReason.textContent = data.reason;

    ui.verdictDetail.innerHTML = "";
    if (!data.valid) {
      [
        ["MAC in the email", data.supplied],
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
  } catch (error) {
    showError(error.message);
  }
});
