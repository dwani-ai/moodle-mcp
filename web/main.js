const form = document.querySelector("#chatForm");
const messages = document.querySelector("#messages");
const messageInput = document.querySelector("#message");
const roleInput = document.querySelector("#role");
const userIdInput = document.querySelector("#userId");

function addMessage(kind, text) {
  const node = document.createElement("div");
  node.className = `message ${kind}`;
  node.textContent = text;
  messages.appendChild(node);
  messages.scrollTop = messages.scrollHeight;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  addMessage("user", message);
  messageInput.value = "";

  const payload = {
    message,
    role: roleInput.value,
    user_id: userIdInput.value ? Number(userIdInput.value) : null,
  };

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "Request failed");
    }
    addMessage("agent", data.answer || "Done.");
  } catch (error) {
    addMessage("error", error.message);
  }
});
