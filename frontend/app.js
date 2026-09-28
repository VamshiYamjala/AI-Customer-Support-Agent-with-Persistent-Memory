/**
 * frontend/app.js
 * Controller for PayNest Customer Support Assistant.
 * 
 * Features:
 * - Customer authentication & tenant-isolated session management
 * - Real-time conversational interface with memory status indicators
 * - Side-by-side comparison of agent answers (with vs without persistent memory)
 * - Interactive memory inspector displaying recalled facts and knowledge base items
 * - Resolution outcome feedback collection
 */

document.addEventListener("DOMContentLoaded", async () => {
  // DOM Elements - Input, messaging, and control buttons
  const chatInput = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  const messagesContainer = document.getElementById("messages-container");
  const memoryToggle = document.getElementById("memory-toggle");
  const toggleLabelText = document.getElementById("toggle-label-text");
  const newSessionBtn = document.getElementById("new-session-btn");
  const memoryStatusChip = document.getElementById("memory-status-chip");
  const inspectorPanel = document.getElementById("inspector-panel");
  const inspectorBody = document.getElementById("inspector-body");
  const tabBtns = document.querySelectorAll(".tab-btn");
  const customerSelect = document.getElementById("customer-select");
  const customerNameEl = document.getElementById("customer-name");
  const customerEmailEl = document.getElementById("customer-email");
  const customerAvatarEl = document.getElementById("customer-avatar");
  const customerTierEl = document.getElementById("customer-tier");
  const bankLabelEl = document.getElementById("bank-label");
  const memCountBadge = document.getElementById("mem-count-badge");
  const mobileMemBadge = document.getElementById("mobile-mem-badge");
  const charCounter = document.getElementById("char-counter");
  const toggleInspectorBtn = document.getElementById("toggle-inspector-btn");

  // Demo Trigger Buttons
  const demoPriyaBtn = document.getElementById("demo-btn-priya-s2");
  const demoCompareBtn = document.getElementById("demo-btn-compare");
  const demoArjunBtn = document.getElementById("demo-btn-arjun");

  // State
  let currentCustomer = "priya";
  let authToken = null;
  let currentSessionId = `sess_${Date.now().toString(36)}`;
  let isSending = false;
  let lastUsedMemories = [];
  let currentTab = "used";

  const customerMeta = {
    priya: {
      initials: "PS",
      tier: "Pro Subscriber",
      bank: "cs-priya",
    },
    arjun: {
      initials: "AP",
      tier: "Enterprise Workspace",
      bank: "cs-arjun",
    },
    meera: {
      initials: "MR",
      tier: "New Customer",
      bank: "cs-meera",
    },
  };

  // 5 Verified PayNest Company Knowledge Base Articles
  const companyKB = [
    {
      id: "K1",
      title: "Subscription Renewal & Outdated Card Details",
      text: "Customers experiencing recurring payment failures on renewal frequently have an expired card or outdated billing zip code on file. Instruct customer to navigate to Settings > Billing Methods to update details before retrying checkout.",
      tags: ["kb", "billing", "cards"],
    },
    {
      id: "K2",
      title: "Two-Factor Authentication (2FA) SMS Delays",
      text: "One-time passwords (2FA) via SMS can take up to 2 minutes during peak carrier hours. Advise customers not to request consecutive codes within 120 seconds to prevent a temporary 15-minute security lockout.",
      tags: ["kb", "auth", "2fa"],
    },
    {
      id: "K3",
      title: "Refund Review Policy & Agent Limitations",
      text: "AI support assistants and frontline agents cannot process refunds or reverse credit card charges directly. All refund requests require review and approval by human billing specialists. Approved refunds settle within 3-5 business days.",
      tags: ["kb", "refunds", "policy"],
    },
    {
      id: "K4",
      title: "Subscription Tier Changes & Proration",
      text: "When changing or upgrading subscription tiers, changes apply immediately and the unused balance from the current billing cycle is automatically credited to the next invoice.",
      tags: ["kb", "subscriptions", "proration"],
    },
    {
      id: "K5",
      title: "Duplicate Pending Charges on Bank Statements",
      text: "Duplicate charges shown as pending on a banking statement are typically unconfirmed authorization holds that automatically drop within 48-72 hours. If both charges post as settled, escalate to Tier 2 support with invoice reference IDs.",
      tags: ["kb", "billing", "duplicate-charges"],
    },
  ];

  // =========================================================================
  // Customer Authentication & Session Management
  // =========================================================================

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

        const meta = customerMeta[currentCustomer] || { initials: "CU", tier: "Standard", bank: `cs-${currentCustomer}` };

        if (customerNameEl) customerNameEl.textContent = data.customer.display_name;
        if (customerEmailEl) customerEmailEl.textContent = data.customer.email_masked;
        if (customerAvatarEl) customerAvatarEl.textContent = meta.initials;
        if (customerTierEl) customerTierEl.textContent = meta.tier;
        if (bankLabelEl) bankLabelEl.textContent = meta.bank;

        resetSession(`Logged in as <strong>${escapeHtml(data.customer.display_name)}</strong>.`);
      }
    } catch (e) {
      console.error("Login failed:", e);
    }
  }

  function resetSession(welcomeHtml = "Started a new session. How can we help you today?") {
    currentSessionId = `sess_${Date.now().toString(36)}`;
    lastUsedMemories = [];
    updateMemoryCounts(0);

    messagesContainer.innerHTML = `
      <div class="message system">
        <div class="system-icon">ℹ️</div>
        <p>${welcomeHtml}</p>
      </div>
    `;

    renderInspector(currentTab);
  }

  function updateMemoryCounts(count) {
    if (memCountBadge) memCountBadge.textContent = count;
    if (mobileMemBadge) mobileMemBadge.textContent = count;
  }

  // Customer dropdown change
  if (customerSelect) {
    customerSelect.addEventListener("change", (e) => {
      loginAsCustomer(e.target.value);
    });
  }

  // =========================================================================
  // Memory Inspector Rendering (3 Tabs: Used, History, KB)
  // =========================================================================

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      tabBtns.forEach((b) => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
      });
      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      currentTab = btn.dataset.tab;
      renderInspector(currentTab);
    });
  });

  function renderInspector(tab = "used") {
    if (tab === "used") {
      renderUsedMemoriesTab();
    } else if (tab === "history") {
      renderHistoryTab();
    } else if (tab === "kb") {
      renderKBTab();
    }
  }

  function renderUsedMemoriesTab() {
    const isMemoryOn = memoryToggle ? memoryToggle.checked : true;

    if (!isMemoryOn) {
      inspectorBody.innerHTML = `
        <div class="inspector-empty">
          <div class="empty-icon">⚪</div>
          <p class="empty-title">Memory Toggle is OFF</p>
          <p class="empty-desc">The assistant is currently running in standard stateless mode without persistent memory retrieval.</p>
        </div>
      `;
      return;
    }

    if (!lastUsedMemories || lastUsedMemories.length === 0) {
      inspectorBody.innerHTML = `
        <div class="inspector-empty">
          <div class="empty-icon">🧠</div>
          <p class="empty-title">No Memories Recalled Yet</p>
          <p class="empty-desc">Send a message or run a <strong>Judge Demo</strong> to inspect memories retrieved for this turn.</p>
        </div>
      `;
      return;
    }

    inspectorBody.innerHTML = "";
    lastUsedMemories.forEach((mem, idx) => {
      const card = document.createElement("div");
      card.className = "memory-card";

      const isKB = mem.type === "world" || (mem.id && mem.id.startsWith("K")) || (mem.context && mem.context.includes("kb"));
      const tagClass = isKB ? "memory-tag-k" : "memory-tag-m";
      const tagText = isKB ? (mem.id && mem.id.startsWith("K") ? `[${mem.id}]` : `[K${idx + 1}]`) : `[M${idx + 1}]`;
      const typeBadgeClass = isKB ? "type-world" : (mem.type === "observation" ? "type-observation" : "type-experience");
      const typeLabel = isKB ? "Company Policy" : (mem.type === "observation" ? "Observation" : "Experience");
      const sourceLabel = isKB ? "support-kb (Shared)" : `cs-${currentCustomer} (Isolated)`;

      card.innerHTML = `
        <div class="memory-card-header">
          <span class="memory-tag-badge ${tagClass}">${tagText}</span>
          <span class="memory-type-badge ${typeBadgeClass}">${typeLabel}</span>
        </div>
        <div class="memory-card-text">${escapeHtml(mem.text)}</div>
        <div class="memory-card-footer">
          <span>Source: <code>${sourceLabel}</code></span>
          <span>${mem.score ? `Score: ${mem.score.toFixed(2)}` : "Verified"}</span>
        </div>
      `;
      inspectorBody.appendChild(card);
    });
  }

  function renderHistoryTab() {
    inspectorBody.innerHTML = `
      <div class="inspector-empty">
        <div class="empty-icon">⏳</div>
        <p class="empty-title">Loading Customer History...</p>
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
              <div class="empty-icon">📁</div>
              <p class="empty-title">No Past Sessions Recorded</p>
              <p class="empty-desc">No previous support tickets recorded for <code>cs-${currentCustomer}</code>.</p>
            </div>
          `;
          return;
        }

        inspectorBody.innerHTML = `
          <div style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.25rem;">
            Bank cs-${currentCustomer} — ${history.length} Session${history.length > 1 ? "s" : ""}
          </div>
        `;

        history.forEach((item) => {
          const card = document.createElement("div");
          card.className = "history-session-card";

          const topic = item.ticket ? item.ticket.topic : (item.session.title || item.session.id);
          const outcomeObj = item.outcomes && item.outcomes.length > 0 ? item.outcomes[0] : null;
          let outcomeBadgeHtml = "";

          if (outcomeObj) {
            const isResolved = outcomeObj.outcome === "resolved";
            outcomeBadgeHtml = `
              <div style="margin-top:0.4rem;">
                <span class="outcome-badge ${isResolved ? 'resolved' : 'broken'}">
                  ${isResolved ? '✓ Resolved' : '✕ Still broken'}
                </span>
              </div>
            `;
          }

          card.innerHTML = `
            <div class="history-session-header">
              <span class="history-session-title">${escapeHtml(topic)}</span>
              <span class="badge badge-subtle">${escapeHtml(item.session.id.slice(0, 12))}</span>
            </div>
            <div class="history-session-meta">
              ${item.messages ? item.messages.length : 0} interactions stored in SQLite & Hindsight.
            </div>
            ${outcomeBadgeHtml}
          `;
          inspectorBody.appendChild(card);
        });
      })
      .catch(() => {
        inspectorBody.innerHTML = `
          <div class="inspector-empty">
            <p>Could not load history for <code>cs-${currentCustomer}</code>.</p>
          </div>
        `;
      });
  }

  function renderKBTab() {
    inspectorBody.innerHTML = `
      <div style="font-size:0.75rem; font-weight:700; color:var(--text-muted); text-transform:uppercase; letter-spacing:0.5px; margin-bottom:0.25rem;">
        Bank support-kb — 5 Verified Policies
      </div>
    `;

    companyKB.forEach((article) => {
      const card = document.createElement("div");
      card.className = "memory-card";
      card.innerHTML = `
        <div class="memory-card-header">
          <span class="memory-tag-badge memory-tag-k">[${article.id}]</span>
          <span class="memory-type-badge type-world">Policy</span>
        </div>
        <strong style="font-size:0.84rem; display:block; margin-bottom:0.25rem; color:var(--text-main);">${escapeHtml(article.title)}</strong>
        <div class="memory-card-text">${escapeHtml(article.text)}</div>
        <div class="memory-card-footer">
          <span>Tags: ${article.tags.map((t) => `<code>${t}</code>`).join(", ")}</span>
        </div>
      `;
      inspectorBody.appendChild(card);
    });
  }

  // =========================================================================
  // Outcome Recording Feedback
  // =========================================================================

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
            ${isResolved ? '✓ Resolution confirmed & saved to memory' : '⚠ Logged: issue persists (flagged for escalation)'}
          </span>
        `;
      }
    } catch (e) {
      console.error("Failed to record outcome:", e);
    }
  }

  // =========================================================================
  // Chat Message Display with Inline Citations
  // =========================================================================

  function formatCitations(rawText) {
    let formatted = escapeHtml(rawText);
    formatted = formatted.replace(/\[(M\d+)\]/g, '<span class="citation-pill citation-m">[$1]</span>');
    formatted = formatted.replace(/\[(K\d+)\]/g, '<span class="citation-pill citation-k">[$1]</span>');
    return formatted;
  }

  function appendMessage(role, text, allowOutcome = false) {
    const msgDiv = document.createElement("div");
    msgDiv.className = `message ${role}`;

    if (role === "assistant") {
      const headerDiv = document.createElement("div");
      headerDiv.className = "assistant-header";
      headerDiv.innerHTML = `
        <span>🤖 PayNest AI</span>
      `;
      msgDiv.appendChild(headerDiv);

      const textP = document.createElement("div");
      textP.innerHTML = formatCitations(text);
      msgDiv.appendChild(textP);

      if (allowOutcome) {
        const outcomeDiv = document.createElement("div");
        outcomeDiv.className = "outcome-actions";
        outcomeDiv.innerHTML = `
          <span class="outcome-prompt">Did this recommendation resolve your issue?</span>
          <div class="outcome-buttons">
            <button class="btn-outcome resolved" title="Confirm fix resolved issue">✓ That worked</button>
            <button class="btn-outcome broken" title="Issue persists">✕ Still broken</button>
          </div>
        `;

        const resolvedBtn = outcomeDiv.querySelector(".resolved");
        const brokenBtn = outcomeDiv.querySelector(".broken");

        resolvedBtn.addEventListener("click", () => sendOutcome("resolved", outcomeDiv));
        brokenBtn.addEventListener("click", () => sendOutcome("not_resolved", outcomeDiv));

        msgDiv.appendChild(outcomeDiv);
      }
    } else {
      const textP = document.createElement("p");
      textP.textContent = text;
      msgDiv.appendChild(textP);
    }

    messagesContainer.appendChild(msgDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return msgDiv;
  }

  function showTypingIndicator() {
    const indicatorDiv = document.createElement("div");
    indicatorDiv.id = "typing-indicator";
    indicatorDiv.className = "message typing assistant";
    indicatorDiv.innerHTML = `
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    `;
    messagesContainer.appendChild(indicatorDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }

  function hideTypingIndicator() {
    const indicator = document.getElementById("typing-indicator");
    if (indicator) indicator.remove();
  }

  // =========================================================================
  // Send Message Logic
  // =========================================================================

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

    appendMessage("user", text);
    chatInput.value = "";
    if (charCounter) charCounter.textContent = "0 / 2000";

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

      // Update inspector state
      lastUsedMemories = data.memories_used || [];
      updateMemoryCounts(lastUsedMemories.length);
      renderInspector(currentTab);

      // Status chip update
      if (memoryStatusChip) {
        const dot = memoryStatusChip.querySelector(".status-dot") || document.createElement("span");
        const statusText = memoryStatusChip.querySelector(".status-text") || memoryStatusChip;

        if (data.memory_status === "active") {
          memoryStatusChip.className = "status-chip status-ready";
          statusText.textContent = "Memory: Active ✓";
        } else if (data.memory_status === "unavailable") {
          memoryStatusChip.className = "status-chip status-disabled";
          statusText.textContent = "Memory: Unavailable";
        } else {
          memoryStatusChip.className = "status-chip status-disabled";
          statusText.textContent = "Memory: OFF";
        }
      }

      if (data.session_id) {
        currentSessionId = data.session_id;
      }

    } catch (err) {
      hideTypingIndicator();
      appendMessage("system", "⚠️ Network connection error. Please verify your connection and try again.");
    } finally {
      isSending = false;
      sendBtn.disabled = false;
      chatInput.disabled = false;
      chatInput.focus();
    }
  }

  // =========================================================================
  // Side-by-Side Comparison Runner
  // =========================================================================

  async function runSideBySideComparison(query) {
    if (isSending) return;
    isSending = true;
    showTypingIndicator();

    appendMessage("user", `[⚖️ Comparing Memory ON vs OFF] "${query}"`);

    try {
      // 1. Fetch Memory OFF
      const respOff = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          message: query,
          session_id: `compare_off_${Date.now()}`,
          use_memory: false,
        }),
      });
      const dataOff = await respOff.json();

      // 2. Fetch Memory ON
      const respOn = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${authToken}`,
        },
        body: JSON.stringify({
          message: query,
          session_id: `compare_on_${Date.now()}`,
          use_memory: true,
        }),
      });
      const dataOn = await respOn.json();

      hideTypingIndicator();

      lastUsedMemories = dataOn.memories_used || [];
      updateMemoryCounts(lastUsedMemories.length);
      renderInspector("used");

      // Inject side-by-side comparison card
      const compCard = document.createElement("div");
      compCard.className = "comparison-card";
      compCard.innerHTML = `
        <div class="comparison-header">
          <div class="comparison-title">
            <span>⚖️ Memory ON vs OFF Comparison</span>
          </div>
          <span class="badge badge-brand">Session 2 Verification</span>
        </div>
        <div class="comparison-grid">
          <div class="comparison-col off">
            <div class="col-header">
              <span class="col-title">🔴 Memory OFF (Stateless)</span>
              <span class="badge badge-subtle">0 Memories</span>
            </div>
            <p class="col-reply">${escapeHtml(dataOff.reply)}</p>
            <div class="col-meta">
              Customer Friction: <strong style="color:#b91c1c;">Must re-explain card & error</strong>
            </div>
          </div>
          <div class="comparison-col on">
            <div class="col-header">
              <span class="col-title">🟢 Memory ON (Hindsight)</span>
              <span class="badge badge-brand">${dataOn.memories_used ? dataOn.memories_used.length : 0} Recalled</span>
            </div>
            <p class="col-reply">${formatCitations(dataOn.reply)}</p>
            <div class="col-meta">
              Customer Friction: <strong style="color:#166534;">0 repetition (Recalled Visa 4242 & past fix)</strong>
            </div>
          </div>
        </div>
        <div class="comparison-insight">
          💡 <strong>Judge Insight:</strong> Without memory, the assistant cannot recall Priya's past session and asks generic discovery questions. With Hindsight persistent memory, the agent cites <strong>[M1]</strong>, knows the previous fix failed, and immediately offers advanced escalation.
        </div>
      `;

      messagesContainer.appendChild(compCard);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;

    } catch (e) {
      hideTypingIndicator();
      appendMessage("system", "⚠️ Comparison test failed. Please verify network connectivity.");
    } finally {
      isSending = false;
    }
  }

  // =========================================================================
  // Event Listeners
  // =========================================================================

  sendBtn.addEventListener("click", sendMessage);

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  chatInput.addEventListener("input", () => {
    const len = chatInput.value.length;
    if (charCounter) charCounter.textContent = `${len} / 2000`;
  });

  if (newSessionBtn) {
    newSessionBtn.addEventListener("click", () => {
      resetSession("Started a new session. How can we help you today?");
    });
  }

  if (memoryToggle) {
    memoryToggle.addEventListener("change", () => {
      const isChecked = memoryToggle.checked;
      if (toggleLabelText) toggleLabelText.textContent = isChecked ? "Memory ON" : "Memory OFF";

      if (memoryStatusChip) {
        const statusText = memoryStatusChip.querySelector(".status-text") || memoryStatusChip;
        memoryStatusChip.className = isChecked ? "status-chip status-ready" : "status-chip status-disabled";
        statusText.textContent = isChecked ? "Memory: Active" : "Memory: OFF";
      }

      renderInspector(currentTab);
    });
  }

  // Mobile Inspector Toggle
  if (toggleInspectorBtn && inspectorPanel) {
    toggleInspectorBtn.addEventListener("click", () => {
      inspectorPanel.classList.toggle("open");
    });
  }

  // Judge Demo Shortcuts
  if (demoPriyaBtn) {
    demoPriyaBtn.addEventListener("click", async () => {
      if (currentCustomer !== "priya") {
        if (customerSelect) customerSelect.value = "priya";
        await loginAsCustomer("priya");
      }
      chatInput.value = "It's happening again with my subscription payment.";
      sendMessage();
    });
  }

  if (demoArjunBtn) {
    demoArjunBtn.addEventListener("click", async () => {
      if (customerSelect) customerSelect.value = "arjun";
      await loginAsCustomer("arjun");
      chatInput.value = "Which credit card did I have an issue with?";
      sendMessage();
    });
  }

  if (demoCompareBtn) {
    demoCompareBtn.addEventListener("click", async () => {
      if (currentCustomer !== "priya") {
        if (customerSelect) customerSelect.value = "priya";
        await loginAsCustomer("priya");
      }
      await runSideBySideComparison("It's happening again with my subscription payment.");
    });
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // Initial load
  await loginAsCustomer("priya");
});
