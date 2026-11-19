// "Show Workflow": a diagram of the agents and how work moves between them. Hovering (or
// tapping) an agent shows what it does and its last task. Last tasks come from the "agents"
// section of backlog/topics.json, which the pipeline and the publisher fill in as they run.
(() => {
  const WHERE = {
    you: { label: "You", color: "var(--amber)" },
    cloud: { label: "Daily Claude session, 7:47 AM", color: "var(--teal)" },
    google: { label: "Google Drive", color: "#60a5fa" },
    laptop: { label: "Your laptop, 10 AM and 7 PM", color: "var(--violet)" },
    social: { label: "Social accounts", color: "#f472b6" },
  };

  // Main flow, in order. The drive keeper is a helper that hangs off Google Drive.
  const NODES = [
    { id: "you_add", name: "You: add topics", where: "you",
      does: "You add topics in this dashboard and put them in order. The top of the queue is made each morning." },
    { id: "collaborator", name: "Collaborator", where: "cloud",
      does: "The orchestrator. Each morning it picks the top queued topic, hands the work from agent to agent, and puts the topic back in the queue (or marks it failed) if something breaks." },
    { id: "researcher", name: "Researcher", where: "cloud",
      does: "Researches the topic on the web: a plain-English definition, the problem it solves, how it works, key facts with sources, analogies and common misconceptions." },
    { id: "scripter", name: "Scripter", where: "cloud",
      does: "Turns the research into a 30-second narration (5 lines, about 70 words), plus the Instagram caption, hashtags and YouTube title. Spells hard words the way the voice should say them." },
    { id: "director", name: "Director", where: "cloud",
      does: "Designs the infographic: the text, icons and layout of the five animated scenes (hook, problem, definition, steps, payoff)." },
    { id: "sound_engineer", name: "Sound engineer", where: "cloud",
      does: "Records each line with Google Text-to-Speech (Chirp 3 HD voice), using the pronunciation dictionary." },
    { id: "editor", name: "Editor", where: "cloud",
      does: "Renders the 1080x1920 animation, times each scene to its line, fits the video to exactly 30 seconds and sets the loudness for Reels and Shorts." },
    { id: "tester", name: "Tester", where: "cloud",
      does: "Listens back with Google Speech-to-Text. Checks the narration matches the script, words are pronounced right, pacing and pauses, length, resolution and loudness. Mispronounced words go back to the sound engineer with a new spelling." },
    { id: "drive", name: "Google Drive", where: "google",
      does: "The finished video, its caption and test results are uploaded here to wait for you. Drive holds at most 5 videos." },
    { id: "you_approve", name: "You: approve", where: "you",
      does: "You watch the video from this dashboard and click Approve, Re-make or Reject. Nothing is posted without your Approve." },
    { id: "publisher", name: "Publisher", where: "laptop",
      does: "Runs on your laptop. Downloads approved videos from Drive and posts them with their captions to YouTube Shorts and Instagram Reels, using Chrome." },
    { id: "socials", name: "Instagram & YouTube", where: "social",
      does: "The channel's Instagram Reels and YouTube Shorts accounts, where the videos go live." },
  ];
  const KEEPER = { id: "drive_keeper", name: "Drive keeper", where: "cloud",
    does: "Cleans up Drive at the start of each run. Deletes a video 3 days after it is posted to both sites, deletes rejected videos right away, and pauses production rather than delete anything you have not approved." };

  const $ = (s, r = document) => r.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const ago = (s) => {
    if (!s) return "";
    const m = Math.max(0, Math.round((Date.now() - new Date(s)) / 60000));
    if (m < 1) return "just now"; if (m < 60) return `${m}m ago`; if (m < 1440) return `${Math.round(m / 60)}h ago`;
    return `${Math.round(m / 1440)}d ago`;
  };
  const latest = (arr, key) => arr.filter((t) => t[key]).sort((a, b) => b[key].localeCompare(a[key]))[0];
  const postedAt = (t) => [t.posted?.instagram, t.posted?.youtube].filter(Boolean).sort().pop();

  let data = { topics: [] };

  // Last task and current state of every agent.
  function activity() {
    const topics = data.topics || [];
    const rec = { ...(data.agents || {}) };
    const out = {};
    for (const n of [...NODES, KEEPER]) out[n.id] = { last: rec[n.id] || null, now: null };

    const added = latest(topics, "created_at");
    if (added) out.you_add.last = { task: "Added a topic to the queue.", topic: added.title, at: added.created_at, ok: true };
    const appr = latest(topics, "approved_at");
    if (appr) out.you_approve.last = { task: "Approved a video for posting.", topic: appr.title, at: appr.approved_at, ok: true };
    const posted = topics.filter(postedAt).sort((a, b) => postedAt(b).localeCompare(postedAt(a)))[0];
    if (posted) {
      const sites = [posted.posted.youtube && "YouTube", posted.posted.instagram && "Instagram"].filter(Boolean).join(" and ");
      out.socials.last = { task: `Went live on ${sites}.`, topic: posted.title, at: postedAt(posted), ok: true,
        url: posted.posted.youtube_url };
    }

    const making = topics.find((t) => t.status === "in_progress");
    if (making) out.collaborator.now = `Working on "${making.title}" now.`;
    const queued = topics.filter((t) => t.status === "queued").length;
    out.you_add.now = queued ? `${queued} topic${queued > 1 ? "s" : ""} in the queue.` : "The queue is empty. Add a topic.";
    const ready = topics.filter((t) => t.status === "ready").length;
    if (ready) out.you_approve.now = `${ready} video${ready > 1 ? "s" : ""} waiting for you.`;
    const toPost = topics.filter((t) => ["approved", "posting"].includes(t.status)).length;
    if (toPost) out.publisher.now = `${toPost} approved video${toPost > 1 ? "s" : ""} to post on the next run.`;
    const inDrive = topics.filter((t) => t.drive_file_id && !t.drive_deleted_at).length;
    out.drive.now = `${inDrive} of 5 video slots in use.`;
    return out;
  }

  function summary(act) {
    const parts = [];
    if (act.collaborator.now) parts.push(act.collaborator.now);
    if (act.you_approve.now) parts.push(act.you_approve.now);
    if (act.publisher.now) parts.push(act.publisher.now);
    if (!parts.length) parts.push((data.topics || []).some((t) => t.status === "queued")
      ? "Idle. The next video is made at 7:47 AM." : "Idle. Add a topic so tomorrow's run has something to make.");
    return parts.join(" ");
  }

  // ---- layout ----
  const NODE_H = 92, ROW_GAP = 46, COL_GAP = 34, MARGIN = 26, TOP = 8;

  function layout(width) {
    const cols = width >= 760 ? 4 : 2;
    const nw = (width - MARGIN * 2 - COL_GAP * (cols - 1)) / cols;
    const pos = {};
    NODES.forEach((n, i) => {
      const row = Math.floor(i / cols), k = i % cols, col = row % 2 ? cols - 1 - k : k;
      pos[n.id] = { row, col };
    });
    const rows = Math.ceil(NODES.length / cols);
    const d = pos.drive;
    const taken = NODES.some((n) => pos[n.id].row === d.row + 1 && pos[n.id].col === d.col);
    pos[KEEPER.id] = { row: taken ? rows : d.row + 1, col: d.col };
    const totalRows = Math.max(rows, pos[KEEPER.id].row + 1);
    for (const p of Object.values(pos)) {
      p.x = MARGIN + p.col * (nw + COL_GAP); p.y = TOP + p.row * (NODE_H + ROW_GAP); p.w = nw; p.h = NODE_H;
      p.cx = p.x + nw / 2; p.cy = p.y + NODE_H / 2;
    }
    return { pos, height: TOP + totalRows * (NODE_H + ROW_GAP) - ROW_GAP + 14 };
  }

  function edges(pos) {
    const out = [];
    const arrow = (d, cls = "") => out.push(`<path d="${d}" class="edge ${cls}" marker-end="url(#wfArrow${cls ? "D" : ""})"/>`);
    const label = (x, y, text) => out.push(`<text x="${x}" y="${y}" class="edge-label" text-anchor="middle">${text}</text>`);
    for (let i = 0; i < NODES.length - 1; i++) {
      const a = pos[NODES[i].id], b = pos[NODES[i + 1].id];
      if (a.row === b.row) {
        const dir = b.col > a.col ? 1 : -1;
        const x1 = dir > 0 ? a.x + a.w : a.x, x2 = dir > 0 ? b.x - 4 : b.x + b.w + 4;
        arrow(`M${x1},${a.cy} L${x2},${b.cy}`);
      } else {
        arrow(`M${a.cx},${a.y + a.h} L${b.cx},${b.y - 4}`);
      }
    }
    // Tester sends mispronounced lines back to the sound engineer.
    const t = pos.tester, s = pos.sound_engineer;
    if (t.row === s.row) {
      const y = t.y + t.h, dip = ROW_GAP * 0.62;
      arrow(`M${t.cx + 14},${y} C${t.cx + 14},${y + dip} ${s.cx - 14},${y + dip} ${s.cx - 14},${y + 5}`, "dashed");
      label((t.cx + s.cx) / 2, y + dip - 2, "re-record a line");
    } else {
      const x1 = t.x + t.w * 0.75, y1 = t.y, x2 = s.x + s.w * 0.25, y2 = s.y + s.h + 5;
      arrow(`M${x1},${y1} C${x1},${y1 - 26} ${x2},${y2 + 26} ${x2},${y2}`, "dashed");
      label((x1 + x2) / 2, (y1 + y2) / 2 + 4, "re-record");
    }
    // Drive keeper cleans up Drive.
    const k = pos.drive_keeper, d = pos.drive;
    if (k.row === d.row + 1 && k.col === d.col) {
      arrow(`M${k.cx + 30},${k.y} L${d.cx + 30},${d.y + d.h + 5}`, "dashed");
      label(k.cx + 30, k.y - ROW_GAP / 2 + 4, "cleans up");
    } else {
      const xm = MARGIN / 2;
      arrow(`M${k.x},${k.cy} L${xm},${k.cy} L${xm},${d.cy} L${d.x - 5},${d.cy}`, "dashed");
    }
    return out.join("");
  }

  function nodeHtml(n, p, a) {
    const w = WHERE[n.where];
    const last = a.last;
    const state = a.now && /waiting for you|Working on/.test(a.now) ? " live" : "";
    const bad = last && last.ok === false ? " bad" : "";
    const status = a.now && state ? esc(a.now) : last ? `Last task ${ago(last.at)}` : "No activity yet";
    return `<button type="button" class="wf-node${state}${bad}" data-id="${n.id}" aria-describedby="wfTip"
      style="left:${p.x}px;top:${p.y}px;width:${p.w}px;height:${p.h}px;--c:${w.color}">
      <span class="wf-name">${esc(n.name)}</span>
      <span class="wf-status">${status}</span></button>`;
  }

  function tipHtml(n, a) {
    const last = a.last;
    const lastHtml = last
      ? `<div class="tip-last${last.ok === false ? " bad" : ""}"><b>Last task</b> · ${esc(ago(last.at))}<br>${esc(last.task)}
         ${last.topic ? `<br><span class="hint">Topic: ${esc(last.topic)}</span>` : ""}</div>`
      : `<div class="tip-last"><b>Last task</b><br><span class="hint">Nothing yet. This fills in after the first run.</span></div>`;
    return `<div class="tip-where" style="color:${WHERE[n.where].color}">${esc(WHERE[n.where].label)}</div>
      <div class="tip-name">${esc(n.name)}</div><p>${esc(n.does)}</p>
      ${a.now ? `<div class="tip-now">${esc(a.now)}</div>` : ""}${lastHtml}`;
  }

  function render() {
    const dlg = $("#workflow");
    if (!dlg || !dlg.open) return;
    const box = $("#wf"), tip = $("#wfTip");
    const width = box.clientWidth;
    if (!width) return;
    const act = activity();
    const { pos, height } = layout(width);
    $("#wfNow").textContent = summary(act);
    box.style.height = height + "px";
    box.innerHTML = `<svg class="wf-edges" width="${width}" height="${height}" aria-hidden="true">
      <defs>
        <marker id="wfArrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="arrow-head"/></marker>
        <marker id="wfArrowD" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="arrow-head dashed"/></marker>
      </defs>${edges(pos)}</svg>`
      + [...NODES, KEEPER].map((n) => nodeHtml(n, pos[n.id], act[n.id])).join("");

    const byId = Object.fromEntries([...NODES, KEEPER].map((n) => [n.id, n]));
    const show = (el) => {
      const n = byId[el.dataset.id];
      tip.innerHTML = tipHtml(n, act[n.id]);
      tip.hidden = false;
      const r = el.getBoundingClientRect(), dr = dlg.getBoundingClientRect();
      const tw = Math.min(320, dr.width - 24);
      tip.style.width = tw + "px";
      let left = r.left - dr.left + r.width / 2 - tw / 2;
      left = Math.max(12, Math.min(left, dr.width - tw - 12));
      let top = r.bottom - dr.top + dlg.scrollTop + 8;
      if (r.bottom + tip.offsetHeight + 16 > window.innerHeight && r.top - tip.offsetHeight - 8 > dr.top) {
        top = r.top - dr.top + dlg.scrollTop - tip.offsetHeight - 8;
      }
      tip.style.left = left + "px"; tip.style.top = top + "px";
    };
    const hide = () => { tip.hidden = true; };
    box.querySelectorAll(".wf-node").forEach((el) => {
      el.addEventListener("mouseenter", () => show(el));
      el.addEventListener("mouseleave", () => document.activeElement !== el && hide());
      el.addEventListener("focus", () => show(el));
      el.addEventListener("blur", hide);
      el.addEventListener("click", () => show(el));
    });
  }

  window.ReelGenWorkflow = {
    open(d) {
      data = d || data;
      const dlg = $("#workflow");
      $("#wfTip").hidden = true;
      dlg.showModal();
      render();
    },
    update(d) { data = d || data; render(); },
  };

  let lastW = 0;
  window.addEventListener("resize", () => {
    const w = $("#wf")?.clientWidth || 0;
    if (w !== lastW) { lastW = w; $("#wfTip").hidden = true; render(); }
  });
})();
