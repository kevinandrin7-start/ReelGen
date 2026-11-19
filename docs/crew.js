// The ReelGen crew: a name, a studio title and a line icon for each agent.
(() => {
  const PERSONAS = {
    you_add: { name: "You", role: "Executive producer", icon: "idea" },
    collaborator: { name: "Harper", role: "Collaborator", icon: "clipboard" },
    researcher: { name: "Oliver", role: "Researcher", icon: "search" },
    scripter: { name: "Grace", role: "Scripter", icon: "script" },
    director: { name: "Elliot", role: "Director", icon: "clapper" },
    sound_engineer: { name: "Miles", role: "Sound engineer", icon: "mic" },
    editor: { name: "Nora", role: "Editor", icon: "timeline" },
    tester: { name: "Quinn", role: "Tester", icon: "headphones" },
    drive: { name: "The Vault", role: "Google Drive", icon: "cloud" },
    drive_keeper: { name: "Walter", role: "Drive keeper", icon: "trash" },
    you_approve: { name: "You", role: "Final cut approval", icon: "approve" },
    publisher: { name: "Felix", role: "Publisher", icon: "send" },
    socials: { name: "Audience", role: "Instagram & YouTube", icon: "broadcast" },
  };

  // 24x24 line icons, drawn with currentColor.
  const ICONS = {
    idea: '<path d="M9 18h6M10 21h4"/><path d="M12 3a6 6 0 0 0-3.5 10.9c.6.5 1 1.2 1 2.1h5c0-.9.4-1.6 1-2.1A6 6 0 0 0 12 3z"/>',
    clipboard: '<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V3h6v1M9 10h6M9 14h6M9 18h3"/>',
    search: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l5 5"/>',
    script: '<path d="M6 3h9l4 4v14H6z"/><path d="M15 3v4h4M9 11h7M9 15h7M9 19h4"/>',
    clapper: '<path d="M3 10h18v10H3z"/><path d="M3 10l1.5-5 16 3.5L20 10"/><path d="M8 5.6l2 3.9M13 6.8l2 3.2"/>',
    mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M8.5 21h7"/>',
    timeline: '<path d="M3 5h18M3 19h18"/><rect x="4" y="8" width="7" height="3" rx="1"/><rect x="12" y="8" width="8" height="3" rx="1"/><rect x="7" y="13" width="10" height="3" rx="1"/><path d="M14 3v18"/>',
    headphones: '<path d="M4 16v-3a8 8 0 0 1 16 0v3"/><rect x="3" y="15" width="4" height="6" rx="1.5"/><rect x="17" y="15" width="4" height="6" rx="1.5"/><path d="M10 13l1.6 1.6L15 11"/>',
    cloud: '<path d="M7 18a4.5 4.5 0 0 1-.6-9A6 6 0 0 1 18 9.5 4.3 4.3 0 0 1 17.5 18z"/><path d="M12 11v5M9.8 13.8L12 16l2.2-2.2"/>',
    trash: '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14M10 11v6M14 11v6"/>',
    approve: '<circle cx="12" cy="12" r="9"/><path d="M8 12.5l2.7 2.7L16.5 9"/>',
    send: '<path d="M21 3L10 14M21 3l-7 18-4-7-7-4z"/>',
    broadcast: '<circle cx="12" cy="12" r="2"/><path d="M8.5 15.5a5 5 0 0 1 0-7M15.5 8.5a5 5 0 0 1 0 7M5.6 18.4a9 9 0 0 1 0-12.8M18.4 5.6a9 9 0 0 1 0 12.8"/>',
    film: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 4v16M17 4v16M3 8h4M3 12h4M3 16h4M17 8h4M17 12h4M17 16h4"/>',
    play: '<path d="M8 5.5v13l10.5-6.5z" fill="currentColor"/>',
    rec: '<circle cx="12" cy="12" r="5" fill="currentColor"/>',
  };

  function icon(name, size = 20, cls = "ico") {
    return `<svg class="${cls}" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor"
      stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ""}</svg>`;
  }

  // An agent's badge: its icon in a round frame.
  function avatar(id, size = 64) {
    const p = PERSONAS[id];
    if (!p) return "";
    return `<span class="badge" style="width:${size}px;height:${size}px" role="img" aria-label="${p.name}, ${p.role}">
      ${icon(p.icon, Math.round(size * 0.46))}</span>`;
  }

  window.ReelGenCrew = { PERSONAS, icon, avatar };
})();
