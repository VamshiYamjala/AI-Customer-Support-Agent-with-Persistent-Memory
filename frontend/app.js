/**
 * frontend/app.js
 * Vanilla JavaScript controller for PayNest Support Chat UI with Hindsight Memory Inspector and Customer Authentication.
 */

document.addEventListener("DOMContentLoaded", async () => {
  const chatInput = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  const messagesContainer = document.getElementById("messages-container");
  const memoryToggle = document.getElementById("memory-toggle");
  const newSessionBtn = document.getElementById("new-session-btn");
  const memoryStatusChip = document.getElementById("memory-status-chip");
  const inspectorBody = document.getElementById("inspector-body");
  const tabBtns = document.querySelectorAll(".tab-btn");
  const customerSelect = document.getElementById("customer-select");
  const customerNameEl = document.getElementById("customer-name");
  const customerEmailEl = document.getElementById("customer-email");

  let currentCustomer = "priya";
  let authToken = null;
  let currentSessionId = `sess_${Date.now().toString(36)}`;
  let isSending = false;
  let lastUsedMemories = [];

  // Authenticate and obtain signed bearer token
  async function loginAsCustomer(customerId) {
    try {
      const resp = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customer_id: customerId }),
      });
      if (resp.ok) {
        const data = await resp.json();
        authToken = data.token;
        currentCustomer = data.customer.id;
        sessionStorage.setItem("paynest_auth_token", authToken);
        sessionStorage.setItem("paynest_customer_id", currentCustomer);

        if (customerNameEl) customerNameEl.textContent = data.customer.display_name;
        if (customerEmailEl) customerEmailEl.textContent = data.customer.email_masked;

        // Reset session on customer switch
        resetSession(`Logged in as ${data.customer.display_name}.`);
      }
    } catch (e) {
      console.error("Login failed:", e);
    }
  }

  function resetSession(welcomeMsg = "Started a new session. How can we help you today?") {
    currentSessionId = `sess_${Date.now().toString(36)}`;
    lastUsedMemories = [];
    messagesContainer.innerHTML = `
      <div class="message system">
        <p>${welcomeMsg}</p>
      </div>
    `;
    renderInspector("used");
  }

  // Customer dropdown change
  if (customerSelect) {
    customerSelect.addEventListener("change", (e) => {
      loginAsCustomer(e.target.value);
    });
  }

  // Tab switching (Used vs All)
  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      const tab = btn.dataset.tab;
      renderInspector(tab);
    });
  });

  function renderInspector(tab = "used") {
    if (tab === "used") {
      if (!lastUsedMemories || lastUsedMemories.length === 0) {
        inspectorBody.innerHTML = `
          <div class="inspector-empty">
            <p>No memories used in this reply.</p>
          </div>
        `;
        return;
      }

      inspectorBody.innerHTML = "";
      lastUsedMemories.forEach((mem, idx) => {
        const card = document.createElement("div");
        card.className = "memory-card";
        const typeClass = mem.type === "world" ? "badge-world" : (mem.type === "observation" ? "badge-obs" : "badge-exp");
        card.innerHTML = `
          <div class="memory-card-header">
            <span class="memory-tag">[M${idx + 1}]</span>
            <span class="badge ${typeClass}">${mem.type || "memory"}</span>
          </div>
          <div class="memory-card-text">${escapeHtml(mem.text)}</div>
        `;
        inspectorBody.appendChild(card);
      });
    } else {
      // Tab === 'all'
      inspectorBody.innerHTML = `
        <div class="inspector-empty">
          <p>Displaying persistent memory bank <code>cs-${currentCustomer}</code>.</p>
        </div>
      `;
      if (lastUsedMemories && lastUsedMemories.length > 0) {
        lastUsedMemories.forEach((mem) => {
          const card = document.createElement("div");
          card.className = "memory-card";
          card.innerHTML = `
            <div class="memory-card-header">
              <span class="badge badge-exp">${mem.type}</span>
            </div>
            <div class="memory-card-text">${escapeHtml(mem.text)}</div>
          `;
          inspectorBody.appendChild(card);
        });
      }
    }
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

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

    if (!authToken) {
      await loginAsCustomer(currentCustomer);
    }

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

    const useMemory = memoryToggle ? memoryToggle.checked : true;

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          message: text,
          session_id: currentSessionId,
          use_memory: useMemory,
        }),
      });

      hideTypingIndicator();

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errMsg = errorData.error?.message || errorData.detail || "The assistant is temporarily unavailable. Please try again.";
        appendMessage("system", `⚠️ ${errMsg}`);
        return;
      }

      const data = await response.json();
      appendMessage("assistant", data.reply);

      if (data.banner) {
        appendMessage("system", `ℹ️ ${data.banner}`);
      }

      // Update Inspector panel
      lastUsedMemories = data.memories_used || [];
      renderInspector("used");

      // Update chip
      if (memoryStatusChip) {
        if (data.memory_status === "active") {
          memoryStatusChip.textContent = "Memory: Saved ✓";
          memoryStatusChip.className = "status-chip ready";
        } else if (data.memory_status === "unavailable") {
          memoryStatusChip.textContent = "Memory: Unavailable";
          memoryStatusChip.className = "status-chip disabled";
        } else {
          memoryStatusChip.textContent = "Memory: OFF";
          memoryStatusChip.className = "status-chip disabled";
        }
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
      resetSession("Started a new session. How can we help you today?");
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

  // Initial login on page load
  await loginAsCustomer("priya");
});
