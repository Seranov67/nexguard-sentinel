"use strict";
const $ = (id) => document.getElementById(id);
let currentCase = null;
let cases = [];
let offset = 0;
let total = 0;
let pendingDecision = null;
let loading = false;
let caseLoading = false;
let decisionSaving = false;
let caseRequest = 0;
const drafts = new Map();
const pageSize = 50;

function rememberDraft() {
  if (currentCase) drafts.set(currentCase.id, {note:$("note").value, disposition:$("disposition").value});
}
function decisionControls() {
  $("decision-submit").disabled = caseLoading || decisionSaving || !currentCase || currentCase.status === "resolved";
  $("reload-case").disabled = caseLoading || decisionSaving || !currentCase;
  for (const id of ["operator", "note", "disposition"]) $(id).disabled = decisionSaving;
}

function text(id, value) { $(id).textContent = value ?? "Unknown"; }
function node(tag, value, className) {
  const result = document.createElement(tag);
  if (value !== undefined) result.textContent = value;
  if (className) result.className = className;
  return result;
}
function facts(id, pairs) {
  $(id).replaceChildren();
  for (const [label, value] of pairs) $(id).append(node("dt", label), node("dd", String(value ?? "Unknown")));
}
function view(name) {
  for (const section of document.querySelectorAll(".view")) section.hidden = section.id !== `${name}-view`;
  for (const nav of document.querySelectorAll(".nav")) {
    const active = nav.dataset.view === name || (name === "detail" && nav.dataset.view === "cases");
    nav.classList.toggle("active", active);
    if (active) nav.setAttribute("aria-current", "page"); else nav.removeAttribute("aria-current");
  }
}
async function api(path, options) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try { const body = await response.json(); detail = body.detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return response.json();
}
function renderCases() {
  const state = $("case-filter").value;
  const filtered = cases.filter((c) => state === "all" || c.status === state);
  $("case-list").replaceChildren();
  for (const c of filtered) {
    const button = node("button", undefined, "case-row");
    const label = node("div");
    label.append(node("strong", `${c.finding.observed_amount} accounting units`));
    label.append(node("small", `${c.finding.synthetic ? "SYNTHETIC · " : ""}${c.finding.policy_version} · Case ${c.id.slice(0, 12)} · ${c.created_at}`));
    button.append(label, node("span", c.status, "tag"));
    button.addEventListener("click", () => openCase(c.id));
    $("case-list").append(button);
  }
  if (!filtered.length) $("case-list").append(node("div", "No cases in this page and state. The observer opens cases only for withdrawals above the policy limit.", "empty"));
  text("page-note", `${offset + (cases.length ? 1 : 0)}–${offset + cases.length} of ${total} · Filter applies to this page`);
  $("previous").disabled = offset === 0;
  $("next").disabled = offset + pageSize >= total;
}
async function refresh() {
  if (loading) return;
  loading = true;
  try {
    const [status, page] = await Promise.all([api("/api/status"), api(`/api/cases?limit=${pageSize}&offset=${offset}`)]);
    const health = status.health;
    const synthetic = status.scope?.origin === "synthetic_fixture";
    text("health-label", health.status.replaceAll("_", " "));
    text("health-age", health.checked_at ? `Checked ${health.checked_at}` : "No source read recorded");
    text("observations", status.counts.observations); text("case-count", status.counts.review_cases);
    text("observations-label", synthetic ? "Fixture observations" : "Verified observations");
    text("queue-count", status.counts.review_cases);
    text("paused", typeof health.guardian_paused === "boolean" ? (health.guardian_paused ? "Paused" : "Unpaused") : "Unknown");
    text("state-block", health.state_block ? `Recorded at block ${health.state_block}` : "No state read");
    text("origin-tag", synthetic ? "SYNTHETIC FIXTURE" : "GRAPH + RPC");
    facts("source-facts", [["RPC head", health.rpc_head], ["Graph snapshot", health.graph_snapshot], ["Confirmed through", health.confirmed_through], ["Block age (seconds)", health.block_age_seconds], ["Last checked (UTC)", health.checked_at], ["Vault", status.vault], ["Guardian", status.guardian]]);
    text("source-limits", health.gap || (health.limits || []).join(" "));
    text("policy-limit", status.policy.withdrawal_limit); text("policy-version", status.policy.version);
    $("notice").classList.toggle("alert", synthetic || health.status !== "healthy");
    text("notice", synthetic ? "SYNTHETIC DEMO · Fixture events only. No live contract or transaction evidence." : health.status === "healthy" ? "Live provider observations · Historical events may be present · Reviewer decisions are local" : `Source ${health.status.replaceAll("_", " ")} · Stored facts remain available; refresh and check verification times.`);
    cases = page.items; total = page.total; renderCases();
  } catch (error) {
    $("notice").classList.add("alert"); text("notice", `Desk unavailable: ${error.message}`);
  } finally { loading = false; }
}
async function openCase(id) {
  if (decisionSaving) return false;
  rememberDraft();
  const request = ++caseRequest;
  caseLoading = true; decisionControls();
  try {
    const value = await api(`/api/cases/${encodeURIComponent(id)}`);
    if (request !== caseRequest) return false;
    rememberDraft();
    currentCase = value.case; pendingDecision = null;
    const c = currentCase, f = c.finding, raw = c.observation.raw;
    text("detail-title", `Case ${id.slice(0, 12)}`);
    text("detail-meta", `${value.synthetic ? "SYNTHETIC FIXTURE" : "Recorded provider evidence"} · Revision ${c.revision} · ${c.created_at}`);
    text("case-status", c.status);
    facts("finding-facts", [["Amount (valueless units)", f.observed_amount], ["Threshold (strictly above)", f.threshold], ["Policy version", f.policy_version], ["Reason", f.reason], ["Withdrawal block", raw.blockNumber], ["Actor", raw.who], ["Source entity", raw.id], ["Disposition", c.disposition || "Pending"]]);
    $("conflict-warning").hidden = !c.conflicts.length;
    text("conflict-warning", "Conflicting source evidence. Reconciliation required; only insufficient-evidence resolution is allowed.");
    $("explorer-links").replaceChildren();
    for (const [label, url] of Object.entries(value.links)) {
      if (!url.startsWith("https://sepolia.basescan.org/")) continue;
      const link = node("a", `View ${label} ↗`); link.href = url; link.target = "_blank"; link.rel = "noopener noreferrer";
      $("explorer-links").append(link);
    }
    text("legacy-status", `Recorded action evidence: ${value.legacy_action.status.replaceAll("_", " ")}`);
    text("legacy-gap", value.legacy_action.gap || "Synthetic fixture; no action occurred in this demo.");
    text("legacy-evidence", JSON.stringify(value.legacy_action, null, 2));
    text("source-evidence", JSON.stringify({observation:c.observation, policy:c.policy_definition, health:value.source_health, limits:value.limits}, null, 2));
    $("export-json").href = `/api/cases/${id}/export/json`; $("export-txt").href = `/api/cases/${id}/export/txt`;
    $("disposition-label").hidden = c.status !== "acknowledged";
    text("decision-submit", c.status === "open" ? "Acknowledge case" : c.status === "acknowledged" ? "Resolve with disposition" : "Decision recorded");
    text("decision-message", c.status === "resolved" ? "This review is resolved. The chain state is unchanged by this decision." : "");
    const draft = drafts.get(id);
    $("note").value = draft?.note || "";
    $("disposition").value = draft?.disposition || "insufficient_evidence";
    $("history").replaceChildren();
    for (const action of c.history) {
      const item = node("li"); item.append(node("strong", `${action.operator} · ${action.status}`), node("p", action.at), node("p", action.disposition || "Awaiting disposition"), node("p", action.note)); $("history").append(item);
    }
    if (!c.history.length) $("history").append(node("li", "No operator decision recorded."));
    view("detail");
    return true;
  } catch (error) {
    if (request === caseRequest) { text("notice", error.message); $("notice").classList.add("alert"); }
    return false;
  } finally {
    if (request === caseRequest) { caseLoading = false; decisionControls(); }
  }
}
$("decision-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!currentCase || currentCase.status === "resolved" || caseLoading || decisionSaving) return;
  const c = currentCase;
  const fields = {action:c.status === "open" ? "acknowledge" : "resolve", revision:c.revision, operator:$("operator").value.trim(), note:$("note").value.trim(), disposition:c.status === "acknowledged" ? $("disposition").value : null};
  if (!fields.operator || !fields.note) { text("decision-message", "Enter your operator label and a review note."); return; }
  const fingerprint = JSON.stringify(fields);
  if (!pendingDecision || pendingDecision.fingerprint !== fingerprint) pendingDecision = {fingerprint, payload:{...fields, request_id:crypto.randomUUID()}};
  decisionSaving = true; decisionControls();
  try {
    await api(`/api/cases/${c.id}/decisions`, {method:"POST", headers:{"Content-Type":"application/json", "X-NexGuard-Review":"1"}, body:JSON.stringify(pendingDecision.payload)});
    drafts.delete(c.id); $("note").value = ""; $("disposition").value = "insufficient_evidence";
    pendingDecision = null; decisionSaving = false;
    const reloaded = await openCase(c.id);
    await refresh();
    text("decision-message", reloaded ? "Decision saved locally." : "Decision saved locally. Reload case to see the current revision.");
  } catch (error) {
    text("decision-message", `${error.message}. Your draft is retained in this page; retry or use Reload case to load its revision.`);
  } finally { decisionSaving = false; decisionControls(); }
});
$("reload-case").addEventListener("click", () => { if (currentCase) openCase(currentCase.id); });
for (const button of document.querySelectorAll("[data-view]")) button.addEventListener("click", () => { view(button.dataset.view); if (button.dataset.view === "cases") refresh(); });
$("refresh").addEventListener("click", refresh); $("case-filter").addEventListener("change", renderCases);
$("previous").addEventListener("click", () => {offset = Math.max(0, offset - pageSize); refresh();});
$("next").addEventListener("click", () => {offset += pageSize; refresh();});
refresh(); setInterval(refresh, 15000);
