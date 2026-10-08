"use strict";
// resextract dashboard UI — no framework, no CDN, no build step.
// Everything is read from same-origin relative routes under /api/.

const $ = (id) => document.getElementById(id);

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function clear(node) { while (node.firstChild) node.removeChild(node.firstChild); }

function card(k, v) {
  const c = el("div", "card");
  c.appendChild(el("div", "k", k));
  c.appendChild(el("div", "v", v === null || v === undefined ? "—" : v));
  return c;
}

function banner(node, text, kind) {
  clear(node);
  node.className = "banner" + (kind ? " " + kind : "");
  node.textContent = text || "";
}

function table(headers, rows) {
  const t = el("table");
  const thead = el("thead");
  const htr = el("tr");
  headers.forEach((h) => htr.appendChild(el("th", null, h)));
  thead.appendChild(htr);
  t.appendChild(thead);
  const tbody = el("tbody");
  rows.forEach((row) => {
    const tr = el("tr");
    row.forEach((cell) => {
      const td = el("td");
      if (cell instanceof Node) td.appendChild(cell); else td.textContent = cell === null || cell === undefined ? "—" : String(cell);
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
  t.appendChild(tbody);
  return t;
}

function pretty(value) {
  try { return JSON.stringify(value); } catch (err) { return String(value); }
}

async function getJSON(path) {
  const res = await fetch(path, { headers: { accept: "application/json" } });
  const body = await res.json().catch(() => ({ error: "invalid JSON response (" + res.status + ")" }));
  return { status: res.status, body: body };
}

// ---------------------------------------------------------------- doctor --- //

async function loadDoctor() {
  const box = $("doctor");
  const { body } = await getJSON("/api/doctor");
  clear(box);
  const legs = (body && body.legs) || [];
  if (!legs.length) {
    box.appendChild(el("span", "muted", "doctor: " + ((body && body.error) || "no legs reported")));
    return;
  }
  legs.forEach((leg) => {
    const cls = "leg " + (leg.ok ? "ok" : "down");
    box.appendChild(el("span", cls, leg.leg + ": " + (leg.ok ? "up" : "down")));
  });
  const occamy = (body.by_leg || {}).Occamy;
  box.title = occamy ? occamy.detail : "";
}

// ------------------------------------------------------------------ runs --- //

async function loadRuns() {
  const { body } = await getJSON("/api/runs");
  const summary = $("runs-summary");
  clear(summary);
  if (body.error) { banner($("degradations"), body.error, "error"); }
  summary.appendChild(card("runs", body.count));
  summary.appendChild(card("journals", (body.journals || []).length));
  summary.appendChild(card("degradations", (body.degradations || []).length));
  const runs = body.runs || [];
  clear($("runs-table"));
  if (!runs.length) {
    $("runs-table").appendChild(el("p", "muted", "no runs recorded in the store"));
  } else {
    $("runs-table").appendChild(table(
      ["id", "target", "status", "started", "finished", "tokens", "journal", "notes"],
      runs.map((r) => [r.id, r.target, r.status, r.started_at, r.finished_at, r.tokens_used, r.journal_file || "none", r.notes])
    ));
  }
  clear($("journals"));
  $("journals").appendChild(table(
    ["run", "events", "bytes", "chain verify", "first bad seq", "mtime"],
    (body.journals || []).map((j) => {
      const v = j.verify || {};
      const tag = el("span", "tag " + (v.ok ? "ok" : "down"), v.ok ? "ok" : (v.ok === false && v.error ? "unreadable" : "broken"));
      return [j.run_id, j.events, j.size_bytes, tag, v.first_bad_seq, j.mtime];
    })
  ));
  clear($("degradations"));
  const degs = body.degradations || [];
  if (!degs.length) {
    $("degradations").appendChild(el("p", "muted", "no degradations recorded"));
  } else {
    $("degradations").appendChild(table(["kind", "run", "detail"], degs.map((d) => [d.kind, d.run_id || "—", d.detail])));
  }
  clear($("resume-point"));
  $("resume-point").appendChild(el("pre", null, JSON.stringify(body.resume_point, null, 2)));

  const select = $("reasoning-run");
  const current = select.value;
  clear(select);
  select.appendChild(el("option", null, "latest journal"));
  select.firstChild.value = "";
  (body.journals || []).forEach((j) => {
    const opt = el("option", null, j.run_id);
    opt.value = j.run_id;
    select.appendChild(opt);
  });
  select.value = current || "";
}

// ------------------------------------------------------------- reasoning --- //

async function loadReasoning() {
  const run = $("reasoning-run").value;
  const limit = $("reasoning-limit").value || 200;
  const query = "/api/reasoning?limit=" + encodeURIComponent(limit) + (run ? "&run_id=" + encodeURIComponent(run) : "");
  const { body } = await getJSON(query);
  const bannerNode = $("reasoning-banner");
  if (body.error) {
    banner(bannerNode, body.error, "error");
  } else if (body.reasoning_text_available === false) {
    banner(bannerNode,
      "reasoning text NOT captured — reasoning_text_available: false\n" + (body.note || ""), "");
  } else {
    banner(bannerNode, "reasoning_content is present in this journal", "ok");
  }
  const meta = $("reasoning-meta");
  clear(meta);
  meta.appendChild(card("run", body.run_id || "—"));
  meta.appendChild(card("events", body.count));
  meta.appendChild(card("total in journal", body.total_events));
  meta.appendChild(card("reasoning text", body.reasoning_text_available ? "captured" : "not captured"));
  meta.appendChild(card("reasoning_tokens key", body.reasoning_tokens_recorded ? "recorded" : "absent"));
  meta.appendChild(card("chain verify", body.verify ? (body.verify.ok ? "ok" : "broken") : "—"));
  meta.appendChild(card("truncated", body.truncated ? "yes" : "no"));

  const fields = el("details");
  fields.appendChild(el("summary", null, "fields present in this journal (" + ((body.fields_present || []).length) + ")"));
  fields.appendChild(el("pre", null, (body.fields_present || []).join(", ")));
  clear($("reasoning-events"));
  $("reasoning-events").appendChild(fields);

  (body.events || []).forEach((evt) => {
    const row = el("div", "evt");
    row.appendChild(el("span", "seq", "#" + evt.seq + " "));
    row.appendChild(el("span", "kind", evt.kind + " "));
    row.appendChild(el("span", "muted", evt.ts || ""));
    row.appendChild(el("div", "payload", pretty(evt.payload)));
    $("reasoning-events").appendChild(row);
  });
}

// -------------------------------------------------------------- findings --- //

function claimNode(claim) {
  const wrap = el("div", "card");
  wrap.appendChild(el("div", "k", "claim " + claim.id + " · " + (claim.kind || "claim")));
  wrap.appendChild(el("div", null, claim.text || ""));
  const meta = el("div", "muted");
  meta.textContent = "verification_state=" + (claim.verification_state || "—") +
    " · confidence=" + (claim.confidence === null || claim.confidence === undefined ? "—" : claim.confidence) +
    (claim.verdict ? " · verdict=" + claim.verdict.verdict + (claim.verdict.rationale ? " (" + claim.verdict.rationale + ")" : "") : " · no verdict recorded");
  wrap.appendChild(meta);
  (claim.evidence || []).forEach((ev) => {
    const line = el("div", "muted");
    line.textContent = "evidence [" + ev.source_kind + "] " + ev.source_ref + (ev.copy_path ? " → " + ev.copy_path : "");
    wrap.appendChild(line);
  });
  return wrap;
}

async function loadFindings() {
  const { body } = await getJSON("/api/findings");
  const counts = $("findings-counts");
  clear(counts);
  if (body.error) { banner($("findings-accepted"), body.error, "error"); }
  const c = body.counts || {};
  ["candidates", "candidates_accepted", "candidates_rejected", "claims", "evidence", "verdicts"].forEach((key) => {
    counts.appendChild(card(key, c[key]));
  });

  clear($("findings-accepted"));
  (body.candidates || []).forEach((candidate) => {
    const block = el("div", "card");
    block.appendChild(el("div", "k", "candidate #" + candidate.id + " · " + (candidate.kind || "?") + " · state=" + (candidate.state || "?")));
    block.appendChild(el("div", null, candidate.title || "(no title)"));
    const meta = el("div", "muted");
    meta.textContent = "score=" + (candidate.score === null || candidate.score === undefined ? "—" : candidate.score) +
      " · provenance=" + pretty(candidate.provenance_json) + " · graph_nodes=" + pretty(candidate.graph_nodes_json);
    block.appendChild(meta);
    (candidate.claims || []).forEach((claim) => block.appendChild(claimNode(claim)));
    if (!(candidate.claims || []).length) block.appendChild(el("div", "muted", "no claims recorded for this candidate"));
    $("findings-accepted").appendChild(block);
  });
  if (!(body.candidates || []).length) $("findings-accepted").appendChild(el("p", "muted", body.note || "no accepted candidates"));

  clear($("findings-rejected"));
  const rejected = body.rejected || [];
  if (!rejected.length) {
    $("findings-rejected").appendChild(el("p", "muted", "no rejected candidates recorded"));
  } else {
    $("findings-rejected").appendChild(table(
      ["source", "title", "reason", "query", "refs"],
      rejected.map((r) => [r.run_id ? r.run_id + " #" + r.seq : "store #" + r.id, r.title, r.reason, r.query, pretty(r.refs)])
    ));
    $("findings-rejected").appendChild(el("pre", null, JSON.stringify(body.rejected_reasons || {}, null, 2)));
  }
}

// --------------------------------------------------------------- dockets --- //

async function loadDockets() {
  const { body } = await getJSON("/api/dockets");
  banner($("dockets-note"), body.error || body.note || "");
  const board = $("dockets-board");
  clear(board);
  (body.dockets || []).forEach((d) => {
    const c = el("div", "docket-card");
    c.appendChild(el("div", "slug", d.slug));
    const tags = el("div");
    tags.appendChild(el("span", "tag", d.type || "?"));
    tags.appendChild(el("span", "tag", d.status || "?"));
    const fresh = (d.freshness || {}).state || "?";
    const age = (d.freshness || {}).age_days;
    tags.appendChild(el("span", "tag " + (fresh === "current" ? "ok" : "warn"), fresh + (age === null || age === undefined ? "" : " · " + age + "d")));
    const v = d.verify || {};
    tags.appendChild(el("span", "tag " + (v.ok ? "ok" : "down"), v.ok ? "verify ok" : "verify " + ((v.problems || []).length) + " problem(s)"));
    c.appendChild(tags);
    const meta = el("div", "muted");
    meta.textContent = "claims=" + d.claims + " · material=" + d.material + " (" + d.material_bytes + " B) · open questions=" + (d.open_questions || []).length + " · rework=" + (d.rework_open || []).length;
    c.appendChild(meta);
    if (d.error) c.appendChild(el("div", "muted", d.error));
    c.addEventListener("click", () => loadDocketDetail(d.route_slug || d.slug));
    board.appendChild(c);
  });
  if (!(body.dockets || []).length) board.appendChild(el("p", "muted", "no dockets on disk"));
}

async function loadDocketDetail(slug) {
  const box = $("docket-detail");
  clear(box);
  const { status, body } = await getJSON("/api/dockets/" + encodeURIComponent(slug));
  box.appendChild(el("h3", null, "docket " + slug + " (HTTP " + status + ")"));
  if (body.error) { box.appendChild(el("pre", null, body.error)); return; }
  const manifest = body.manifest || {};
  const lane = manifest.lane || {};
  const fresh = manifest.freshness || {};
  const summary = el("div", "card-grid");
  summary.appendChild(card("type", lane.type));
  summary.appendChild(card("status", manifest.status));
  summary.appendChild(card("freshness", fresh.state));
  summary.appendChild(card("age (days)", fresh.age_days));
  summary.appendChild(card("claims", (manifest.claims || []).length));
  summary.appendChild(card("material", (manifest.material || []).length));
  summary.appendChild(card("generated by", (manifest.generated_by || {}).model));
  box.appendChild(summary);
  box.appendChild(el("p", "muted", "thesis: " + (lane.thesis || "—")));
  (body.documents || []).forEach((doc) => {
    const d = el("details");
    d.appendChild(el("summary", null, doc.name + (doc.present ? " (" + doc.bytes + " B, " + (doc.headings || []).length + " headings)" : " — not present")));
    (doc.headings || []).forEach((h) => d.appendChild(el("div", "muted", "  ".repeat(h.level - 1) + "#".repeat(h.level) + " " + h.text)));
    box.appendChild(d);
  });
  const files = el("details");
  files.appendChild(el("summary", null, "files on disk (" + (body.files || []).length + ")"));
  files.appendChild(el("pre", null, (body.files || []).map((f) => f.path + "  " + f.bytes + " B").join("\n")));
  box.appendChild(files);
}

// ------------------------------------------------------------------- web --- //

async function loadWeb() {
  const { body } = await getJSON("/api/web-health");
  banner($("web-note"), body.error || body.note || "", body.degraded ? "" : "ok");
  const h = body.search_health || {};
  const grid = $("web-health");
  clear(grid);
  grid.appendChild(table(
    ["engine", "rows", "ok", "failed", "results", "query", "error"],
    (h.rows || []).map((r) => [r.engine, "", r.ok ? "yes" : "no", "", r.result_count, r.query, r.error])
  ));
  const dayTable = table(["day", "rows", "failed"], Object.keys(h.by_day || {}).map((day) => [day, h.by_day[day], (h.by_day_failed || {})[day] || 0]));
  grid.appendChild(dayTable);
  grid.appendChild(el("pre", null, "by_engine=" + pretty(h.by_engine) + "\nby_engine_failed=" + pretty(h.by_engine_failed)));

  const s = body.web_sources || {};
  const src = $("web-sources");
  clear(src);
  const cards = el("div", "card-grid");
  cards.appendChild(card("sources", s.total));
  cards.appendChild(card("current", s.current));
  cards.appendChild(card("changed", s.changed));
  cards.appendChild(card("gone", s.gone));
  cards.appendChild(card("suspect", s.suspect));
  src.appendChild(cards);
  src.appendChild(table(["url", "state", "http", "fetched_at", "failure_reason"],
    (s.rows || []).map((r) => [r.url, r.change_state, r.http_status, r.fetched_at, r.failure_reason])));
}

// --------------------------------------------------------------- refresh --- //

async function loadRefresh() {
  const { body } = await getJSON("/api/refresh");
  banner($("refresh-note"), body.error || body.note || "", body.note ? "" : "ok");
  const rework = $("refresh-rework");
  clear(rework);
  rework.appendChild(table(
    ["id", "docket", "reason", "required work", "opened", "closed"],
    (body.rework || []).map((r) => [r.id, r.docket_dir || r.docket_id, r.reason, r.required_work, r.opened_at, r.closed_at])
  ));
  const files = $("refresh-files");
  clear(files);
  (body.files || []).forEach((f) => {
    const d = el("details");
    d.appendChild(el("summary", null, f.path + " (" + f.bytes + " B)"));
    (f.headings || []).forEach((h) => d.appendChild(el("div", "muted", "  ".repeat(h.level - 1) + "#".repeat(h.level) + " " + h.text)));
    files.appendChild(d);
  });
  if (!(body.files || []).length) files.appendChild(el("p", "muted", "no UPDATE_BACKLOG.md or WORK_SUGGESTIONS.md on disk"));
}

// ------------------------------------------------------------------- sse --- //

function setSSE(state, cls) {
  $("sse-state").textContent = state;
  $("sse-dot").className = "dot " + cls;
}

function startSSE() {
  const source = new EventSource("/api/events");
  source.addEventListener("heartbeat", () => setSSE("live", "on"));
  source.addEventListener("journal", (msg) => {
    setSSE("live · journal change", "on");
    try {
      const data = JSON.parse(msg.data);
      $("runs-table").dataset.lastEvent = pretty(data);
    } catch (err) { /* ignore */ }
    loadRuns();
  });
  source.addEventListener("docket", (msg) => {
    setSSE("live · docket change", "on");
    loadDockets();
  });
  source.addEventListener("doctor", () => loadDoctor());
  source.addEventListener("end", () => setSSE("stream tick budget reached", "off"));
  source.onerror = () => setSSE("reconnecting", "off");
}

// ------------------------------------------------------------------ boot --- //

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    const panel = $("tab-" + tab.dataset.tab);
    if (panel) panel.classList.add("active");
  });
});

$("refresh").addEventListener("click", () => loadAll());
$("reasoning-load").addEventListener("click", () => loadReasoning());
$("reasoning-run").addEventListener("change", () => loadReasoning());

async function loadAll() {
  await Promise.allSettled([loadDoctor(), loadRuns(), loadFindings(), loadWeb(), loadRefresh()]);
  await Promise.allSettled([loadReasoning(), loadDockets()]);
}

loadAll();
startSSE();
