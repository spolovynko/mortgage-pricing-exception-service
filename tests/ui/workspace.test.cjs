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
