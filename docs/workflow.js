// "Show Workflow": the crew drawn as a neural network. Each agent is a neuron, the
// main hand-offs carry travelling signal pulses, and faint synapses link neighbouring layers.
// Hovering (or tapping) an agent shows what it does and its last task. Last tasks come from the
// "agents" section of backlog/topics.json, which the pipeline and the publisher fill in as they run.
(() => {
  const crew = () => window.ReelGenCrew;
  const WHERE = {
    you: { label: "You", color: "#f2c230" },
    cloud: { label: "Daily Claude session, 7:47 AM", color: "#c3c9d2" },
    google: { label: "Google Drive", color: "#6f97c9" },
    laptop: { label: "Your laptop, 10 AM and 7 PM", color: "#c08a4a" },
    social: { label: "Social accounts", color: "#c4524f" },
  };

  const AGENTS = {
    you_add: { where: "you", does: "You add topics in this dashboard and put them in order. The top of the queue is made each morning." },
    collaborator: { where: "cloud", does: "The orchestrator. Each morning Harper picks the top queued topic, hands the work from agent to agent, and puts the topic back in the queue (or marks it failed) if something breaks." },
    researcher: { where: "cloud", step: 1, does: "Researches the topic on the web: a plain-English definition, the problem it solves, how it works, key facts with sources, analogies and common misconceptions." },
    scripter: { where: "cloud", step: 2, does: "Turns the research into a 30-second narration (5 lines, about 70 words), plus the Instagram caption, hashtags and YouTube title. Spells hard words the way the voice should say them." },
    director: { where: "cloud", step: 3, does: "Designs the infographic: the text, icons and layout of the five animated scenes (hook, problem, definition, steps, payoff)." },
    sound_engineer: { where: "cloud", step: 4, does: "Records each line with Google Text-to-Speech (Chirp 3 HD voice), using the pronunciation dictionary." },
    editor: { where: "cloud", step: 5, does: "Renders the 1080x1920 animation, times each scene to its line, fits the video to exactly 30 seconds and sets the loudness for Reels and Shorts." },
    tester: { where: "cloud", step: 6, does: "Listens back with Google Speech-to-Text. Checks the narration matches the script, words are pronounced right, pacing and pauses, length, resolution and loudness. Mispronounced words go back to Miles with a new spelling." },
    drive: { where: "google", step: 7, does: "The finished video, its caption and test results are uploaded to Google Drive to wait for you. Drive holds at most 5 videos." },
    drive_keeper: { where: "cloud", does: "Cleans up Drive at the start of each run. Deletes a video 3 days after it is posted to both sites, deletes rejected videos right away, and pauses production rather than delete anything you have not approved." },
    you_approve: { where: "you", step: 8, does: "You watch the video from this dashboard and click Approve, Re-make or Reject. Nothing is posted without your Approve." },
    publisher: { where: "laptop", step: 9, does: "Runs on your laptop. Downloads approved videos from Drive and posts them with their captions to YouTube Shorts and Instagram Reels, using Chrome." },
    socials: { where: "social", step: 10, does: "The channel's Instagram Reels and YouTube Shorts accounts, where the videos go live." },
  };

  // Network layers, input to output.
  const LAYERS = [["you_add"], ["collaborator"], ["researcher", "scripter", "director"],
    ["sound_engineer", "editor", "tester"], ["drive", "drive_keeper"], ["you_approve"], ["publisher"], ["socials"]];
  // Main hand-offs (these carry signal pulses), then loops.
  const FLOW = [["you_add", "collaborator"], ["collaborator", "researcher"], ["researcher", "scripter"],
    ["scripter", "director"], ["director", "sound_engineer"], ["sound_engineer", "editor"], ["editor", "tester"],
    ["tester", "drive"], ["drive", "you_approve"], ["you_approve", "publisher"], ["publisher", "socials"]];
  // Loops: the tester sends mispronounced lines back; the drive keeper cleans up Drive.
  const LOOPS = [["tester", "sound_engineer"], ["drive_keeper", "drive"]];
  // Where each node sits in its layer, in grid steps from the middle (2-node layers hang down).
  const slot = (n, j) => (n === 2 ? j : j - (n - 1) / 2);

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
  const reduced = () => window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

  let data = { topics: [] };

  // Last task and current state of every agent.
  function activity() {
    const topics = data.topics || [];
    const rec = data.agents || {};
    const out = {};
    for (const id of Object.keys(AGENTS)) out[id] = { last: rec[id] || null, now: null, live: false };

    const added = latest(topics, "created_at");
    if (added) out.you_add.last = { task: "Added a topic to the queue.", topic: added.title, at: added.created_at, ok: true };
    const appr = latest(topics, "approved_at");
    if (appr) out.you_approve.last = { task: "Approved a video for posting.", topic: appr.title, at: appr.approved_at, ok: true };
    const posted = topics.filter(postedAt).sort((a, b) => postedAt(b).localeCompare(postedAt(a)))[0];
    if (posted) {
      const sites = [posted.posted.youtube && "YouTube", posted.posted.instagram && "Instagram"].filter(Boolean).join(" and ");
      out.socials.last = { task: `Went live on ${sites}.`, topic: posted.title, at: postedAt(posted), ok: true };
    }

    const making = topics.find((t) => t.status === "in_progress");
    if (making) Object.assign(out.collaborator, { now: `In production: "${making.title}".`, live: true });
    const queued = topics.filter((t) => t.status === "queued").length;
    out.you_add.now = queued ? `${queued} topic${queued > 1 ? "s" : ""} in the queue.` : "The queue is empty. Add a topic.";
    const ready = topics.filter((t) => t.status === "ready").length;
    if (ready) Object.assign(out.you_approve, { now: `${ready} cut${ready > 1 ? "s" : ""} waiting for your review.`, live: true });
    const toPost = topics.filter((t) => ["approved", "posting"].includes(t.status)).length;
    if (toPost) Object.assign(out.publisher, { now: `${toPost} approved video${toPost > 1 ? "s" : ""} to publish on the next run.`, live: true });
    const inDrive = topics.filter((t) => t.drive_file_id && !t.drive_deleted_at).length;
    out.drive.now = `${inDrive} of 5 video slots in use.`;
    return out;
  }

  function summary(act) {
    const parts = [act.collaborator.now, act.you_approve.now, act.publisher.now].filter(Boolean);
    if (!parts.length) parts.push((data.topics || []).some((t) => t.status === "queued")
      ? "Standing by. Next production run at 7:47 AM." : "The queue is empty. Add a topic for the next run at 7:47 AM.");
    return parts.join(" ");
  }

  // ---- layout ----
  function layout(width) {
    const wide = width >= 760;
    const pos = {};
    if (wide) {
      const r = 34, padX = 70, gapY = 138, h = 3 * gapY + 30;
      LAYERS.forEach((layer, i) => {
        const x = padX + (i * (width - 2 * padX)) / (LAYERS.length - 1);
        layer.forEach((id, j) => { pos[id] = { x, y: h / 2 + slot(layer.length, j) * gapY - 6, r, layer: i }; });
      });
      return { pos, height: h, wide, labelW: Math.min(128, (width - 2 * padX) / (LAYERS.length - 1) + 6) };
    }
    const r = 28, padY = 46, gapY = 132;
    LAYERS.forEach((layer, i) => {
      const y = padY + i * gapY;
      layer.forEach((id, j) => { pos[id] = { x: width / 2 + slot(layer.length, j) * Math.min(118, width / 3), y, r, layer: i }; });
    });
    return { pos, height: padY + (LAYERS.length - 1) * gapY + 70, wide, labelW: Math.min(112, width / 3 - 4) };
  }

  // Path between two neurons, trimmed to their rims. Same-layer links curve around the side.
  function link(a, b, wide, bend = 0) {
    if (a.layer === b.layer && wide) {
      const side = bend < 0 ? -1 : 1; bend = Math.abs(bend);
      const v = b.y > a.y ? 1 : -1;
      const x1 = a.x + a.r * 0.8 * side, y1 = a.y + a.r * 0.6 * v, x2 = b.x + b.r * 0.8 * side, y2 = b.y - b.r * 0.6 * v;
      const cx = a.x + (a.r + 46 + bend) * side;
      return `M${x1},${y1} C${cx},${y1 + 20 * v} ${cx},${y2 - 20 * v} ${x2},${y2}`;
    }
    const dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy) || 1;
    const x1 = a.x + (dx / d) * (a.r + 4), y1 = a.y + (dy / d) * (a.r + 4);
    const x2 = b.x - (dx / d) * (b.r + 7), y2 = b.y - (dy / d) * (b.r + 7);
    if (!bend) return `M${x1},${y1} L${x2},${y2}`;
    const mx = (x1 + x2) / 2 - (dy / d) * bend, my = (y1 + y2) / 2 + (dx / d) * bend;
    return `M${x1},${y1} Q${mx},${my} ${x2},${y2}`;
  }

  function svg(pos, wide, width, height) {
    const out = [];
    // faint synapses between neighbouring layers
    const flowKey = new Set(FLOW.map(([a, b]) => a + ">" + b));
    for (let i = 0; i < LAYERS.length - 1; i++) {
      for (const a of LAYERS[i]) for (const b of LAYERS[i + 1]) {
        if (!flowKey.has(a + ">" + b)) out.push(`<path d="${link(pos[a], pos[b], wide)}" class="syn"/>`);
      }
    }
    // main hand-offs with travelling pulses
    FLOW.forEach(([a, b], i) => {
      const d = link(pos[a], pos[b], wide);
      out.push(`<path d="${d}" class="flow" marker-end="url(#nnArrow)"/>`);
      if (!reduced()) {
        out.push(`<circle r="4" class="pulse"><animateMotion dur="1.6s" begin="-${((FLOW.length - i) * 0.45).toFixed(2)}s" repeatCount="indefinite" path="${d}"/></circle>`);
      }
    });
    // loops
    for (const [a, b] of LOOPS) {
      const A = pos[a], B = pos[b];
      // Skip over any neuron in between: arc well clear of it.
      const far = Math.abs(A.x - B.x) > 1.5 * Math.min(118, width / 3);
      const bend = wide ? (a === "drive_keeper" ? -6 : 30) : far ? 84 : 26;
      out.push(`<path d="${link(A, B, wide, bend)}" class="loop" marker-end="url(#nnArrowLoop)"/>`);
    }
    return `<svg class="nn-edges" width="${width}" height="${height}" aria-hidden="true">
      <defs>
        <marker id="nnArrow" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#f2c230"/></marker>
        <marker id="nnArrowLoop" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#8b929c"/></marker>
        <filter id="nnGlow" filterUnits="userSpaceOnUse" x="-50" y="-50" width="${width + 100}" height="${height + 100}"><feGaussianBlur stdDeviation="2.5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>${out.join("")}</svg>`;
  }

  function nodeHtml(id, p, a, labelW) {
    const P = crew().PERSONAS[id], A = AGENTS[id], c = WHERE[A.where].color;
    const bad = a.last && a.last.ok === false;
    const status = a.live ? a.now : a.last ? `${bad ? "Trouble" : "Last task"} ${ago(a.last.at)}` : "Standing by";
    return `<button type="button" class="neuron${a.live ? " live" : ""}${bad ? " bad" : ""}" data-id="${id}"
      style="left:${p.x - labelW / 2}px;top:${p.y - p.r}px;width:${labelW}px;--c:${c};--d:${p.r * 2}px" aria-describedby="wfTip">
      <span class="orb">${crew().avatar(id, p.r * 2)}${A.step ? `<span class="step">${A.step}</span>` : ""}</span>
      <span class="n-name">${esc(P.name)}</span><span class="n-role">${esc(P.role)}</span>
      <span class="n-status">${esc(status)}</span></button>`;
  }

  function tipHtml(id, a) {
    const P = crew().PERSONAS[id], A = AGENTS[id], w = WHERE[A.where];
    const last = a.last;
    const lastHtml = last
      ? `<div class="tip-last${last.ok === false ? " bad" : ""}"><b>Last task</b> · ${esc(ago(last.at))}<br>${esc(last.task)}
         ${last.topic ? `<br><span class="tip-topic">Topic: ${esc(last.topic)}</span>` : ""}</div>`
      : `<div class="tip-last"><b>Last task</b><br><span class="tip-topic">Nothing yet. This fills in after the first run.</span></div>`;
    return `<div class="tip-head">${crew().avatar(id, 44)}<div><div class="tip-name">${esc(P.name)}</div>
        <div class="tip-where" style="color:${w.color}">${esc(P.role)} · ${esc(w.label)}</div></div></div>
      <p>${esc(A.does)}</p>${a.now ? `<div class="tip-now">${esc(a.now)}</div>` : ""}${lastHtml}`;
  }

  function render() {
    const dlg = $("#workflow");
    if (!dlg || !dlg.open || !crew()) return;
    const box = $("#wf"), tip = $("#wfTip");
    const width = box.clientWidth;
    if (!width) return;
    const act = activity();
    const { pos, height, wide, labelW } = layout(width);
    $("#wfNowText").textContent = summary(act);
    $("#wfNowAvatar").innerHTML = crew().icon(act.collaborator.live ? "rec" : "film", 18);
    $("#wfNowAvatar").className = act.collaborator.live ? "rec on" : "rec";
    box.style.height = height + "px";
    box.innerHTML = svg(pos, wide, width, height)
      + Object.keys(AGENTS).map((id) => nodeHtml(id, pos[id], act[id], labelW)).join("");

    const show = (el) => {
      const id = el.dataset.id;
      tip.innerHTML = tipHtml(id, act[id]);
      tip.hidden = false;
      const r = el.querySelector(".orb").getBoundingClientRect(), dr = dlg.getBoundingClientRect();
      const tw = Math.min(330, dr.width - 24);
      tip.style.width = tw + "px";
      let left = r.left - dr.left + r.width / 2 - tw / 2;
      left = Math.max(12, Math.min(left, dr.width - tw - 12));
      let top = r.bottom - dr.top + dlg.scrollTop + 64;
      if (r.bottom + 64 + tip.offsetHeight + 12 > window.innerHeight && r.top - tip.offsetHeight - 12 > dr.top) {
        top = r.top - dr.top + dlg.scrollTop - tip.offsetHeight - 12;
      }
      tip.style.left = left + "px"; tip.style.top = top + "px";
    };
    const hide = () => { tip.hidden = true; };
    box.querySelectorAll(".neuron").forEach((el) => {
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
      $("#wfTip").hidden = true;
      $("#workflow").showModal();
      render();
    },
    update(d) { data = d || data; render(); },
    summary(d) { data = d || data; return summary(activity()); },
  };

  let lastW = 0;
  window.addEventListener("resize", () => {
    const w = $("#wf")?.clientWidth || 0;
    if (w !== lastW) { lastW = w; $("#wfTip").hidden = true; render(); }
  });
})();
