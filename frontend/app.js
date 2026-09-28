/**
 * frontend/app.js
 * Vanilla JavaScript controller for PayNest Support Chat UI with Hindsight Memory Inspector, Customer Authentication, and Resolution Outcomes.
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
        const isKB = mem.type === "world" || (mem.id && mem.id.startsWith("K")) || (mem.context && mem.context.includes("kb"));
        const typeClass = isKB ? "badge-world" : (mem.type === "observation" ? "badge-obs" : "badge-exp");
        const tagLabel = isKB ? (mem.id && mem.id.startsWith("K") ? `[${mem.id}]` : `[K${idx + 1}]`) : `[M${idx + 1}]`;
        const typeLabel = isKB ? "KB / Policy" : (mem.type || "experience");

        card.innerHTML = `
          <div class="memory-card-header">
            <span class="memory-tag">${tagLabel}</span>
            <span class="badge ${typeClass}">${typeLabel}</span>
          </div>
          <div class="memory-card-text">${escapeHtml(mem.text)}</div>
        `;
        inspectorBody.appendChild(card);
      });
    } else {
      // Tab === 'all': Fetch customer longitudinal history from /api/customer/history
      inspectorBody.innerHTML = `
        <div class="inspector-empty">
          <p>Loading history for bank <code>cs-${currentCustomer}</code>...</p>
        </div>
      `;

      fetch("/api/customer/history", {
        headers: { "Authorization": `Bearer ${authToken}` },
      })
        .then((res) => res.json())
        .then((history) => {
          if (!history || history.length === 0) {
            inspectorBody.innerHTML = `
              <div class="inspector-empty">
                <p>No past session history recorded yet for <code>cs-${currentCustomer}</code>.</p>
              </div>
            `;
            return;
          }

          inspectorBody.innerHTML = `
            <div style="font-size:0.8rem; font-weight:600; color:var(--text-muted); margin-bottom:0.75rem;">
              Memory Bank: <code>cs-${currentCustomer}</code> (${history.length} session${history.length > 1 ? "s" : ""})
            </div>
          `;

          history.forEach((item) => {
            const card = document.createElement("div");
            card.className = "memory-card";
            const topic = item.ticket ? item.ticket.topic : (item.session.title || item.session.id);
            const outcomeObj = item.outcomes && item.outcomes.length > 0 ? item.outcomes[0] : null;
            const outcomeBadge = outcomeObj
              ? `<div style="font-size:0.75rem; margin-top:0.35rem; color:${outcomeObj.outcome === 'resolved' ? '#15803d' : '#b91c1c'}; font-weight:600;">
                   Outcome: ${outcomeObj.outcome === 'resolved' ? '✓ Resolved' : '✕ Still broken'}
                 </div>`
              : "";

            card.innerHTML = `
              <div class="memory-card-header">
                <strong style="font-size:0.82rem; color:var(--text-main);">${escapeHtml(topic)}</strong>
                <span class="badge badge-obs">${escapeHtml(item.session.id.slice(0, 12))}</span>
              </div>
              <div class="memory-card-text" style="font-size:0.8rem; color:var(--text-muted);">
                ${item.messages ? item.messages.length : 0} interactions logged to SQLite & Hindsight.
              </div>
              ${outcomeBadge}
            `;
            inspectorBody.appendChild(card);
          });
        })
        .catch(() => {
          inspectorBody.innerHTML = `
            <div class="inspector-empty">
              <p>Persistent memory bank <code>cs-${currentCustomer}</code>.</p>
            </div>
          `;
        });
    }
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // Record customer resolution outcome
  async function sendOutcome(outcome, containerEl) {
    try {
      const resp = await fetch("/api/outcome", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          session_id: currentSessionId,
          outcome: outcome,
          note: outcome === "resolved" ? "Confirmed working by customer." : "Customer indicated issue is still broken.",
        }),
      });

      if (resp.ok) {
        const isResolved = outcome === "resolved";
        containerEl.innerHTML = `
          <span class="outcome-badge ${isResolved ? 'resolved' : 'broken'}">
            ${isResolved ? '✓ Outcome: Resolved (Saved to Memory)' : '⚠ Outcome: Still investigating (Logged to Memory)'}
          </span>
        `;
      }
    } catch (e) {
      console.error("Failed to record outcome:", e);
    }
  }

  // Append a message to the chat view
  function appendMessage(role, text, allowOutcome = false) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;

    const textP = document.createElement("p");
    textP.textContent = text;
    msgDiv.appendChild(textP);

    if (role === "assistant" && allowOutcome) {
      const outcomeDiv = document.createElement("div");
      outcomeDiv.className = "outcome-actions";
      outcomeDiv.innerHTML = `
        <span class="outcome-prompt">Did this resolve your issue?</span>
        <button class="btn-outcome resolved" title="Confirm fix worked">✓ That worked</button>
        <button class="btn-outcome broken" title="Fix did not work">✕ Still broken</button>
      `;

      const resolvedBtn = outcomeDiv.querySelector(".resolved");
      const brokenBtn = outcomeDiv.querySelector(".broken");

      resolvedBtn.addEventListener("click", () => sendOutcome("resolved", outcomeDiv));
      brokenBtn.addEventListener("click", () => sendOutcome("not_resolved", outcomeDiv));

      msgDiv.appendChild(outcomeDiv);
    }

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
      appendMessage("assistant", data.reply, true);

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
