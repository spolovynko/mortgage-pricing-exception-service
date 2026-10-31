const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const views = fs.readFileSync(path.join(__dirname, "../../ui/workspace.js"), "utf8");
const controller = fs.readFileSync(path.join(__dirname, "../../ui/app.js"), "utf8")
  .replace(/\nbootstrap\(\);\s*$/, "\n");

function workspace(storage = new Map()) {
  const listeners = new Map();
  const app = { innerHTML: "", addEventListener: (kind, callback) => listeners.set(kind, callback), querySelectorAll: () => [] };
  const elements = new Map([
    ["#app", app], ["#identity", { innerHTML: "", addEventListener() {} }],
    ["#navigation", { innerHTML: "", addEventListener() {} }], ["#breadcrumbs", { innerHTML: "" }],
  ]);
  let calls = 0;
  const context = vm.createContext({
    document: { querySelector: (selector) => elements.get(selector) || null, getElementById: () => null, activeElement: null },
    sessionStorage: { getItem: (key) => storage.get(key) ?? null, setItem: (key, value) => storage.set(key, value), removeItem: (key) => storage.delete(key) },
    fetch: async () => { calls++; throw new Error("Unexpected network call"); },
    AbortController, setTimeout, clearTimeout, console,
    FormData: class { constructor(form) { this.form = form; } get(name) { return this.form.elements.namedItem(name)?.value ?? null; } },
  });
  vm.runInContext(views + "\n" + controller, context);
  const run = (code) => vm.runInContext(code, context);
  run(`state.users = [{id:"ada",login:"ada.manager",display_name:"Ada Manager (Fictional)",roles:["relationship_manager"]},{id:"blake",login:"blake.reviewer",display_name:"Blake Reviewer (Fictional)",roles:["reviewer"]}];
    state.applications = [{id:"app-a",reference:"SYN-A",manager_id:"ada",loan_amount:"250000.00",property_value:"320000.00",standard_rate_bps:425,term_months:300},{id:"app-b",reference:"SYN-B",manager_id:"ada",loan_amount:"180000.00",property_value:"240000.00",standard_rate_bps:475,term_months:240}];`);
  return { run, context, app, listeners, storage, elements, calls: () => calls };
}

function form(id = "create-form", reference = "new", changes = {}) {
  const values = {
    application_id: "app-a", discount_bps: "37", reason: "Draft <img src=x> stays private to this identity",
    purpose: "purchase", rate_type: "fixed", loan_amount: "245123.45", property_value: "320000.00",
    currency_code: "EUR", term_months: "300", standard_rate_bps: "425", reason_category: "competitive_offer",
    competitor_rate_bps: "390", competitor_expires_on: "2027-01-31", synthetic_example: "",
    ...changes,
  };
  const fields = Object.fromEntries(Object.entries(values).map(([name, value]) => [name, { value, validityMessage: "", setCustomValidity(message) { this.validityMessage = message; } }]));
  return { id, dataset: { reference }, elements: { namedItem: (name) => fields[name] }, reportValidity: () => Object.values(fields).every((field) => !field.validityMessage), fields };
}

test("assessment report is rendered in a fixed readable text format", () => {
  const page = workspace();
  page.context.testAssessment = {
    request_id: "request-a", version_number: 2, result: {
      suggested_outcome: "suggest_do_not_approve", outcome_rationale: "Required checklist information is missing.",
      summary: "Review the submitted context.", reported_claims: ["A claim"],
      missing_information: [{ item: "Income evidence", reason: "Not provided" }], limitations: ["No external verification."],
    },
  };
  const report = page.run("assessmentReportText(testAssessment)");
  assert.match(report, /^AI ASSESSMENT REPORT/);
  assert.match(report, /Suggested outcome: Suggest do not approve/);
  assert.match(report, /REPORTED CLAIMS \(UNVERIFIED\)\n- A claim/);
  assert.match(report, /MISSING INFORMATION TO REVIEW\n- Income evidence — Not provided/);
  assert.match(report, /DECISION AUTHORITY/);
});

test("assessment preview streams readable text without exposing its JSON envelope", () => {
  const page = workspace();
  page.context.preview = page.run('assessmentStreamPreview("request-a", 1, \'{"summary":"Review the submitted terms\\ncarefully\')');
  assert.match(page.context.preview, /SUMMARY\nReview the submitted terms\ncarefully/);
  assert.match(page.context.preview, /REPORTED CLAIMS \(UNVERIFIED\)/);
  assert.doesNotMatch(page.context.preview, /"summary"/);
});

test("assessment performance text distinguishes first text from model generation", () => {
  const page = workspace();
  page.context.performanceText = page.run('assessmentPerformanceText({startedAt:1000,firstTextAt:3500,completedAt:7500},{load_duration:1000000000,prompt_eval_duration:500000000,eval_duration:2000000000,eval_count:40})');
  assert.match(page.context.performanceText, /First report text 2\.5s/);
  assert.match(page.context.performanceText, /total 6\.5s/);
  assert.match(page.context.performanceText, /model load 1\.0s/);
  assert.match(page.context.performanceText, /generation 2\.0s \(40 tokens · 20\.0 tokens\/s\)/);
});

test("create draft survives view changes and reload without rendering narrative as HTML", () => {
  const page = workspace();
  page.context.testForm = form();
  page.run('saveFormDraft(testForm); state.screen="applications"; render(); state.screen="requests"; render(); state.screen="create"; render();');
  assert.match(page.app.innerHTML, /value="245123\.45"/);
  assert.match(page.app.innerHTML, /value="37"/);
  assert.match(page.app.innerHTML, /Draft &lt;img src=x&gt;/);
  assert.doesNotMatch(page.app.innerHTML, /<img src=x>/);
  const reloaded = workspace(page.storage);
  reloaded.run('state.screen="create"; render();');
  assert.match(reloaded.app.innerHTML, /value="245123\.45"/);
  assert.match(reloaded.app.innerHTML, /Draft &lt;img src=x&gt;/);
  assert.equal(page.calls() + reloaded.calls(), 0);
});

test("drafts remain scoped to identity and exact revision version", () => {
  const page = workspace();
  page.context.testForm = form();
  page.run('saveFormDraft(testForm); state.login="blake.reviewer";');
  assert.equal(page.run('getFormDraft("create")'), null);
  page.run('state.screen="create"; render();');
  assert.equal(page.run('state.screen'), "requests");
  assert.doesNotMatch(page.elements.get("#navigation").innerHTML, /data-screen="create"/);
  assert.match(page.elements.get("#navigation").innerHTML, /data-screen="review"/);
  page.run('state.login="ada.manager";');
  page.context.testForm = form("revision-form", "request-a:1");
  page.run('saveFormDraft(testForm);');
  assert.equal(page.run('getFormDraft("revision", "request-a:1").discount_bps'), "37");
  assert.equal(page.run('getFormDraft("revision", "request-a:2")'), null);
  assert.equal(page.run('getFormDraft("revision", "request-b:1")'), null);
});

test("switching applications refreshes financial defaults and retains the entered justification", async () => {
  const page = workspace();
  const draft = form("create-form", "new", { application_id: "app-b" });
  page.context.testForm = draft;
  await page.listeners.get("change")({ target: { id: "create-application", value: "app-b", form: draft } });
  assert.equal(page.run('getFormDraft("create").loan_amount'), "180000.00");
  assert.equal(page.run('getFormDraft("create").standard_rate_bps'), "475");
  assert.equal(page.run('getFormDraft("create").term_months'), "240");
  assert.equal(page.run('getFormDraft("create").discount_bps'), "37");
  assert.equal(page.run('getFormDraft("create").reason'), draft.fields.reason.value);
  assert.equal(page.calls(), 0);
});

test("editing a draft preserves the original pending creation key and payload", () => {
  const page = workspace();
  page.run('setCreateIntent({key:"original-key",payload:{application_id:"app-a",discount_bps:25,reason:"Original submission"}});');
  const original = page.run('JSON.stringify(getCreateIntent())');
  page.context.testForm = form();
  page.run('saveFormDraft(testForm); state.screen="create"; render();');
  assert.match(page.app.innerHTML, /value="37"/);
  assert.equal(page.run('JSON.stringify(getCreateIntent())'), original);
  assert.equal(page.calls(), 0);
});

test("retrying a failed create reuses the original idempotency key and payload", async () => {
  const page = workspace();
  const attempts = [];
  page.run('state.requests = [];');
  page.context.fetch = async (_path, options) => {
    attempts.push({ path: _path, method: options.method, key: options.headers["Idempotency-Key"], body: options.body });
    if (attempts.length === 1) throw new Error("synthetic connection failure");
    const body = _path === "/requests" && options.method === "POST"
      ? { request_id: "request-a", version_number: 1, replayed: true }
      : _path === "/requests" ? []
        : _path === "/demo/applications" ? []
          : _path === "/requests/request-a" ? { request_id: "request-a", application_id: "app-a" }
            : { application_id: "app-a", status: "none" };
    return { ok: true, headers: { get: () => "retry-correlation" }, json: async () => body };
  };
  page.context.testForm = form();
  await page.run("submitCreate(testForm)");
  const pending = page.run("JSON.stringify(getCreateIntent())");
  assert.match(page.app.innerHTML, /Retry submission/);
  await page.run('handleWorkspaceClick({ target: { closest: () => ({ dataset: { action: "retry-create" } }) } })');
  const submissions = attempts.filter((attempt) => attempt.path === "/requests" && attempt.method === "POST");
  assert.equal(submissions.length, 2);
  assert.equal(submissions[0].key, submissions[1].key);
  assert.equal(submissions[0].body, submissions[1].body);
  assert.notEqual(page.run("JSON.stringify(getCreateIntent())"), pending);
});

test("a stale review displays refresh without submitting another decision", async () => {
  const page = workspace();
  const calls = [];
  page.run('state.reviewDetail = { request_id: "request-a", current_version: { version_number: 1 } };');
  page.context.fetch = async (path, options) => {
    calls.push({ path, body: JSON.parse(options.body) });
    return { ok: false, status: 409, headers: { get: () => "stale-correlation" },
      json: async () => ({ error: { code: "stale_version", message: "Refresh the request." } }) };
  };
  await page.run('decide("approved")');
  assert.equal(calls.length, 1);
  assert.equal(calls[0].body.expected_version, 1);
  assert.match(page.app.innerHTML, /Refresh request/);
  assert.equal(page.run('state.reviewDetail.current_version.version_number'), 1);
});

test("an existing request blocks duplicate creation without silently retargeting a saved draft", () => {
  const page = workspace();
  page.context.testForm = form();
  page.run('saveFormDraft(testForm); state.requests=[{request_id:"request-a",application_id:"app-a",application_reference:"SYN-A",status:"approved",current_version_number:1}]; state.screen="create"; render();');
  assert.equal(page.run('creationSelection().selected.id'), "app-a");
  assert.match(page.app.innerHTML, /This application already has a request/);
  assert.match(page.app.innerHTML, /type="submit" disabled/);
  page.run('setCreateIntent({key:"original-key",payload:{application_id:"app-a",discount_bps:37,reason:"Original"}}); render();');
  assert.equal(page.run('creationSelection().existingRequest'), null);
  assert.doesNotMatch(page.app.innerHTML, /type="submit" disabled/);
});

test("competitor expiry without a rate is rejected while its draft is retained", () => {
  const page = workspace();
  page.context.testForm = form("create-form", "new", { competitor_rate_bps: "" });
  page.run('saveFormDraft(testForm);');
  assert.equal(page.run('readContext(testForm)'), null);
  assert.match(page.context.testForm.fields.competitor_expires_on.validityMessage, /competitor rate/);
  assert.equal(page.run('getFormDraft("create").competitor_expires_on'), "2027-01-31");
  assert.equal(page.calls(), 0);
});
