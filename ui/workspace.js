"use strict";

const draftFields = ["application_id", "discount_bps", "reason", "purpose", "rate_type", "loan_amount", "property_value", "currency_code", "term_months", "standard_rate_bps", "reason_category", "competitor_rate_bps", "competitor_expires_on", "synthetic_example"];

function icon(name, size = 18) {
  const paths = {
    requests: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    applications: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    create: '<path d="M12 5v14M5 12h14"/>',
    review: '<path d="M12 3l8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6"/>',
    history: '<path d="M3 11a9 9 0 1 1 3 8M3 4v7h7M12 7v5l3 2"/>',
    approved: '<path d="M5 12l4 4L19 6"/>',
    declined: '<path d="M6 6l12 12M6 18L18 6"/>',
    pending: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    arrow: '<path d="M5 12h14M14 7l5 5-5 5"/>',
  };
  return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.requests}</svg>`;
}

function formDraftKey(kind, reference = "new", login = state.login) {
  return `formDraft:${login}:${kind}:${reference}`;
}

function getFormDraft(kind, reference = "new") {
  try {
    const value = JSON.parse(sessionStorage.getItem(formDraftKey(kind, reference)) || "null");
    if (!value || typeof value !== "object" || Array.isArray(value)) return null;
    return Object.fromEntries(draftFields.filter((name) => typeof value[name] === "string").map((name) => [name, value[name]]));
  } catch { return null; }
}

function saveFormDraft(form) {
  const values = {};
  for (const name of draftFields) {
    const control = form.elements.namedItem(name);
    if (control) values[name] = String(control.value);
  }
  const kind = form.id === "revision-form" ? "revision" : "create";
  sessionStorage.setItem(formDraftKey(kind, form.dataset.reference || "new"), JSON.stringify(values));
  return values;
}

function clearFormDraft(kind, reference = "new") {
  sessionStorage.removeItem(formDraftKey(kind, reference));
}

function draftContext(base, raw, application) {
  const context = {
    application: {
      ...Object.fromEntries(applicationFinancialFields.map((field) => [field, application?.[field]])),
      ...base?.application,
    },
    reason_category: base?.reason_category || "",
    competitor_offer: base?.competitor_offer,
  };
  if (!raw) return context;
  for (const field of ["purpose", "rate_type", "loan_amount", "property_value", "currency_code", "term_months", "standard_rate_bps"]) {
    if (Object.hasOwn(raw, field)) context.application[field] = raw[field];
  }
  if (Object.hasOwn(raw, "reason_category")) context.reason_category = raw.reason_category;
  if (Object.hasOwn(raw, "competitor_rate_bps")) {
    context.competitor_offer = raw.competitor_rate_bps || raw.competitor_expires_on
      ? { rate_bps: raw.competitor_rate_bps, expires_on: raw.competitor_expires_on || undefined } : undefined;
  }
  return context;
}

function money(value, currency = "EUR") {
  if (value === null || value === undefined || value === "" || !Number.isFinite(Number(value))) return "—";
  try { return new Intl.NumberFormat("en-BE", { style: "currency", currency, maximumFractionDigits: 2, minimumFractionDigits: 0 }).format(Number(value)); }
  catch { return String(value); }
}

function rate(value) {
  return value === null || value === undefined || value === "" || !Number.isFinite(Number(value)) ? "—" : `${(Number(value) / 100).toFixed(2)}%`;
}

function term(value) {
  if (!value) return "—";
  const years = Math.floor(Number(value) / 12), months = Number(value) % 12;
  return `${years ? `${years} yr` : ""}${months ? ` ${months} mo` : ""}`.trim();
}

function statusBadge(status) {
  const safe = ["pending", "approved", "declined"].includes(status) ? status : "unknown";
  return `<span class="badge ${safe}">${safe}</span>`;
}

function pageHeading(title, subtitle, actions = "") {
  return `<div class="page-heading"><div><div class="eyebrow">Mortgage workspace</div><h1 id="main-heading" tabindex="-1">${escapeHtml(title)}</h1><p class="subtitle">${escapeHtml(subtitle)}</p></div>${actions}</div>`;
}

function navHtml() {
  const tabs = [["requests", "Requests"], ["applications", "Applications"], ...(isManager() ? [["create", "New request"]] : []), ...(isReviewer() ? [["review", "Review queue"]] : []), ["history", "History"]];
  const pending = state.requests.filter((row) => row.status === "pending").length;
  return tabs.map(([screen, label]) => `<button type="button" class="${state.screen === screen ? "active" : ""}" data-screen="${screen}" aria-label="${label}" aria-current="${state.screen === screen ? "page" : "false"}" ${state.busy ? "disabled" : ""}>${icon(screen)}<span class="nav-label">${label}</span>${screen === "review" && pending ? `<span class="nav-count">${pending}</span>` : ""}</button>`).join("");
}

function identityHtml() {
  identityPanel.innerHTML = `<span class="identity-label">Demo user</span><div class="identity-tabs" role="group" aria-label="Demo user">${state.users.map((item) => {
    const role = item.roles.includes("relationship_manager") ? "Manager" : item.roles.includes("reviewer") ? "Reviewer" : item.display_name;
    return `<button type="button" class="identity-tab ${item.login === state.login ? "active" : ""}" data-login="${escapeHtml(item.login)}" aria-pressed="${item.login === state.login}" ${state.busy ? "disabled" : ""}>${escapeHtml(role)}</button>`;
  }).join("")}</div>`;
}

function empty(message, title = "Nothing to show yet") {
  return `<div class="empty">${icon("requests", 32)}<strong>${escapeHtml(title)}</strong>${escapeHtml(message)}</div>`;
}

function statsHtml() {
  return `<div class="stats">${[["All requests", "requests", state.requests.length], ["Awaiting review", "pending", state.requests.filter((row) => row.status === "pending").length], ["Approved", "approved", state.requests.filter((row) => row.status === "approved").length], ["Declined", "declined", state.requests.filter((row) => row.status === "declined").length]].map(([label, style, count]) => `<div class="stat"><div><span class="stat-label">${label}</span><strong class="stat-value">${count}</strong></div><span class="stat-icon ${style}">${icon(style)}</span></div>`).join("")}</div>`;
}

function listRequests(rows, selectedId = "") {
  return `<div class="request-list">${rows.map((row) => `<article class="request-row ${row.request_id === selectedId ? "selected" : ""}"><div class="request-row-top">${statusBadge(row.status)}<span class="version-tag">v${row.current_version_number}</span></div><span class="reference">${escapeHtml(row.application_reference)}</span><div class="button-row"><button type="button" class="button small" data-action="open-request" data-request="${escapeHtml(row.request_id)}">Review terms ${icon("arrow", 13)}</button></div></article>`).join("")}</div>`;
}

function detailFields(detail) {
  const version = detail.current_version, decision = version.decision;
  const baseline = version.context?.application.standard_rate_bps;
  return `<div class="card-header">${statusBadge(version.status)}<span class="version-tag">Version ${version.version_number}</span></div><div class="detail-reference">${escapeHtml(detail.application_reference)}</div>
    <div class="discount-hero"><span>Requested discount</span><strong>${version.discount_bps}<span style="font-size:16px;letter-spacing:0"> bps</span></strong><div class="rate-flow"><span>Standard rate<b>${rate(baseline)}</b></span><span>Requested rate<b>${baseline === undefined ? "—" : rate(baseline - version.discount_bps)}</b></span></div></div>
    <h3>Manager’s justification</h3><div class="reason-box">${escapeHtml(version.reason)}</div><dl class="details"><dt>Submitted by</dt><dd>${escapeHtml(userName(version.submitted_by_login))}</dd><dt>Submitted</dt><dd>${escapeHtml(timestamp(version.submitted_at))}</dd></dl>
    ${version.context ? `<hr class="section-divider"><h3>Submitted application details</h3><dl class="details">${contextSummary(version.context)}</dl>` : '<p class="help">No application context was recorded on this version.</p>'}
    ${decision ? `<hr class="section-divider"><dl class="details"><dt>Decision</dt><dd>${statusBadge(decision.outcome)}</dd><dt>Reviewed by</dt><dd>${escapeHtml(userName(decision.reviewer_login))}</dd><dt>Decided</dt><dd>${escapeHtml(timestamp(decision.decided_at))}</dd></dl>` : '<p class="help">These exact submitted terms await a human decision.</p>'}`;
}

function pricingHtml() {
  if (!state.detail || !state.pricing) return "";
  const pricing = state.pricing;
  return `<section class="card"><h3>Current approved discount</h3><p class="${pricing.status === "approved" ? "reference" : "help"}">${pricing.status === "approved" ? `${pricing.discount_bps} bps · version ${pricing.version_number}` : "No current approved discount is available."}</p></section>`;
}

function creationSelection() {
  const intent = getCreateIntent(), raw = getFormDraft("create");
  const applications = state.applications.filter((item) => item.manager_id === currentUser()?.id);
  const available = applications.filter((item) => !state.requests.some((row) => row.application_id === item.id) || intent?.payload?.application_id === item.id);
  const selectedId = raw?.application_id || state.createApplicationId || intent?.payload?.application_id;
  const selected = applications.find((item) => item.id === selectedId) || available[0];
  const existingRequest = intent?.payload?.application_id === selected?.id ? null : state.requests.find((row) => row.application_id === selected?.id);
  return { applications, selected, existingRequest, raw, intent };
}

function createIntentForm() {
  const { applications, selected, existingRequest, raw, intent } = creationSelection();
  if (!selected) return `<section class="card">${empty("Each application already has a request. Open an existing request to inspect or revise its terms.", "No applications awaiting a request")}<button class="button" data-screen="requests">View requests</button></section>`;
  const pending = intent?.payload?.application_id === selected.id ? intent.payload : null;
  const context = draftContext(pending?.context, raw?.application_id === selected.id ? raw : null, selected);
  return `<form id="create-form" data-reference="new"><section class="card form-section"><div class="card-header"><div><div class="eyebrow">01 · Application</div><h2>Application and loan details</h2></div><span class="version-tag">New submission</span></div>
    <div class="field"><label for="create-application">Application</label><select id="create-application" name="application_id" required>${appOptions(applications, selected.id)}</select></div>${existingRequest ? `<div class="notice warning">This application already has a request. Choose another application, or open the existing request to revise its terms.<br><button class="button small" type="button" data-action="open-request" data-request="${escapeHtml(existingRequest.request_id)}">View existing request</button></div>` : ""}<p class="help">Saved financial details are prefilled below. Check the terms you want to submit.</p>${contextFields("create", context)}</section>
    <section class="card form-section"><div class="eyebrow">02 · Request</div><h2>Propose a discount</h2><p class="help">A reviewer will decide on these exact submitted terms.</p><div class="field"><label for="create-discount">Discount (basis points)</label><input id="create-discount" name="discount_bps" type="number" min="1" step="1" placeholder="e.g. 25" value="${escapeHtml(raw?.discount_bps ?? pending?.discount_bps ?? "")}" required><span class="help">25 basis points = 0.25 percentage points.</span></div><div class="field"><label for="create-reason">Reason for the discount</label><textarea id="create-reason" name="reason" maxlength="2000" placeholder="Explain the commercial reason and the supporting information…" required>${escapeHtml(raw?.reason ?? pending?.reason ?? "")}</textarea><span class="help">Up to 2,000 characters. Do not include borrower-identifying information.</span></div>
    <details class="sample-controls"><summary>Use a synthetic example</summary><div class="button-row"><label class="sr-only" for="synthetic-example">Synthetic example</label><select id="synthetic-example" name="synthetic_example"><option value="">Choose an example</option>${[["competition", "Competitive offer"], ["retention", "Customer retention"], ["relationship", "Relationship request"]].map(([value, label]) => `<option value="${value}" ${raw?.synthetic_example === value ? "selected" : ""}>${label}</option>`).join("")}</select><button class="button" type="button" data-action="fill-synthetic">Fill form</button></div><p class="help">Fills a fictional rationale without submitting or replacing saved application financials.</p></details>
    <div class="button-row spread"><button class="button quiet" type="button" data-action="discard-create">Discard draft</button><button class="button primary" type="submit" ${state.busy || existingRequest ? "disabled" : ""}>${state.busy ? "Submitting…" : "Submit for review"}${icon("arrow", 15)}</button></div><p class="help">Your draft stays in this browser tab until submitted or discarded.</p></section></form>`;
}

function renderCreate() {
  if (!isManager()) return pageHeading("New request", "Only the application’s manager can submit a request.");
  const { selected, raw, intent } = creationSelection();
  const context = draftContext(intent?.payload?.context, raw, selected);
  const discount = raw?.discount_bps ?? intent?.payload?.discount_bps ?? "";
  return `${pageHeading("New discount request", "Start with an application, then explain the change you are requesting.", '<button class="button" data-screen="requests">Back to requests</button>')}
    <div class="composer-layout">${createIntentForm()}${selected ? `<aside class="stack composer-aside"><section class="card"><div class="eyebrow">Saved application</div><h3>${escapeHtml(selected.reference)}</h3><div class="financial-summary"><div><span>Loan amount</span><strong>${money(selected.loan_amount)}</strong></div><div><span>Property value</span><strong>${money(selected.property_value)}</strong></div><div><span>Standard rate</span><strong>${rate(selected.standard_rate_bps)}</strong></div><div><span>Term</span><strong>${term(selected.term_months)}</strong></div></div></section><section class="card"><div class="eyebrow">Request preview</div><div class="discount-hero"><span>Requested discount</span><strong id="preview-discount">${discount === "" ? "—" : `${escapeHtml(discount)} bps`}</strong><div class="rate-flow"><span>Requested rate<b id="preview-rate">${discount === "" ? "—" : rate(Number(context.application.standard_rate_bps) - Number(discount))}</b></span></div></div><p class="help">A preview of the requested terms. Approval remains a human decision.</p></section></aside>` : ""}</div>`;
}

function updateComposerPreview(form) {
  const discount = form.elements.namedItem("discount_bps")?.value || "";
  const baseline = form.elements.namedItem("standard_rate_bps")?.value || "";
  const discountElement = document.querySelector("#preview-discount"), rateElement = document.querySelector("#preview-rate");
  if (discountElement) discountElement.textContent = discount === "" ? "—" : `${discount} bps`;
  if (rateElement) rateElement.textContent = discount === "" || baseline === "" ? "—" : rate(Number(baseline) - Number(discount));
}

function revisionForm(detail) {
  if (appFor(detail.application_id)?.manager_id !== currentUser()?.id || !["approved", "declined"].includes(detail.status)) return "";
  const version = detail.current_version, reference = `${detail.request_id}:${version.version_number}`;
  const raw = getFormDraft("revision", reference);
  const context = draftContext(version.context, raw, appFor(detail.application_id));
  return `<section class="card"><div class="eyebrow">New version</div><h2>Revise the terms</h2><p class="help">A revision becomes pending and needs a fresh decision. The existing version stays in history.</p><form id="revision-form" data-reference="${escapeHtml(reference)}"><div class="field"><label for="revision-discount">New discount (basis points)</label><input id="revision-discount" name="discount_bps" type="number" min="1" step="1" value="${escapeHtml(raw?.discount_bps ?? version.discount_bps)}" required></div>${contextFields("revision", context)}<div class="field"><label for="revision-reason">Reason for revised terms</label><textarea id="revision-reason" name="reason" maxlength="2000" required>${escapeHtml(raw?.reason ?? version.reason)}</textarea></div><div class="button-row"><button class="button primary" type="submit" ${state.busy ? "disabled" : ""}>Submit revised version</button></div></form></section>`;
}

function renderRequests() {
  const rows = state.requests.filter((row) => (!state.applicationFilter || row.application_id === state.applicationFilter) && (!state.statusFilter || row.status === state.statusFilter) && row.application_reference.toLowerCase().includes(state.requestSearch.toLowerCase()));
  const selected = state.detail && rows.some((row) => row.request_id === state.detail.request_id);
  const actions = isManager() ? `<button class="button primary" data-screen="create">${icon("create", 15)}New request</button>` : '<button class="button primary" data-screen="review">Open review queue</button>';
  return `${pageHeading("Discount requests", "A clear view of every submission and its current decision.", actions)}${statsHtml()}<div class="workbench ${selected ? "has-selection" : ""}"><section class="card"><div class="card-header"><h2>All requests <span class="muted">(${rows.length})</span></h2><button class="button small" data-action="reload">Refresh</button></div><div class="toolbar"><div class="field search-field"><label for="request-search">Search applications</label><input id="request-search" type="search" placeholder="Find an application reference…" value="${escapeHtml(state.requestSearch)}"></div><div class="field"><label for="status-filter">Status</label><select id="status-filter"><option value="">All statuses</option>${["pending", "approved", "declined"].map((status) => `<option value="${status}" ${status === state.statusFilter ? "selected" : ""}>${status[0].toUpperCase() + status.slice(1)}</option>`).join("")}</select></div><div class="field"><label for="application-filter">Application</label><select id="application-filter"><option value="">All applications</option>${appOptions(state.applications, state.applicationFilter)}</select></div></div>
    ${rows.length ? `<div class="table-wrap"><table class="data-table"><caption class="sr-only">Current discount requests</caption><thead><tr><th scope="col">Application</th><th scope="col">Status</th><th scope="col">Version</th><th scope="col">Action</th></tr></thead><tbody>${rows.map((row) => `<tr class="${row.request_id === state.selectedRequestId ? "selected" : ""}"><td><span class="reference">${escapeHtml(row.application_reference)}</span><span class="subline">${escapeHtml(state.users.find((user) => user.id === appFor(row.application_id)?.manager_id)?.display_name || "")}</span></td><td>${statusBadge(row.status)}</td><td><span class="version-tag">v${row.current_version_number}</span></td><td><button class="button small" data-action="open-request" data-request="${escapeHtml(row.request_id)}">View request</button></td></tr>`).join("")}</tbody></table></div>` : empty("Try another filter or start a new request from an application.", "No requests to display")}</section>
    ${selected ? `<aside class="stack"><section class="card">${detailFields(state.detail)}<div class="button-row"><button class="button small" data-action="view-history" data-request="${escapeHtml(state.detail.request_id)}">View history</button><button class="button small quiet" data-action="close-detail">Close</button></div></section>${pricingHtml()}${isManager() ? revisionForm(state.detail) : ""}</aside>` : ""}</div>`;
}

function renderApplications() {
  const rows = state.applications.filter((item) => item.reference.toLowerCase().includes(state.applicationSearch.toLowerCase()));
  return `${pageHeading("Applications", "Saved loan details, ready to use in a discount request.")}<section class="card"><div class="card-header"><h2>Mortgage applications <span class="muted">(${state.applications.length})</span></h2><button class="button small" data-action="reload">Refresh</button></div><div class="toolbar"><div class="field search-field"><label for="application-search">Search applications</label><input id="application-search" type="search" placeholder="Find an application reference…" value="${escapeHtml(state.applicationSearch)}"></div></div>${rows.length ? `<div class="table-wrap"><table class="data-table"><caption class="sr-only">Saved mortgage application financial details</caption><thead><tr><th scope="col">Application</th><th scope="col" class="numeric">Loan amount</th><th scope="col" class="numeric">Property value</th><th scope="col">Standard rate</th><th scope="col">Term</th><th scope="col">Request</th></tr></thead><tbody>${rows.map((item) => { const request = state.requests.find((row) => row.application_id === item.id); return `<tr><td><span class="reference">${escapeHtml(item.reference)}</span><span class="subline">${escapeHtml(state.users.find((user) => user.id === item.manager_id)?.display_name || "")}</span></td><td class="numeric">${money(item.loan_amount)}</td><td class="numeric">${money(item.property_value)}</td><td>${rate(item.standard_rate_bps)}</td><td>${term(item.term_months)}</td><td>${request ? `<button class="button small" data-action="open-request" data-request="${escapeHtml(request.request_id)}">View request</button>` : isManager() && item.manager_id === currentUser()?.id ? `<button class="button small" data-action="new-request" data-application="${escapeHtml(item.id)}">New request</button>` : '<span class="muted">Not submitted</span>'}</td></tr>`; }).join("")}</tbody></table></div>` : empty("Try another application reference.", "No applications match")}</section>`;
}

function renderReview() {
  if (!isReviewer()) return pageHeading("Review queue", "Only a reviewer can make a decision.");
  const pending = state.requests.filter((row) => row.status === "pending"), detail = state.reviewDetail;
  const own = detail && (detail.current_version.submitted_by_login === state.login || appFor(detail.application_id)?.manager_id === currentUser()?.id);
  const canDecide = detail?.status === "pending" && !own;
  const assessment = state.assessment?.result;
  const aiPanel = detail && !own ? `<hr class="section-divider"><h3>Optional AI assistance</h3><p class="help">Local model assistance is optional. You can review and decide without installing or enabling it.</p><div class="button-row"><button class="button quiet" type="button" data-action="ai-toggle" aria-pressed="${state.aiEnabled}">${state.aiEnabled ? "Turn AI off" : "Turn AI on for this session"}</button><button class="button" type="button" data-action="generate-assessment" ${!state.aiEnabled || state.busy ? "disabled" : ""}>Generate assessment for v${detail.current_version.version_number}</button></div>${state.assessment?.status === "stale" ? '<div class="notice warning">The request changed during generation. This assessment is stale and hidden.</div>' : assessment ? `<div class="notice"><strong>Advisory summary · v${state.assessment.version_number}</strong><p>${escapeHtml(assessment.summary)}</p><p><strong>Reported claims (unverified)</strong></p><ul>${assessment.reported_claims.map((item) => `<li>${escapeHtml(item)}</li>`).join("") || "<li>None listed</li>"}</ul><p><strong>Missing information to review</strong></p><ul>${assessment.missing_information.map((item) => `<li>${escapeHtml(item.item)} — ${escapeHtml(item.reason)}</li>`).join("") || "<li>None listed</li>"}</ul><p>${assessment.limitations.map(escapeHtml).join(" ")}</p><p class="help">Advisory only. Check the submitted version yourself; no external evidence was verified.</p></div>` : ""}` : "";
  return `${pageHeading("Review queue", "Review the submitted terms and record a human decision.", '<button class="button" data-action="reload">Refresh queue</button>')}<div class="review-layout"><section class="card"><div class="card-header"><h2>Awaiting review</h2><span class="version-tag">${pending.length}</span></div>${pending.length ? listRequests(pending, state.selectedReviewId) : empty("New submissions will appear here.", "Queue is clear")}</section><section class="card">${detail ? detailFields(detail) : empty("Choose a pending request to see its submitted terms.", "Ready for your review")}${own ? '<div class="notice warning">You cannot review your own application or submission.</div>' : ""}${aiPanel}${canDecide ? `<hr class="section-divider"><h3>Decision on version ${detail.current_version.version_number}</h3><p class="help">Approval accepts the requested discount exactly. Editing terms requires a new version.</p><div class="button-row"><button class="button primary" data-action="decide" data-outcome="approved" ${state.busy ? "disabled" : ""}>Approve version ${detail.current_version.version_number}</button><button class="button danger" data-action="decide" data-outcome="declined" ${state.busy ? "disabled" : ""}>Decline version ${detail.current_version.version_number}</button></div>` : ""}${detail ? `<div class="button-row"><button class="button quiet" data-action="view-history" data-request="${escapeHtml(detail.request_id)}">View decision history</button></div>` : ""}</section></div>`;
}

function renderHistory() {
  const selected = state.requests.find((row) => row.request_id === state.historyRequestId);
  const events = state.history.map((event) => {
    const older = event.event_type === "approved" && event.version_number < (selected?.current_version_number || 0);
    const title = older ? "Earlier approval · historical" : ({ created: "Request submitted", revised: "Revised terms submitted", approved: "Discount approved", declined: "Discount declined" })[event.event_type] || event.event_type;
    const decision = event.version?.decision;
    return `<article class="history-event"><div class="history-title">${escapeHtml(title)}<span class="version-tag">Version ${event.version_number}</span></div><div class="history-meta">${escapeHtml(userName(event.actor_login))} · ${escapeHtml(timestamp(event.occurred_at))}</div><details><summary>View submitted terms · ${event.version.discount_bps} bps</summary><p class="help">Associated version terms and final decision; this is not a status snapshot at the event time.</p><div class="reason-box">${escapeHtml(event.version.reason)}</div><dl class="details">${event.version.context ? contextSummary(event.version.context) : '<dt>Application context</dt><dd>Not recorded</dd>'}<dt>Submitted</dt><dd>${escapeHtml(timestamp(event.version.submitted_at))}</dd>${decision ? `<dt>Final decision</dt><dd>${statusBadge(decision.outcome)} · ${escapeHtml(decision.reviewer_login)}</dd>` : ""}</dl></details></article>`;
  }).join("");
  return `${pageHeading("Request history", "Every version and decision, preserved in a single timeline.")}<section class="card"><div class="field"><label for="history-request">Application / request</label><select id="history-request"><option value="">Select a request</option>${requestOptions(state.requests, state.historyRequestId)}</select></div>${selected ? `<hr class="section-divider"><div class="card-header"><h2>${escapeHtml(selected.application_reference)}</h2>${statusBadge(selected.status)}</div><div class="history-list">${events || empty("Loading the recorded events…")}</div>` : empty("Select a request to see who submitted, revised and reviewed each version.", "A complete audit trail")}</section>`;
}

function render(options = {}) {
  const active = document.activeElement;
  const focusId = active?.id;
  const selection = active && ["text", "search"].includes(active.type) ? [active.selectionStart, active.selectionEnd] : null;
  if (state.screen === "create" && !isManager() || state.screen === "review" && !isReviewer()) state.screen = "requests";
  identityHtml();
  document.querySelector("#navigation").innerHTML = navHtml();
  const names = { requests: "Requests", applications: "Applications", create: "New request", review: "Review queue", history: "History" };
  document.querySelector("#breadcrumbs").innerHTML = `Workspace <span>/ ${names[state.screen] || "Requests"}</span>`;
  const views = { requests: renderRequests, applications: renderApplications, create: renderCreate, review: renderReview, history: renderHistory };
  app.innerHTML = noticeHtml() + (views[state.screen] || renderRequests)();
  if (state.busy) for (const control of app.querySelectorAll("input, select, textarea, button")) control.disabled = true;
  const replacement = document.getElementById(options.focusHeading ? "main-heading" : focusId);
  if (replacement && !replacement.disabled) {
    replacement.focus({ preventScroll: !options.focusHeading });
    if (selection && !options.focusHeading) replacement.setSelectionRange(...selection);
  }
}
