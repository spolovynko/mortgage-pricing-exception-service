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
  createApplicationId: "",
  statusFilter: "",
  requestSearch: "",
  applicationSearch: "",
  notice: null,
  revisionDraft: null,
  busy: false,
  aiEnabled: sessionStorage.getItem("aiEnabled") === "true",
  assessment: null,
};

const applicationFinancialFields = ["loan_amount", "property_value", "standard_rate_bps", "term_months"];

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
      if (state.reviewDetail?.request_id !== requestId
          || state.reviewDetail?.current_version.version_number !== detail.current_version.version_number) {
        state.assessment = null;
      }
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
  state.screen = target === "review" ? "review" : "requests";
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
    clearFormDraft("create");
    state.createApplicationId = "";
    state.screen = "requests";
    await refreshAfterWrite(
      result.request_id,
      `Request submitted for review · version ${result.version_number}${result.replayed ? " (existing submission recovered)" : ""}.`,
    );
  } catch (error) {
    setError(error, { retry: true });
  } finally {
    state.busy = false;
    render();
  }
}

async function submitCreate(form) {
  saveFormDraft(form);
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
  saveFormDraft(form);
  const context = readContext(form);
  if (!context) return;
  const draft = {
    discount_bps: Number(data.get("discount_bps")),
    reason: String(data.get("reason")),
    context,
  };
  state.revisionDraft = draft;
  const openedVersion = state.detail.current_version.version_number;
  const revisionReference = `${state.detail.request_id}:${openedVersion}`;
  state.busy = true;
  state.notice = null;
  render();
  try {
    const result = await api(`/requests/${encodeURIComponent(state.detail.request_id)}/revisions`, {
      method: "POST",
      body: { expected_version: openedVersion, ...draft },
    });
    state.revisionDraft = null;
    clearFormDraft("revision", revisionReference);
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

identityPanel.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-login]");
  if (!button || state.busy || button.dataset.login === state.login) return;
  if (!state.users.some((user) => user.login === button.dataset.login)) return;
  state.login = button.dataset.login;
  sessionStorage.setItem("demoLogin", state.login);
  state.screen = "requests";
  state.createApplicationId = "";
  state.selectedRequestId = "";
  state.selectedReviewId = "";
  state.historyRequestId = "";
  state.detail = null;
  state.reviewDetail = null;
  state.revisionDraft = null;
  state.history = [];
  state.pricing = null;
  await loadWorkspace();
  render({ focusHeading: true });
});

app.addEventListener("input", (event) => {
  const form = event.target.form;
  if (form && ["create-form", "revision-form"].includes(form.id)) {
    saveFormDraft(form);
    if (form.id === "create-form") updateComposerPreview(form);
  } else if (event.target.id === "request-search") {
    state.requestSearch = event.target.value;
    render();
  } else if (event.target.id === "application-search") {
    state.applicationSearch = event.target.value;
    render();
  }
});

app.addEventListener("change", async (event) => {
  const { id, value } = event.target;
  const form = event.target.form;
  if (form && ["create-form", "revision-form"].includes(form.id)) saveFormDraft(form);
  if (id === "create-application") {
    state.createApplicationId = value;
    const application = appFor(value);
    for (const field of applicationFinancialFields) form.elements.namedItem(field).value = application?.[field] ?? "";
    saveFormDraft(form);
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
  if (state.busy) return;
  if (event.target.id === "create-form") await submitCreate(event.target);
  if (event.target.id === "revision-form") await submitRevision(event.target);
});

async function handleWorkspaceClick(event) {
  const button = event.target.closest("button");
  if (!button || state.busy) return;
  if (button.dataset.screen) {
    state.screen = button.dataset.screen;
    state.notice = null;
    render({ focusHeading: true });
  } else if (button.dataset.action === "new-request") {
    const application = appFor(button.dataset.application);
    if (!application || application.manager_id !== currentUser()?.id) return;
    const draft = getFormDraft("create") || {};
    draft.application_id = application.id;
    for (const field of applicationFinancialFields) draft[field] = String(application[field] ?? "");
    sessionStorage.setItem(formDraftKey("create"), JSON.stringify(draft));
    state.screen = "create";
    state.notice = null;
    render({ focusHeading: true });
  } else if (button.dataset.action === "open-request") {
    const target = state.screen === "review" ? "review" : "detail";
    state.screen = target === "review" ? "review" : "requests";
    await loadRequest(button.dataset.request, target);
  } else if (button.dataset.action === "close-detail") {
    state.detail = null;
    state.pricing = null;
    state.selectedRequestId = "";
    render({ focusHeading: true });
  } else if (button.dataset.action === "view-history") {
    state.screen = "history";
    await loadHistory(button.dataset.request);
    render({ focusHeading: true });
  } else if (button.dataset.action === "discard-create") {
    clearFormDraft("create");
    clearCreateIntent();
    state.createApplicationId = "";
    state.notice = { kind: "success", message: "Draft discarded. Saved requests are unchanged." };
    render({ focusHeading: true });
  } else if (button.dataset.action === "ai-toggle") {
    state.aiEnabled = !state.aiEnabled;
    state.assessment = null;
    sessionStorage.setItem("aiEnabled", String(state.aiEnabled));
    render();
  } else if (button.dataset.action === "generate-assessment") {
    if (!state.aiEnabled || !state.reviewDetail) return;
    state.busy = true;
    state.assessment = null;
    render();
    try {
      state.assessment = await api(`/requests/${state.reviewDetail.request_id}/assessments`, {
        method: "POST", body: { expected_version: state.reviewDetail.current_version.version_number },
      });
    } catch (error) {
      state.notice = { kind: "error", message: error instanceof ApiError && error.code === "ai_disabled"
        ? "Optional AI assistance is not enabled on this service. Continue the human review."
        : "AI assistance is unavailable. Continue the human review." };
    } finally {
      state.busy = false;
      render();
    }
  } else if (button.dataset.action === "decide") {
    await decide(button.dataset.outcome);
  } else if (button.dataset.action === "fill-synthetic") {
    const form = button.closest("form");
    const sample = syntheticExamples[form.elements.namedItem("synthetic_example").value];
    if (sample) {
      form.elements.namedItem("discount_bps").value = sample.discount_bps;
      form.elements.namedItem("reason").value = sample.reason;
      const application = appFor(form.elements.namedItem("application_id").value);
      for (const [name, value] of Object.entries(sample.context.application)) {
        form.elements.namedItem(name).value = applicationFinancialFields.includes(name) ? application?.[name] ?? value : value;
      }
      form.elements.namedItem("reason_category").value = sample.context.reason_category;
      const offer = sample.context.competitor_offer;
      form.querySelector("details.optional-fields").open = Boolean(offer);
      form.elements.namedItem("competitor_rate_bps").value = offer?.rate_bps ?? "";
      form.elements.namedItem("competitor_expires_on").value = offer?.expires_on ?? "";
      saveFormDraft(form);
      updateComposerPreview(form);
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
}

app.addEventListener("click", handleWorkspaceClick);
document.querySelector("#navigation").addEventListener("click", handleWorkspaceClick);

bootstrap();
