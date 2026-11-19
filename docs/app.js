// ReelGen backlog dashboard. Reads and writes backlog/topics.json through the GitHub API.
(() => {
  const FILE = "backlog/topics.json";
    const $ = (s) => document.querySelector(s);
  const store = {
    get(k, d = "") { try { return localStorage.getItem("reelgen." + k) ?? d; } catch { return d; } },
    set(k, v) { try { localStorage.setItem("reelgen." + k, v); } catch {} },
  };

  function defaultRepo() {
    const m = location.hostname.match(/^([^.]+)\.github\.io$/);
    const name = location.pathname.split("/").filter(Boolean)[0];
    return m && name ? `${m[1]}/${name}` : "kevinandrin7-start/ReelGen";
  }
  let repo = store.get("repo", defaultRepo());
  let token = store.get("token");
  let data = { topics: [] };
  let sha = null;

  const api = (path, opts = {}) => fetch(`https://api.github.com/repos/${repo}${path}`, {
    ...opts,
    headers: { Accept: "application/vnd.github+json", ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}) },
  });

  const b64decode = (s) => new TextDecoder().decode(Uint8Array.from(atob(s.replace(/\n/g, "")), (c) => c.charCodeAt(0)));
  const b64encode = (s) => { const b = new TextEncoder().encode(s); let out = ""; b.forEach((x) => (out += String.fromCharCode(x))); return btoa(out); };

  function banner(msg, ok = false) {
    const el = $("#banner");
    if (!msg) { el.hidden = true; return; }
    el.textContent = msg; el.className = "banner" + (ok ? " ok" : ""); el.hidden = false;
    if (ok) setTimeout(() => (el.hidden = true), 4000);
  }

  async function load() {
    const r = await api(`/contents/${FILE}?ref=main&t=${Date.now()}`, { cache: "no-store" });
    if (!r.ok) throw new Error(`Could not load the backlog (${r.status}). Check Settings.`);
    const j = await r.json();
    sha = j.sha;
    data = JSON.parse(b64decode(j.content));
    render();
    window.ReelGenWorkflow?.update(data);
  }

  // Apply a change to the freshest copy and save; retries if the pipeline saved in between.
  async function change(mutate, message) {
    if (!token) { $("#settings").showModal(); throw new Error("Add a GitHub token in Settings first."); }
    for (let i = 0; i < 4; i++) {
      await load();
      mutate(data);
      const body = JSON.stringify(data, null, 2) + "\n";
      const r = await api(`/contents/${FILE}`, {
        method: "PUT",
        body: JSON.stringify({ message, content: b64encode(body), sha, branch: "main" }),
      });
      if (r.ok) { sha = (await r.json()).content.sha; render(); return; }
      if (r.status !== 409 && r.status !== 422) throw new Error(`Save failed (${r.status}): ${(await r.text()).slice(0, 200)}`);
      await new Promise((res) => setTimeout(res, 800 * (i + 1)));
    }
    throw new Error("Save kept conflicting with the pipeline. Try again in a minute.");
  }

  const nowIso = () => new Date().toISOString().replace(/\.\d+Z$/, "Z");
  const find = (d, id) => d.topics.find((t) => t.id === id);
  const set = (t, f) => Object.assign(t, f, { updated_at: nowIso() });
  const ago = (s) => {
    if (!s) return "";
    const m = Math.round((Date.now() - new Date(s)) / 60000);
    if (m < 60) return `${m}m ago`; if (m < 1440) return `${Math.round(m / 60)}h ago`; return `${Math.round(m / 1440)}d ago`;
  };
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  async function act(btn, fn) {
    btn && (btn.disabled = true);
    try { await fn(); } catch (e) { banner(e.message); } finally { btn && (btn.disabled = false); }
  }

  const empty = (icon, text) => `<div class="empty">${window.ReelGenCrew ? window.ReelGenCrew.icon(icon, 18) : ""}<span>${text}</span></div>`;

  function statusbar() {
    const n = (s) => data.topics.filter((t) => s.includes(t.status)).length;
    const making = data.topics.find((t) => t.status === "in_progress");
    const vault = data.topics.filter((t) => t.drive_file_id && !t.drive_deleted_at).length;
    const item = (label, value, cls = "") => `<span class="sb ${cls}"><b>${label}</b>${value}</span>`;
    $("#statusbar").innerHTML = [
      making ? item("Now rendering", esc(making.title), "live") : item("Next run", "7:47 AM"),
      item("Queue", n(["queued"])),
      item("Review", n(["ready"]), n(["ready"]) ? "gold" : ""),
      item("Publishing", n(["approved", "posting"])),
      item("Released", n(["posted"])),
      item("Vault", `${vault}/5`, vault >= 5 ? "warn" : ""),
    ].join("");
    $("#recDot").classList.toggle("on", !!making);
  }

  function render() {
    statusbar();
    const by = (s) => data.topics.filter((t) => s.includes(t.status));
    const queued = by(["queued"]).sort((a, b) => (a.order ?? 0) - (b.order ?? 0));
    const ready = by(["ready"]);
    const active = by(["in_progress", "approved", "posting"]);
    const posted = by(["posted"]).sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || ""));
    const failed = by(["failed", "rejected"]);
    [["ready", ready], ["queued", queued], ["active", active], ["posted", posted], ["failed", failed]]
      .forEach(([k, arr]) => ($(`#c-${k}`).textContent = arr.length ? `(${arr.length})` : ""));

    // waiting for approval
    const rw = $("#ready"); rw.innerHTML = "";
    if (!ready.length) rw.innerHTML = empty("approve", "No dailies to review. New cuts appear here when they're ready.");
    for (const t of ready) {
      const n = $("#readyTpl").content.cloneNode(true);
      const img = n.querySelector(".thumb");
      if (t.thumbnail) img.src = `https://raw.githubusercontent.com/${repo}/main/${t.thumbnail}`; else img.closest(".frame").remove();
      n.querySelector(".status").innerHTML = `<span class="pill ${t.test_passed ? "ok" : "warn"}">${t.test_passed ? "QC passed" : "QC flagged"}</span> <span class="hint">${esc(t.title)} · ${ago(t.finished_at)}</span>`;
      n.querySelector(".ytitle").textContent = t.youtube_title || t.title;
      n.querySelector(".caption").textContent = t.caption || "";
      n.querySelector(".tests").innerHTML = `<span class="${t.test_passed ? "pass" : "fail"}">${esc(t.test_summary || "")}</span>`;
      const w = n.querySelector(".watch");
      if (t.drive_link) w.href = t.drive_link; else w.remove();
      n.querySelector(".approve").onclick = (e) => act(e.target, () => change((d) =>
        set(find(d, t.id), { status: "approved", approved_at: nowIso() }), `Approve: ${t.title}`));
      n.querySelector(".reject").onclick = (e) => confirm("Reject this video? It will be deleted from Drive.") &&
        act(e.target, () => change((d) => set(find(d, t.id), { status: "rejected" }), `Reject: ${t.title}`));
      n.querySelector(".remake").onclick = (e) => confirm("Make this topic again from scratch? The current video will be deleted from Drive.") &&
        act(e.target, () => change((d) => {
          const old = find(d, t.id);
          set(old, { status: "rejected" });
          d.topics.push({ ...newTopic(old.title, old.notes), order: -Date.now() / 1000 });
        }, `Re-make: ${t.title}`));
      rw.appendChild(n);
    }

    // queue
    const ql = $("#queued"); ql.innerHTML = "";
    if (!queued.length) ql.innerHTML = empty("script", "The script bin is empty. Add a topic to schedule the next production.");
    queued.forEach((t, i) => {
      const li = document.createElement("li");
      li.innerHTML = `<div><div class="t">${esc(t.title)}</div><div class="meta">${esc(t.notes || "")}${t.error ? ` <span class="pill warn">retrying: ${esc(t.error.slice(0, 80))}</span>` : ""}</div></div>
        <div class="acts"><button class="ghost up" ${i === 0 ? "disabled" : ""} title="Move up">↑</button>
        <button class="ghost down" ${i === queued.length - 1 ? "disabled" : ""} title="Move down">↓</button>
        <button class="ghost top" title="Make next">Next</button>
        <button class="danger del" title="Remove">✕</button></div>`;
      const swap = (j) => (e) => act(e.target, () => change((d) => {
        const a = find(d, t.id), b = find(d, queued[j].id);
        [a.order, b.order] = [b.order, a.order];
        if (a.order === b.order) a.order += j < i ? -0.001 : 0.001;
      }, `Reorder: ${t.title}`));
      li.querySelector(".up").onclick = swap(i - 1);
      li.querySelector(".down").onclick = swap(i + 1);
      li.querySelector(".top").onclick = (e) => act(e.target, () => change((d) => {
        const min = Math.min(...d.topics.filter((x) => x.status === "queued").map((x) => x.order ?? 0));
        set(find(d, t.id), { order: min - 1 });
      }, `Move to top: ${t.title}`));
      li.querySelector(".del").onclick = (e) => confirm(`Remove "${t.title}"?`) && act(e.target, () =>
        change((d) => { d.topics = d.topics.filter((x) => x.id !== t.id); }, `Remove topic: ${t.title}`));
      ql.appendChild(li);
    });

    const simple = (el, arr, meta, extra, who = "film", quiet = "Nothing here yet.") => {
      el.innerHTML = arr.length ? "" : empty(who, quiet);
      for (const t of arr) {
        const li = document.createElement("li");
        li.innerHTML = `<div><div class="t">${esc(t.title)}</div><div class="meta">${meta(t)}</div></div><div class="acts"></div>`;
        extra && extra(t, li.querySelector(".acts"));
        el.appendChild(li);
      }
    };
    const label = { in_progress: "Rendering", approved: "Approved, waiting for the publisher", posting: "Publishing" };
    simple($("#active"), active, (t) => `<span class="pill">${label[t.status]}</span> ${ago(t.updated_at)}`, null,
      "clapper", "Nothing in production. Next run at 7:47 AM.");
    simple($("#posted"), posted, (t) => {
      const p = t.posted || {};
      const link = (k, n) => p[k + "_url"] ? `<a href="${esc(p[k + "_url"])}" target="_blank" rel="noopener">${n}</a>` : (p[k] ? n : `<s>${n}</s>`);
      return `${link("instagram", "Instagram")} · ${link("youtube", "YouTube")} · ${ago(t.updated_at)}${t.drive_deleted_at ? " · removed from Drive" : ""}`;
    }, null, "broadcast", "Nothing released yet.");
    simple($("#failed"), failed, (t) => `<span class="pill ${t.status === "failed" ? "bad" : ""}">${t.status}</span> ${esc((t.error || "").slice(0, 160))}`,
      (t, acts) => {
        const b = document.createElement("button"); b.className = "ghost"; b.textContent = "Retry";
        b.onclick = () => act(b, () => change((d) => set(find(d, t.id), { status: "queued", attempts: 0, error: null }), `Retry: ${t.title}`));
        acts.appendChild(b);
      }, "trash", "Nothing on the cutting room floor.");
  }

  function newTopic(title, notes) {
    const id = "t_" + Array.from(crypto.getRandomValues(new Uint8Array(5)), (b) => b.toString(16).padStart(2, "0")).join("");
    return { id, title: title.trim(), notes: (notes || "").trim(), status: "queued", order: Date.now() / 1000,
      created_at: nowIso(), updated_at: nowIso(), attempts: 0, error: null, posted: {} };
  }

  $("#addForm").onsubmit = (e) => {
    e.preventDefault();
    const btn = e.target.querySelector("button");
    const title = $("#title").value, notes = $("#notes").value;
    act(btn, async () => {
      await change((d) => d.topics.push(newTopic(title, notes)), `Add topic: ${title.trim()}`);
      $("#title").value = ""; $("#notes").value = "";
      banner("Added to the queue.", true);
    });
  };
  $("#workflowBtn").onclick = () => window.ReelGenWorkflow.open(data);
  const C = window.ReelGenCrew;
  if (C) document.querySelectorAll("[data-icon]").forEach((el) => (el.innerHTML = C.icon(el.dataset.icon, el.classList.contains("brand-mark") ? 26 : 16)));

  // Studio clock: local time as a 30 fps timecode.
  const pad = (n) => String(n).padStart(2, "0");
  const tick = () => {
    const d = new Date();
    $("#timecode").textContent = `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}:${pad(Math.floor(d.getMilliseconds() / 33.34))}`;
  };
  tick();
  setInterval(tick, 1000 / 10);
  $("#refresh").onclick = (e) => act(e.target, load);
  $("#settingsBtn").onclick = () => { $("#repo").value = repo; $("#token").value = token; $("#settings").showModal(); };
  $("#settingsForm").onsubmit = (e) => {
    if (e.submitter?.value !== "save") return;
    repo = $("#repo").value.trim() || defaultRepo(); token = $("#token").value.trim();
    store.set("repo", repo); store.set("token", token);
    act(null, load);
  };

  act(null, async () => {
    await load();
    if (!token) banner("Read-only view. Add a GitHub token in Settings to add topics and approve videos.");
  });
  setInterval(() => document.visibilityState === "visible" && load().catch(() => {}), 60000);
})();
