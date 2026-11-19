// The ReelGen crew: an original anime persona for each agent, drawn as inline SVG chibi avatars.
(() => {
  const INK = "#1b1530";
  const SKIN = "#ffe3cc";

  const PERSONAS = {
    you_add: { name: "Senpai", role: "You · Topic boss", line: "Make a video about THIS!",
      look: { bg: "#ffd23f", hair: "#3a2a4d", style: "short", eyes: "happy", mouth: "open", acc: ["crown"], shirt: "#ff4d8d" } },
    collaborator: { name: "Captain Rin", role: "Collaborator", line: "Everyone, assemble! Today's topic is in!",
      look: { bg: "#ff8fab", hair: "#e2363f", style: "ponytail", eyes: "normal", mouth: "smile", brows: "determined", acc: ["headset"], shirt: "#1b1530" } },
    researcher: { name: "Prof. Kumo", role: "Researcher", line: "According to my six sources...",
      look: { bg: "#b9a5ff", hair: "#6b4fd8", style: "messy", eyes: "normal", mouth: "smile", acc: ["glasses"], shirt: "#ffffff" } },
    scripter: { name: "Hana", role: "Scripter", line: "Seventy words. Not. One. More.",
      look: { bg: "#ffc2d6", hair: "#ff5c9a", style: "bob", eyes: "normal", mouth: "smile", acc: ["pen"], shirt: "#22d3ee" } },
    director: { name: "Taro", role: "Director", line: "Make it POP! More icons!",
      look: { bg: "#ffe680", hair: "#ffb800", style: "spiky", eyes: "sparkle", mouth: "open", acc: ["beret"], shirt: "#ff6b3d" } },
    sound_engineer: { name: "DJ Sora", role: "Sound engineer", line: "Mic check... Kubernetes. KOO-ber-NET-eez!",
      look: { bg: "#8ff0e6", hair: "#14b8a6", style: "short", eyes: "wink", mouth: "smile", acc: ["headphones"], shirt: "#6b4fd8" } },
    editor: { name: "Kenji", role: "Editor", line: "Thirty point zero zero seconds. Perfect.",
      look: { bg: "#9ecbff", hair: "#1e3a8a", style: "spiky", eyes: "normal", mouth: "smirk", brows: "determined", acc: ["band"], shirt: "#ffd23f" } },
    tester: { name: "Detective Yuki", role: "Tester", line: "Hmm... that word sounded sus.",
      look: { bg: "#d6dcff", hair: "#c9cfe8", style: "bob", eyes: "squint", mouth: "flat", brows: "suspicious", acc: ["cap"], shirt: "#8b5e3c" } },
    drive: { name: "Kura", role: "Google Drive spirit", line: "I'll keep your videos safe~ (five max!)",
      look: { bg: "#bfe0ff", mascot: "cloud" } },
    drive_keeper: { name: "Grandpa Sweep", role: "Drive keeper", line: "Posted three days ago? Into the bin!",
      look: { bg: "#d9f99d", hair: "#f4f4f5", style: "bald", eyes: "happy", mouth: "mustache", acc: [], shirt: "#4d7c0f" } },
    you_approve: { name: "Senpai", role: "You · Final boss", line: "Approved! Ship it!",
      look: { bg: "#ffd23f", hair: "#3a2a4d", style: "short", eyes: "sparkle", mouth: "open", acc: ["crown"], shirt: "#ff4d8d" } },
    publisher: { name: "Neko Express", role: "Publisher", line: "Delivery for Instagram, nya!",
      look: { bg: "#ffd0a8", mascot: "cat" } },
    socials: { name: "The Fans", role: "Instagram & YouTube", line: "SUGOI!! Liked and subscribed!",
      look: { bg: "#ffb3d1", mascot: "heart" } },
  };

  const s = (attrs) => Object.entries(attrs).map(([k, v]) => `${k}="${v}"`).join(" ");
  const line = { stroke: INK, "stroke-width": 2.2, "stroke-linecap": "round", "stroke-linejoin": "round" };

  function eyes(kind, color = INK) {
    const one = (x, k) => {
      if (k === "happy") return `<path d="M${x - 4.5},55 Q${x},48.5 ${x + 4.5},55" fill="none" ${s({ ...line, "stroke-width": 2.6 })}/>`;
      if (k === "squint") return `<path d="M${x - 5},53 L${x + 5},53" ${s({ ...line, "stroke-width": 3 })}/>
        <circle cx="${x}" cy="54.5" r="2" fill="${color}"/>`;
      const sparkle = k === "sparkle"
        ? `<path d="M${x + 1.5},48.5 l0.9,2 2,0.9 -2,0.9 -0.9,2 -0.9,-2 -2,-0.9 2,-0.9z" fill="#fff"/>` : "";
      return `<ellipse cx="${x}" cy="53.5" rx="4.4" ry="5.8" fill="${color}"/>
        <ellipse cx="${x}" cy="56.5" rx="3" ry="2.4" fill="#5b4b8a" opacity=".7"/>
        <circle cx="${x + 1.5}" cy="50.8" r="1.8" fill="#fff"/><circle cx="${x - 1.6}" cy="56.6" r=".9" fill="#fff"/>${sparkle}`;
    };
    if (kind === "wink") return one(41, "happy") + one(59, "normal");
    return one(41, kind) + one(59, kind);
  }

  function brows(kind) {
    if (kind === "determined") return `<path d="M36,45 L45,47.5 M64,45 L55,47.5" ${s(line)}/>`;
    if (kind === "suspicious") return `<path d="M36,46 L45,46 M55,44 L64,47" ${s(line)}/>`;
    return "";
  }

  function mouth(kind) {
    switch (kind) {
      case "open": return `<path d="M45,63 Q50,72 55,63 Z" fill="#9b2c4a" ${s(line)}/><path d="M47.5,67 Q50,69.5 52.5,67" fill="#ff8fab"/>`;
      case "smirk": return `<path d="M46,65 Q51,67 55,62.5" fill="none" ${s(line)}/>`;
      case "flat": return `<path d="M46.5,65 L53.5,64" fill="none" ${s(line)}/>`;
      case "mustache": return `<path d="M40,63 Q45,59 50,62.5 Q55,59 60,63 Q55,67.5 50,64.5 Q45,67.5 40,63 Z" fill="#f4f4f5" ${s({ ...line, "stroke-width": 1.6 })}/>`;
      default: return `<path d="M46,64 Q50,68 54,64" fill="none" ${s(line)}/>`;
    }
  }

  function hairBack(style, c) {
    if (style === "bob") return `<path d="M23,52 Q21,22 50,21 Q79,22 77,52 L78,72 Q71,77 67,68 L33,68 Q29,77 22,72 Z" fill="${c}" ${s(line)}/>`;
    if (style === "ponytail") return `<path d="M70,32 Q96,36 88,74 Q84,64 74,58 Z" fill="${c}" ${s(line)}/>`;
    return "";
  }

  function hairFront(style, c) {
    switch (style) {
      case "spiky": return `<path d="M24,54 L19,38 L29,41 L27,26 L38,33 L42,17 L50,30 L59,17 L62,32 L73,26 L71,41 L81,38 L76,54 Q73,39 50,38 Q27,39 24,54 Z" fill="${c}" ${s(line)}/>`;
      case "bob": return `<path d="M26,50 Q28,26 50,25 Q72,26 74,50 Q66,38 58,42 Q52,34 46,42 Q37,36 26,50 Z" fill="${c}" ${s(line)}/>`;
      case "ponytail": return `<path d="M25,52 Q24,24 50,23 Q76,24 75,52 Q70,36 60,38 L56,44 L52,37 Q38,36 25,52 Z" fill="${c}" ${s(line)}/>`;
      case "messy": return `<path d="M24,54 Q18,40 26,34 Q24,22 38,22 Q44,13 54,19 Q66,14 70,26 Q82,30 76,54 Q74,40 64,42 L60,36 L55,43 L49,35 L44,43 L38,37 Q28,40 24,54 Z" fill="${c}" ${s(line)}/>`;
      case "bald": return `<path d="M25,56 Q20,46 27,40 Q28,48 30,52 Z M75,56 Q80,46 73,40 Q72,48 70,52 Z" fill="${c}" ${s({ ...line, "stroke-width": 1.6 })}/>
        <path d="M37,44 Q41,41 45,44 M55,44 Q59,41 63,44" fill="none" stroke="#e4e4e7" stroke-width="3.2" stroke-linecap="round"/>`;
      default: return `<path d="M25,52 Q24,24 50,23 Q76,24 75,52 Q72,38 62,40 L58,34 L52,40 L46,34 L40,40 Q29,38 25,52 Z" fill="${c}" ${s(line)}/>`;
    }
  }

  function accessory(a) {
    switch (a) {
      case "glasses": return `<g fill="#fff" fill-opacity=".25" ${s(line)}><circle cx="41" cy="54" r="7.5"/><circle cx="59" cy="54" r="7.5"/></g>
        <path d="M48.5,53 Q50,51.5 51.5,53 M33.5,52 L26,49 M66.5,52 L74,49" fill="none" ${s(line)}/>`;
      case "headphones": return `<path d="M22,52 Q20,16 50,15 Q80,16 78,52" fill="none" stroke="${INK}" stroke-width="6" stroke-linecap="round"/>
        <path d="M22,52 Q20,16 50,15 Q80,16 78,52" fill="none" stroke="#ff4d8d" stroke-width="3" stroke-linecap="round"/>
        <rect x="15" y="44" width="11" height="18" rx="4" fill="#ff4d8d" ${s(line)}/><rect x="74" y="44" width="11" height="18" rx="4" fill="#ff4d8d" ${s(line)}/>`;
      case "headset": return `<rect x="17" y="46" width="9" height="15" rx="4" fill="#ffd23f" ${s(line)}/>
        <path d="M22,60 Q24,72 38,71" fill="none" ${s({ ...line, "stroke-width": 2.6 })}/><circle cx="40" cy="71" r="3" fill="#ffd23f" ${s(line)}/>`;
      case "beret": return `<path d="M24,34 Q34,10 66,16 Q82,22 76,32 Q52,24 24,34 Z" fill="#e2363f" ${s(line)}/><path d="M52,15 L54,9" ${s(line)}/>`;
      case "cap": return `<path d="M25,40 Q26,16 50,15 Q74,16 75,40 Q50,32 25,40 Z" fill="#8b5e3c" ${s(line)}/>
        <path d="M70,37 L88,42 L72,44 Z" fill="#6b4226" ${s(line)}/><path d="M34,25 L66,25 M30,32 L70,32" stroke="#6b4226" stroke-width="1.6"/>`;
      case "pen": return `<path d="M73,46 L86,26" stroke="${INK}" stroke-width="6" stroke-linecap="round"/><path d="M73,46 L86,26" stroke="#ffd23f" stroke-width="3.4" stroke-linecap="round"/>`;
      case "crown": return `<path d="M35,26 L37,10 L44,19 L50,6 L56,19 L63,10 L65,26 Z" fill="#ffd23f" ${s(line)}/>
        <circle cx="50" cy="20" r="2.3" fill="#ff4d8d"/>`;
      case "band": return `<path d="M25,41 Q50,32 75,41 L75,47 Q50,38 25,47 Z" fill="#ff4d8d" ${s(line)}/>
        <path d="M74,43 L86,38 M74,45 L85,48" ${s({ ...line, stroke: "#ff4d8d", "stroke-width": 3 })}/>`;
      default: return "";
    }
  }

  function mascot(kind) {
    if (kind === "cloud") return `<path d="M22,70 Q10,70 12,57 Q14,45 27,47 Q28,30 46,31 Q58,24 68,36 Q86,34 87,51 Q95,58 88,68 Q84,73 76,72 Z"
        fill="#fff" ${s(line)}/>${eyes("happy")}<path d="M46,63 Q50,67 54,63" fill="none" ${s(line)}/>
        <ellipse cx="33" cy="61" rx="4.5" ry="2.4" fill="#ff8fab" opacity=".7"/><ellipse cx="67" cy="61" rx="4.5" ry="2.4" fill="#ff8fab" opacity=".7"/>
        <path d="M44,80 L56,80 M50,74 L50,88 M46,84 L50,88 L54,84" ${s({ ...line, stroke: "#2563eb", "stroke-width": 2.6 })}/>`;
    if (kind === "heart") return `<path d="M50,84 Q16,62 18,40 Q21,24 36,25 Q46,26 50,36 Q54,26 64,25 Q79,24 82,40 Q84,62 50,84 Z"
        fill="#ff4d8d" ${s(line)}/>${eyes("sparkle", "#1b1530")}<path d="M45,62 Q50,70 55,62 Z" fill="#9b2c4a" ${s(line)}/>
        <path d="M14,20 l1.6,4 4,1.6 -4,1.6 -1.6,4 -1.6,-4 -4,-1.6 4,-1.6z M86,16 l1.3,3 3,1.3 -3,1.3 -1.3,3 -1.3,-3 -3,-1.3 3,-1.3z M88,78 l1.2,2.8 2.8,1.2 -2.8,1.2 -1.2,2.8 -1.2,-2.8 -2.8,-1.2 2.8,-1.2z" fill="#ffd23f" stroke="${INK}" stroke-width="1"/>`;
    // cat courier
    return `<path d="M22,46 L24,16 L42,32 Z M78,46 L76,16 L58,32 Z" fill="#f59e42" ${s(line)}/>
      <path d="M27,38 L28,24 L37,33 Z M73,38 L72,24 L63,33 Z" fill="#ffb3c7"/>
      <ellipse cx="50" cy="55" rx="30" ry="26" fill="#f59e42" ${s(line)}/>
      <path d="M38,32 Q44,38 40,44 M62,32 Q56,38 60,44 M50,30 L50,40" stroke="#c2410c" stroke-width="2.4" fill="none" stroke-linecap="round"/>
      <ellipse cx="50" cy="64" rx="13" ry="9" fill="#fff4e6"/>
      ${eyes("normal")}<path d="M46,63 Q48,66 50,63 Q52,66 54,63" fill="none" ${s(line)}/><path d="M48.5,60 L51.5,60 L50,61.6 Z" fill="#ff5c9a"/>
      <path d="M22,58 L34,60 M22,64 L34,63 M78,58 L66,60 M78,64 L66,63" stroke="${INK}" stroke-width="1.4"/>
      <path d="M30,30 Q50,18 70,30 L68,36 Q50,28 32,36 Z" fill="#22d3ee" ${s(line)}/><path d="M64,33 L80,36 L66,38 Z" fill="#0e7490" ${s(line)}/>`;
  }

  function avatar(id, size = 64, title = true) {
    const p = PERSONAS[id];
    if (!p) return "";
    const L = p.look;
    const clip = `av-${id}-${Math.random().toString(36).slice(2, 7)}`;
    let body;
    if (L.mascot) {
      body = mascot(L.mascot);
    } else {
      body = `<path d="M14,100 Q16,77 50,75 Q84,77 86,100 Z" fill="${L.shirt}" ${s(line)}/>
        <path d="M44,74 L50,82 L56,74" fill="${SKIN}" ${s(line)}/>
        ${hairBack(L.style, L.hair)}
        <ellipse cx="50" cy="52" rx="24" ry="25" fill="${SKIN}" ${s(line)}/>
        <ellipse cx="34.5" cy="61" rx="4.5" ry="2.4" fill="#ff8fab" opacity=".75"/>
        <ellipse cx="65.5" cy="61" rx="4.5" ry="2.4" fill="#ff8fab" opacity=".75"/>
        ${eyes(L.eyes)}${brows(L.brows)}${mouth(L.mouth)}${hairFront(L.style, L.hair)}
        ${(L.acc || []).map(accessory).join("")}`;
    }
    return `<svg class="avatar" width="${size}" height="${size}" viewBox="0 0 100 100" role="img" aria-label="${p.name}">
      ${title ? `<title>${p.name}, ${p.role}</title>` : ""}
      <defs><clipPath id="${clip}"><circle cx="50" cy="50" r="49"/></clipPath></defs>
      <g clip-path="url(#${clip})"><circle cx="50" cy="50" r="50" fill="${L.bg}"/>
        <g fill="#fff" opacity=".35"><circle cx="15" cy="20" r="2"/><circle cx="85" cy="78" r="2.5"/><circle cx="82" cy="18" r="1.5"/></g>
        ${body}</g></svg>`;
  }

  window.ReelGenCrew = { PERSONAS, avatar };
})();
