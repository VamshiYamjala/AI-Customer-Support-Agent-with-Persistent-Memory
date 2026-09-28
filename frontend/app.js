/**
 * frontend/app.js
 * Vanilla JavaScript controller for PayNest Support Chat UI.
 */

document.addEventListener("DOMContentLoaded", () => {
  const chatInput = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  const messagesContainer = document.getElementById("messages-container");
  const memoryToggle = document.getElementById("memory-toggle");
  const newSessionBtn = document.getElementById("new-session-btn");
  const memoryStatusChip = document.getElementById("memory-status-chip");
  const inspectorBody = document.getElementById("inspector-body");

  let currentSessionId = `sess_${Date.now().toString(36)}`;
  let isSending = false;

  // Append a message to the chat view
  function appendMessage(role, text) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;

    const textP = document.createElement("p");
    textP.textContent = text;
    msgDiv.appendChild(textP);

    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return msgDiv;
  }

  // Append typing indicator
  function showTypingIndicator() {
    const indicatorDiv = document.createElement("div");
    indicatorDiv.id = "typing-indicator";
    indicatorDiv.className = "message assistant typing";
    indicatorDiv.innerHTML = "<em>PayNest Support is typing...</em>";
    messagesContainer.appendChild(indicatorDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function hideTypingIndicator() {
    const indicator = document.getElementById("typing-indicator");
    if (indicator) {
      indicator.remove();
    }
  }

  // Send message to POST /api/chat
  async function sendMessage() {
    const text = chatInput.value.trim();
    if (!text || isSending) return;

    // Check message length
    if (text.length > 2000) {
      alert("Message is too long (maximum 2,000 characters).");
      return;
    }

    // UI Updates
    appendMessage("user", text);
    chatInput.value = "";
    isSending = true;
    sendBtn.disabled = true;
    chatInput.disabled = true;
    showTypingIndicator();

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: text,
          session_id: currentSessionId,
          use_memory: memoryToggle ? memoryToggle.checked : false,
        }),
      });

      hideTypingIndicator();

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errMsg = errorData.error?.message || "The assistant is temporarily unavailable. Please try again.";
        appendMessage("system", `⚠️ ${errMsg}`);
        return;
      }

      const data = await response.json();
      appendMessage("assistant", data.reply);

      // Update Inspector panel
      if (data.memories_used && data.memories_used.length > 0) {
        inspectorBody.innerHTML = "";
        data.memories_used.forEach((mem) => {
          const card = document.createElement("div");
          card.className = "memory-card";
          card.innerHTML = `<strong>[${mem.id || "Fact"}]</strong> ${mem.text}`;
          inspectorBody.appendChild(card);
        });
      } else {
        inspectorBody.innerHTML = `
          <div class="inspector-empty">
            <p>No memories used in this reply (Memory ${data.memory_status.toUpperCase()}).</p>
          </div>
        `;
      }

      if (data.session_id) {
        currentSessionId = data.session_id;
      }

    } catch (err) {
      hideTypingIndicator();
      appendMessage("system", "⚠️ Network connection error. Please check your connection and try again.");
    } finally {
      isSending = false;
      sendBtn.disabled = false;
      chatInput.disabled = false;
      chatInput.focus();
    }
  }

  // Event Listeners
  sendBtn.addEventListener("click", sendMessage);

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  if (newSessionBtn) {
    newSessionBtn.addEventListener("click", () => {
      currentSessionId = `sess_${Date.now().toString(36)}`;
      messagesContainer.innerHTML = `
        <div class="message system">
          <p>Started a new session. How can we help you today?</p>
        </div>
      `;
      inspectorBody.innerHTML = `
        <div class="inspector-empty">
          <p>No memories recalled yet. Send a message to inspect persistent memory retrieval.</p>
        </div>
      `;
    });
  }

  if (memoryToggle) {
    memoryToggle.addEventListener("change", () => {
      const isChecked = memoryToggle.checked;
      const label = memoryToggle.parentElement.querySelector(".label-text");
      if (label) {
        label.textContent = isChecked ? "Memory ON" : "Memory OFF";
      }
      if (memoryStatusChip) {
        memoryStatusChip.textContent = isChecked ? "Memory: Ready" : "Memory: OFF";
        memoryStatusChip.className = isChecked ? "status-chip ready" : "status-chip disabled";
      }
    });
  }
});
