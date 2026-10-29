"use strict";

const app = document.querySelector("#app");
const identityPanel = document.querySelector("#identity");
const timeoutMeta = document.querySelector('meta[name="api-timeout-ms"]');
const apiTimeoutMs = Number(timeoutMeta?.content) || 10000;
const state = {
  users: [],
  applications: [],
  requests: [],
  login: sessionStorage.getItem("demoLogin") || "ada.manager",
  screen: "requests",
  selectedRequestId: "",
  selectedReviewId: "",
  historyRequestId: "",
  detail: null,
  reviewDetail: null,
  history: [],
  pricing: null,
  applicationFilter: "",
  statusFilter: "",
  notice: null,
  revisionDraft: null,
  busy: false,
};

const labels = {
  relationship_manager: "Relationship manager",
  reviewer: "Reviewer",
};

const syntheticExamples = {
  competition: {
    discount_bps: 25,
    reason: "Synthetic example: a comparable competing offer is available for the same mortgage term.",
    context: {
      application: {
        purpose: "purchase", rate_type: "fixed", loan_amount: "250000.00",
        property_value: "320000.00", currency_code: "EUR", term_months: 300,
        standard_rate_bps: 425,
      },
      reason_category: "competitive_offer",
      competitor_offer: { rate_bps: 390, expires_on: "2027-01-31" },
    },
  },
  retention: {
    discount_bps: 20,
    reason: "Synthetic example: the manager is requesting a retention exception for an existing customer.",
    context: {
      application: {
        purpose: "remortgage", rate_type: "variable", loan_amount: "180000.00",
        property_value: "240000.00", currency_code: "EUR", term_months: 240,
        standard_rate_bps: 475,
      },
      reason_category: "retention",
    },
  },
  relationship: {
    discount_bps: 15,
    reason: "Synthetic example: a relationship pricing exception is requested for a product transfer.",
    context: {
      application: {
        purpose: "product_transfer", rate_type: "tracker", loan_amount: "210000.00",
        property_value: "300000.00", currency_code: "EUR", term_months: 300,
        standard_rate_bps: 445,
      },
      reason_category: "relationship",
    },
  },
};

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[char]);
}

function newId() {
  if (globalThis.crypto?.randomUUID) return crypto.randomUUID();
  return `ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

class ApiError extends Error {
  constructor(status, code, message, correlationId) {
    super(message);
    this.status = status;
    this.code = code;
    this.correlationId = correlationId;
  }
}

async function api(path, { method = "GET", body, login = state.login, idempotencyKey } = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), apiTimeoutMs);
  const headers = {
    "X-Demo-User": login,
    "X-Correlation-ID": newId(),
  };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
  try {
    const response = await fetch(path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
    const correlationId = response.headers.get("X-Correlation-ID");
    let payload;
    try {
      payload = await response.json();
    } catch {
      throw new ApiError(response.status, "invalid_response", "The API returned an invalid response.", correlationId);
    }
    if (!response.ok) {
      const envelope = payload?.error || {};
      throw new ApiError(
        response.status,
        envelope.code || "api_error",
        envelope.message || "The API request failed.",
        payload?.correlation_id || correlationId,
      );
    }
    return payload;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    const timedOut = error?.name === "AbortError";
    throw new ApiError(
      null,
      "backend_unavailable",
      timedOut ? "The API request timed out." : "The API is unavailable.",
      headers["X-Correlation-ID"],
    );
  } finally {
    clearTimeout(timeout);
  }
}

function roleSet(user = currentUser()) {
  return new Set(user?.roles || []);
}

function currentUser() {
  return state.users.find((user) => user.login === state.login);
}

function isManager(user = currentUser()) {
  return roleSet(user).has("relationship_manager");
}

function isReviewer(user = currentUser()) {
  return roleSet(user).has("reviewer");
}

function userName(login) {
  const user = state.users.find((item) => item.login === login);
  return user ? `${user.display_name} (${user.login})` : login;
}

function timestamp(value) {
  if (!value) return "—";
  return value.replace("T", " ").replace(/Z$/, " UTC").replace(/\+00:00$/, " UTC");
}

function getCreateIntent(login = state.login) {
  try {
    return JSON.parse(sessionStorage.getItem(`createIntent:${login}`) || "null");
  } catch {
    return null;
  }
}

function setCreateIntent(intent, login = state.login) {
  sessionStorage.setItem(`createIntent:${login}`, JSON.stringify(intent));
}

function clearCreateIntent(login = state.login) {
  sessionStorage.removeItem(`createIntent:${login}`);
}

function noticeHtml() {
  if (!state.notice) return "";
  const kind = state.notice.kind || "success";
  const details = state.notice.correlationId
    ? `<div class="error-details">Correlation ID: <code>${escapeHtml(state.notice.correlationId)}</code></div>`
    : "";
  const retry = state.notice.retry
    ? '<button class="button" data-action="retry-create">Retry submission</button>'
    : "";
  const refresh = state.notice.refresh
    ? '<button class="button" data-action="refresh-review">Refresh request</button>'
    : "";
  const reconnect = state.notice.reconnect
    ? '<button class="button" data-action="reconnect">Retry loading</button>'
    : "";
  return `<div class="notice ${kind}" role="status">${escapeHtml(state.notice.message)}${details}${retry}${refresh}${reconnect}</div>`;
}

function navHtml() {
  const tabs = ["requests", ...(isReviewer() ? ["review"] : []), "history"];
  return `<nav class="nav" aria-label="Main navigation">${tabs.map((tab) =>
    `<button type="button" class="${state.screen === tab ? "active" : ""}" data-screen="${tab}" aria-current="${state.screen === tab ? "page" : "false"}">${tab[0].toUpperCase()}${tab.slice(1)}</button>`
  ).join("")}</nav>`;
}

function aiHtml() {
  const enabled = sessionStorage.getItem("useAiAssistance") === "true";
  return `<section class="card ai-control" aria-label="AI assistance preference">
    <div><strong>Use AI assistance</strong><div class="help">This preference is local to this browser tab.</div></div>
    <label class="toggle"><input id="ai-toggle" type="checkbox" ${enabled ? "checked" : ""}> On</label>
    <button type="button" class="button" disabled title="AI assessment is unavailable until Phase 06">Generate assessment</button>
    <span class="help">Unavailable until Phase 06.</span>
  </section>`;
}

function identityHtml() {
  const user = currentUser();
  const roles = user?.roles.map((role) => labels[role] || role).join(", ") || "";
  identityPanel.innerHTML = `<label for="demo-user">Demo user</label>
    <select id="demo-user" aria-label="Demo user">${state.users.map((item) =>
      `<option value="${escapeHtml(item.login)}" ${item.login === state.login ? "selected" : ""}>${escapeHtml(item.display_name)} (${escapeHtml(item.login)})</option>`
    ).join("")}</select><span>${escapeHtml(roles)}</span>`;
}

function empty(message, title = "Nothing to show yet") {
  return `<div class="empty"><strong>${escapeHtml(title)}</strong>${escapeHtml(message)}</div>`;
}

function appFor(referenceOrId) {
  return state.applications.find((item) => item.id === referenceOrId || item.reference === referenceOrId);
}

function appOptions(applications, selected) {
  return applications.map((item) =>
    `<option value="${escapeHtml(item.id)}" ${item.id === selected ? "selected" : ""}>${escapeHtml(item.reference)}</option>`
  ).join("");
}

function requestOptions(requests, selected) {
  return requests.map((item) =>
    `<option value="${escapeHtml(item.request_id)}" ${item.request_id === selected ? "selected" : ""}>${escapeHtml(item.application_reference)} · ${escapeHtml(item.status)} · v${item.current_version_number}</option>`
  ).join("");
}

function contextFields(prefix, context) {
  const application = context?.application || {};
  const competitor = context?.competitor_offer || {};
  const option = (value, label, selected) => `<option value="${value}" ${value === selected ? "selected" : ""}>${label}</option>`;
  return `<fieldset class="context-fields"><legend>Application details for this version</legend>
    <p class="help">Structured context helps reviewers compare requests. Do not enter borrower-identifying data.</p>
    <div class="form-grid">
      <div class="field"><label for="${prefix}-purpose">Mortgage purpose</label>
        <select id="${prefix}-purpose" name="purpose" required>
          <option value="">Select purpose</option>
          ${option("purchase", "Purchase", application.purpose)}
          ${option("remortgage", "Remortgage", application.purpose)}
          ${option("product_transfer", "Product transfer", application.purpose)}
        </select></div>
      <div class="field"><label for="${prefix}-rate-type">Rate type</label>
        <select id="${prefix}-rate-type" name="rate_type" required>
          <option value="">Select rate type</option>
          ${option("fixed", "Fixed", application.rate_type)}
          ${option("variable", "Variable", application.rate_type)}
          ${option("tracker", "Tracker", application.rate_type)}
        </select></div>
      <div class="field"><label for="${prefix}-loan">Loan amount</label>
        <input id="${prefix}-loan" name="loan_amount" type="number" min="0.01" step="0.01" value="${escapeHtml(application.loan_amount ?? "")}" required></div>
      <div class="field"><label for="${prefix}-property">Property value</label>
        <input id="${prefix}-property" name="property_value" type="number" min="0.01" step="0.01" value="${escapeHtml(application.property_value ?? "")}" required></div>
      <div class="field"><label for="${prefix}-currency">Currency code</label>
        <input id="${prefix}-currency" name="currency_code" type="text" minlength="3" maxlength="3" pattern="[A-Z]{3}" value="${escapeHtml(application.currency_code ?? "EUR")}" required></div>
      <div class="field"><label for="${prefix}-term">Term (months)</label>
        <input id="${prefix}-term" name="term_months" type="number" min="1" step="1" value="${escapeHtml(application.term_months ?? "")}" required></div>
      <div class="field"><label for="${prefix}-standard-rate">Standard rate (bps)</label>
        <input id="${prefix}-standard-rate" name="standard_rate_bps" type="number" min="0" step="1" value="${escapeHtml(application.standard_rate_bps ?? "")}" required></div>
      <div class="field"><label for="${prefix}-category">Reason category</label>
        <select id="${prefix}-category" name="reason_category" required>
          <option value="">Select category</option>
          ${option("competitive_offer", "Competitive offer", context?.reason_category)}
          ${option("retention", "Retention", context?.reason_category)}
          ${option("relationship", "Relationship", context?.reason_category)}
          ${option("other", "Other", context?.reason_category)}
        </select></div>
    </div>
    <details class="optional-fields" id="${prefix}-competitor" ${competitor.rate_bps !== undefined ? "open" : ""}>
      <summary>Add manager-reported competitor offer (unverified)</summary>
      <div class="form-grid">
        <div class="field"><label for="${prefix}-competitor-rate">Competitor rate (bps)</label>
          <input id="${prefix}-competitor-rate" name="competitor_rate_bps" type="number" min="0" step="1" value="${escapeHtml(competitor.rate_bps ?? "")}"></div>
        <div class="field"><label for="${prefix}-competitor-expiry">Offer expiry (optional)</label>
          <input id="${prefix}-competitor-expiry" name="competitor_expires_on" type="date" value="${escapeHtml(competitor.expires_on ?? "")}"></div>
      </div>
    </details>
  </fieldset>`;
}

function contextSummary(context) {
  if (!context) return `<p class="help">No structured application context was recorded for this version.</p>`;
  const application = context.application;
  const toMinorUnits = (amount) => {
    const [whole, fraction = ""] = String(amount).split(".");
    return BigInt(whole) * 100n + BigInt((fraction + "00").slice(0, 2));
  };
  const loanMinor = toMinorUnits(application.loan_amount);
  const propertyMinor = toMinorUnits(application.property_value);
  const ltvTenths = (loanMinor * 1000n + propertyMinor / 2n) / propertyMinor;
  const ltv = `${ltvTenths / 10n}.${ltvTenths % 10n}`;
  const competitor = context.competitor_offer;
  return `<dt>Mortgage purpose</dt><dd>${escapeHtml(application.purpose.replaceAll("_", " "))}</dd>
    <dt>Product / rate</dt><dd>${escapeHtml(application.rate_type)}</dd>
    <dt>Loan amount</dt><dd>${escapeHtml(application.loan_amount)} ${escapeHtml(application.currency_code)}</dd>
    <dt>Property value</dt><dd>${escapeHtml(application.property_value)} ${escapeHtml(application.currency_code)}</dd>
    <dt>Loan-to-value (derived)</dt><dd>${escapeHtml(ltv)}%</dd>
    <dt>Term</dt><dd>${application.term_months} months</dd>
    <dt>Standard rate</dt><dd>${application.standard_rate_bps} bps</dd>
    <dt>Reason category</dt><dd>${escapeHtml(context.reason_category.replaceAll("_", " "))}</dd>
    ${competitor ? `<dt>Reported competitor offer</dt><dd>${competitor.rate_bps} bps${competitor.expires_on ? ` · expires ${escapeHtml(competitor.expires_on)}` : ""} · unverified</dd>` : ""}`;
}

function listRequests(rows, selectedId = "") {
  if (!rows.length) return empty("New submissions will appear here.", "No requests match these filters");
  return `<div class="request-list">${rows.map((row) => `
    <div class="request-row ${row.request_id === selectedId ? "selected" : ""}">
      <div><div class="request-reference">${escapeHtml(row.application_reference)}</div>
        <div class="request-meta">Version ${row.current_version_number}</div></div>
      <span class="badge ${escapeHtml(row.status)}">${escapeHtml(row.status)}</span>
      <button type="button" class="button" data-action="open-request" data-request="${escapeHtml(row.request_id)}">Open</button>
    </div>`).join("")}</div>`;
}

function detailFields(detail) {
  const version = detail.current_version;
  const decision = version.decision;
  return `<dl class="details">
    <dt>Application</dt><dd>${escapeHtml(detail.application_reference)}</dd>
    <dt>Version</dt><dd>${version.version_number}</dd>
    <dt>Status</dt><dd><span class="badge ${escapeHtml(version.status)}">${escapeHtml(version.status)}</span></dd>
    <dt>Requested discount</dt><dd>${version.discount_bps} bps</dd>
    <dt>Submitted by</dt><dd>${escapeHtml(version.submitted_by_login)}</dd>
    <dt>Submitted at</dt><dd>${escapeHtml(timestamp(version.submitted_at))}</dd>
    ${version.context ? contextSummary(version.context) : ""}
    <dt>Reason submitted</dt><dd>${escapeHtml(version.reason)}</dd>
    ${decision ? `<dt>Decision</dt><dd>${escapeHtml(decision.outcome)} by ${escapeHtml(decision.reviewer_login)}</dd>
      <dt>Decided at</dt><dd>${escapeHtml(timestamp(decision.decided_at))}</dd>` : ""}
  </dl>`;
}

function pricingHtml() {
  if (!state.detail || !state.pricing) return "";
  const pricing = state.pricing;
  const text = pricing.status === "approved"
    ? `${pricing.discount_bps} bps · version ${pricing.version_number} · request ${pricing.request_id}`
    : "No current approved discount.";
  return `<section class="card"><h3>Current approved pricing</h3><p>${escapeHtml(text)}</p></section>`;
}

function createIntentForm() {
  const ownedApps = state.applications.filter((item) => currentUser() && item.manager_id === currentUser().id);
  if (!ownedApps.length) return empty("No applications are assigned to this manager.");
  const intent = getCreateIntent();
  const draft = intent?.payload;
  const context = draft?.context;
  const selectedApp = ownedApps.some((item) => item.id === draft?.application_id)
    ? draft.application_id : ownedApps[0].id;
  return `<section class="card"><div class="card-header"><h2>Create request</h2></div>
    <form id="create-form">
      <div class="field"><label for="create-application">Application</label>
        <select id="create-application" name="application_id" required>${appOptions(ownedApps, selectedApp)}</select></div>
      <div class="field"><label for="create-discount">Discount (basis points)</label>
        <input id="create-discount" name="discount_bps" type="number" min="1" step="1" value="${escapeHtml(draft?.discount_bps ?? "")}" required></div>
      <div class="sample-controls"><label for="synthetic-example">Synthetic example</label>
        <div class="button-row"><select id="synthetic-example" name="synthetic_example">
          <option value="">Choose an example to prefill</option><option value="competition">Competitive offer</option>
          <option value="retention">Customer retention</option><option value="relationship">Relationship request</option>
        </select><button class="button" type="button" data-action="fill-synthetic">Fill form</button></div>
        <span class="help">Fills a clearly synthetic draft; no request is saved until you submit.</span></div>
      ${contextFields("create", context)}
      <div class="field"><label for="create-reason">Free-text reason (1–2,000 characters)</label>
        <textarea id="create-reason" name="reason" maxlength="2000" required>${escapeHtml(draft?.reason ?? "")}</textarea></div>
      <div class="button-row"><button class="button primary" type="submit" ${state.busy ? "disabled" : ""}>Submit request</button></div>
    </form>
  </section>`;
}

function revisionForm(detail) {
  const owner = appFor(detail.application_id)?.manager_id === currentUser()?.id;
  if (!owner || !["approved", "declined"].includes(detail.status)) return "";
  const version = detail.current_version;
  const draft = state.revisionDraft || {
    discount_bps: version.discount_bps,
    reason: version.reason,
    context: version.context,
  };
  return `<section class="card"><h3>Revise terms</h3>
    <p class="help">A revision creates a new pending version that needs fresh review.</p>
    <form id="revision-form" class="inline-form">
      <div class="field"><label for="revision-discount">New discount (basis points)</label>
        <input id="revision-discount" name="discount_bps" type="number" min="1" step="1" value="${escapeHtml(draft.discount_bps ?? "")}" required></div>
      ${contextFields("revision", draft.context)}
      <div class="field"><label for="revision-reason">Free-text reason for revised terms</label>
        <textarea id="revision-reason" name="reason" maxlength="2000" required>${escapeHtml(draft.reason ?? "")}</textarea></div>
      <button class="button primary" type="submit" ${state.busy ? "disabled" : ""}>Submit revision</button>
    </form>
  </section>`;
}

function renderRequests() {
  const rows = state.requests.filter((row) =>
    (!state.applicationFilter || row.application_id === state.applicationFilter)
    && (!state.statusFilter || row.status === state.statusFilter)
  );
  const selected = state.detail && rows.find((item) => item.request_id === state.detail.request_id);
  const applications = state.applications;
  return `<div class="page-heading"><div><h1>Requests</h1><p class="subtitle">Create and track pricing exception requests.</p></div></div>
    ${navHtml()}${noticeHtml()}${aiHtml()}
    <div class="layout"><div class="stack">
      ${isManager() ? createIntentForm() : ""}
      <section class="card"><div class="card-header"><h2>Request list</h2><button class="button" data-action="reload">Refresh</button></div>
        <div class="filters">
          <div class="field"><label for="application-filter">Application filter</label><select id="application-filter"><option value="">All applications</option>${appOptions(applications, state.applicationFilter)}</select></div>
          <div class="field"><label for="status-filter">Status filter</label><select id="status-filter"><option value="">All statuses</option>${["pending", "approved", "declined"].map((status) => `<option value="${status}" ${status === state.statusFilter ? "selected" : ""}>${status}</option>`).join("")}</select></div>
        </div>
        ${listRequests(rows, state.selectedRequestId)}
      </section>
    </div><div class="stack">
      <section class="card"><div class="card-header"><h2>Request details</h2></div>
        ${selected ? detailFields(state.detail) : empty("Select a request to review its exact terms and decision.", "No request selected")}
      </section>
      ${pricingHtml()}
      ${state.detail ? revisionForm(state.detail) : ""}
    </div></div>`;
}

function renderReview() {
  const pending = state.requests.filter((item) => item.status === "pending");
  const detail = state.reviewDetail;
  const own = detail?.current_version.submitted_by_login === state.login;
  const canDecide = detail?.status === "pending" && !own && isReviewer();
  return `<div class="page-heading"><div><h1>Review</h1><p class="subtitle">Decide the version shown below.</p></div></div>
    ${navHtml()}${noticeHtml()}${aiHtml()}
    <div class="layout"><section class="card"><div class="card-header"><h2>Pending requests</h2><button class="button" data-action="reload">Refresh</button></div>
      ${pending.length ? listRequests(pending, state.selectedReviewId) : empty("There are no pending requests to review.", "Review queue is clear")}
    </section><section class="card"><h2>Terms for review</h2>
      ${detail ? detailFields(detail) : empty("Open a pending request to review its current version.", "No request opened")}
      ${own ? '<div class="notice warning">You submitted this request and cannot review it.</div>' : ""}
      ${canDecide ? `<div class="button-row">
        <button class="button primary" data-action="decide" data-outcome="approved" ${state.busy ? "disabled" : ""}>Approve version ${detail.current_version.version_number}</button>
        <button class="button danger" data-action="decide" data-outcome="declined" ${state.busy ? "disabled" : ""}>Decline version ${detail.current_version.version_number}</button>
      </div>` : ""}
    </section></div>`;
}

function renderHistory() {
  const selected = state.requests.find((item) => item.request_id === state.historyRequestId);
  const events = state.history.map((event) => {
    const olderApproval = event.event_type === "approved" && event.version_number < (selected?.current_version_number || 0);
    const title = olderApproval ? "Earlier approval (historical)" : `${event.event_type[0].toUpperCase()}${event.event_type.slice(1)}`;
    const decision = event.version?.decision;
    return `<article class="history-event">
      <div class="history-title">${escapeHtml(title)} · version ${event.version_number}</div>
      <div class="history-meta">${escapeHtml(event.actor_login)} · ${escapeHtml(timestamp(event.occurred_at))}</div>
      <details><summary>View version ${event.version_number} terms · ${escapeHtml(event.event_type)}</summary>
        <p class="help">These are the associated version terms and final decision, not a status snapshot from the event time.</p>
        <dl class="details"><dt>Discount</dt><dd>${event.version.discount_bps} bps</dd>
          <dt>Reason</dt><dd>${escapeHtml(event.version.reason)}</dd>
          ${event.version.context ? contextSummary(event.version.context) : ""}
          <dt>Submitted by</dt><dd>${escapeHtml(event.version.submitted_by_login)}</dd>
          <dt>Submitted at</dt><dd>${escapeHtml(timestamp(event.version.submitted_at))}</dd>
          ${decision ? `<dt>Decision</dt><dd>${escapeHtml(decision.outcome)} by ${escapeHtml(decision.reviewer_login)} · ${escapeHtml(timestamp(decision.decided_at))}</dd>` : ""}
        </dl>
      </details>
    </article>`;
  }).join("");
  return `<div class="page-heading"><div><h1>History</h1><p class="subtitle">A chronological record of terms and decisions.</p></div></div>
    ${navHtml()}${noticeHtml()}${aiHtml()}
    <section class="card"><div class="field"><label for="history-request">Request history</label>
      <select id="history-request"><option value="">Select a request</option>${requestOptions(state.requests, state.historyRequestId)}</select></div>
      ${selected ? `<div class="history-list">${events || empty("No history events were returned.")}</div>` : empty("Select a request to inspect its events.", "No request selected")}
    </section>`;
}

function render() {
  identityHtml();
  const body = state.screen === "review" ? renderReview()
    : state.screen === "history" ? renderHistory() : renderRequests();
  app.innerHTML = body;
}

function setError(error, { refresh = false, retry = false, reconnect = false } = {}) {
  state.notice = {
    kind: "error",
    message: error.message || "The operation failed.",
    correlationId: error.correlationId,
    refresh,
    retry,
    reconnect,
  };
}

async function loadWorkspace() {
  state.notice = null;
  try {
    const [applications, requests] = await Promise.all([
      api("/demo/applications"),
      api("/requests"),
    ]);
    state.applications = applications;
    state.requests = requests;
    if (!requests.some((item) => item.request_id === state.selectedRequestId)) {
      state.selectedRequestId = "";
      state.detail = null;
      state.pricing = null;
    }
    if (!requests.some((item) => item.request_id === state.selectedReviewId)) {
      state.selectedReviewId = "";
      state.reviewDetail = null;
    }
    if (!requests.some((item) => item.request_id === state.historyRequestId)) {
      state.historyRequestId = "";
      state.history = [];
    }
    render();
  } catch (error) {
    setError(error, { reconnect: true });
    render();
  }
}

async function loadRequest(requestId, target = "detail") {
  state.notice = null;
  try {
    const detail = await api(`/requests/${encodeURIComponent(requestId)}`);
    if (target === "review") {
      state.selectedReviewId = requestId;
      state.reviewDetail = detail;
    } else {
      state.selectedRequestId = requestId;
      state.detail = detail;
      state.pricing = await api(`/applications/${encodeURIComponent(detail.application_id)}/approved-discount`);
    }
    render();
  } catch (error) {
    setError(error, { reconnect: true });
    render();
  }
}

async function loadHistory(requestId) {
  state.historyRequestId = requestId;
  state.history = [];
  state.notice = null;
  render();
  if (!requestId) return;
  try {
    state.history = await api(`/requests/${encodeURIComponent(requestId)}/history`);
  } catch (error) {
    setError(error, { reconnect: true });
  }
  render();
}

async function refreshAfterWrite(requestId, message, target = "detail") {
  await loadWorkspace();
  if (state.notice?.kind !== "error") await loadRequest(requestId, target);
  if (state.notice?.kind === "error") {
    state.notice.message = `${message} The change was saved, but the refreshed view failed: ${state.notice.message}`;
  } else {
    state.notice = { kind: "success", message };
  }
  render();
}

function readContext(form) {
  const data = new FormData(form);
  const expiryInput = form.elements.namedItem("competitor_expires_on");
  const competitorRate = String(data.get("competitor_rate_bps") || "");
  const competitorExpiry = String(data.get("competitor_expires_on") || "");
  expiryInput.setCustomValidity(competitorExpiry && !competitorRate
    ? "Enter the reported competitor rate when adding an expiry date."
    : "");
  if (!form.reportValidity()) return null;
  const context = {
    application: {
      purpose: String(data.get("purpose")),
      rate_type: String(data.get("rate_type")),
      loan_amount: String(data.get("loan_amount")),
      property_value: String(data.get("property_value")),
      currency_code: String(data.get("currency_code")),
      term_months: Number(data.get("term_months")),
      standard_rate_bps: Number(data.get("standard_rate_bps")),
    },
    reason_category: String(data.get("reason_category")),
  };
  if (competitorRate) {
    context.competitor_offer = {
      rate_bps: Number(competitorRate),
      ...(competitorExpiry ? { expires_on: competitorExpiry } : {}),
    };
  }
  return context;
}

function createPayload(form, context) {
  const data = new FormData(form);
  return {
    application_id: String(data.get("application_id")),
    discount_bps: Number(data.get("discount_bps")),
    reason: String(data.get("reason")),
    context,
  };
}

async function sendCreate(intent) {
  state.busy = true;
  state.notice = null;
  render();
  try {
    const result = await api("/requests", {
      method: "POST",
      body: intent.payload,
      idempotencyKey: intent.key,
    });
    clearCreateIntent();
    await refreshAfterWrite(
      result.request_id,
      `Submitted: ${result.request_id} · version ${result.version_number}${result.replayed ? " (retried safely)" : ""}.`,
    );
  } catch (error) {
    setError(error, { retry: true });
  } finally {
    state.busy = false;
    render();
  }
}

async function submitCreate(form) {
  const context = readContext(form);
  if (!context) return;
  const payload = createPayload(form, context);
  const existing = getCreateIntent();
  const intent = existing && JSON.stringify(existing.payload) === JSON.stringify(payload)
    ? existing : { key: newId(), payload };
  setCreateIntent(intent);
  await sendCreate(intent);
}

async function submitRevision(form) {
  const data = new FormData(form);
  const context = readContext(form);
  if (!context) return;
  const draft = {
    discount_bps: Number(data.get("discount_bps")),
    reason: String(data.get("reason")),
    context,
  };
  state.revisionDraft = draft;
  const openedVersion = state.detail.current_version.version_number;
  state.busy = true;
  state.notice = null;
  render();
  try {
    const result = await api(`/requests/${encodeURIComponent(state.detail.request_id)}/revisions`, {
      method: "POST",
      body: { expected_version: openedVersion, ...draft },
    });
    state.revisionDraft = null;
    await refreshAfterWrite(
      result.request_id,
      `Revision submitted as pending version ${result.version_number}; fresh review is required.`,
    );
  } catch (error) {
    setError(error, { refresh: error.code === "stale_version" });
  } finally {
    state.busy = false;
    render();
  }
}

async function decide(outcome) {
  if (!state.reviewDetail) return;
  const openedVersion = state.reviewDetail.current_version.version_number;
  state.busy = true;
  state.notice = null;
  render();
  try {
    const requestId = state.reviewDetail.request_id;
    await api(`/requests/${encodeURIComponent(requestId)}/decisions`, {
      method: "POST",
      body: { expected_version: openedVersion, outcome },
    });
    await refreshAfterWrite(
      state.selectedReviewId || requestId,
      `Version ${openedVersion} ${outcome}.`,
      "review",
    );
  } catch (error) {
    const stale = error.code === "stale_version";
    setError(error, { refresh: stale });
  } finally {
    state.busy = false;
    render();
  }
}

async function bootstrap() {
  try {
    state.users = await api("/demo/users", { login: "ada.manager" });
    if (!state.users.some((user) => user.login === state.login)) state.login = "ada.manager";
    sessionStorage.setItem("demoLogin", state.login);
    await loadWorkspace();
  } catch (error) {
    setError(error, { reconnect: true });
    render();
  }
}

identityPanel.addEventListener("change", async (event) => {
  if (event.target.id !== "demo-user") return;
  state.login = event.target.value;
  sessionStorage.setItem("demoLogin", state.login);
  state.screen = "requests";
  state.selectedRequestId = "";
  state.selectedReviewId = "";
  state.historyRequestId = "";
  state.detail = null;
  state.reviewDetail = null;
  state.history = [];
  state.pricing = null;
  await loadWorkspace();
});

app.addEventListener("change", async (event) => {
  const { id, value, checked } = event.target;
  if (id === "ai-toggle") {
    sessionStorage.setItem("useAiAssistance", String(checked));
    render();
  } else if (id === "application-filter") {
    state.applicationFilter = value;
    render();
  } else if (id === "status-filter") {
    state.statusFilter = value;
    render();
  } else if (id === "history-request") {
    await loadHistory(value);
  }
});

app.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (event.target.id === "create-form") await submitCreate(event.target);
  if (event.target.id === "revision-form") await submitRevision(event.target);
});

app.addEventListener("click", async (event) => {
  const button = event.target.closest("button");
  if (!button) return;
  if (button.dataset.screen) {
    state.screen = button.dataset.screen;
    state.notice = null;
    render();
  } else if (button.dataset.action === "open-request") {
    const target = state.screen === "review" ? "review" : "detail";
    await loadRequest(button.dataset.request, target);
  } else if (button.dataset.action === "decide") {
    await decide(button.dataset.outcome);
  } else if (button.dataset.action === "fill-synthetic") {
    const form = button.closest("form");
    const sample = syntheticExamples[form.elements.namedItem("synthetic_example").value];
    if (sample) {
      form.elements.namedItem("discount_bps").value = sample.discount_bps;
      form.elements.namedItem("reason").value = sample.reason;
      const context = sample.context;
      for (const [name, value] of Object.entries(context.application)) {
        form.elements.namedItem(name).value = value;
      }
      form.elements.namedItem("reason_category").value = context.reason_category;
      const offer = context.competitor_offer;
      const details = form.querySelector("details.optional-fields");
      details.open = Boolean(offer);
      form.elements.namedItem("competitor_rate_bps").value = offer?.rate_bps ?? "";
      form.elements.namedItem("competitor_expires_on").value = offer?.expires_on ?? "";
    }
  } else if (button.dataset.action === "retry-create") {
    const intent = getCreateIntent();
    if (intent) await sendCreate(intent);
  } else if (button.dataset.action === "refresh-review") {
    if (state.screen === "review" && state.selectedReviewId) {
      const requestId = state.selectedReviewId;
      await loadWorkspace();
      await loadRequest(requestId, "review");
    } else if (state.detail) {
      const requestId = state.detail.request_id;
      await loadWorkspace();
      await loadRequest(requestId);
    }
  } else if (button.dataset.action === "reload" || button.dataset.action === "reconnect") {
    await loadWorkspace();
    if (state.selectedRequestId) await loadRequest(state.selectedRequestId);
    if (state.selectedReviewId) await loadRequest(state.selectedReviewId, "review");
    if (state.historyRequestId) await loadHistory(state.historyRequestId);
  }
});

bootstrap();
