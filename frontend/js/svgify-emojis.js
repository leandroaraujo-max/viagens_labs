(function () {
  const ICONS = {
    "✈️": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 16l20-4-20-4 5 4-5 4z"/><path d="M9 12h13"/></svg>',
    "🚌": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="13" rx="2"/><path d="M7 17v3M17 17v3M3 10h18"/><circle cx="8" cy="19" r="1"/><circle cx="16" cy="19" r="1"/></svg>',
    "🏨": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21V5a2 2 0 0 1 2-2h8v18"/><path d="M13 21V9a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v12"/><path d="M7 7h2M7 11h2M7 15h2M16 11h2M16 15h2"/></svg>',
    "🚗": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 16l1.5-5h11L19 16"/><rect x="3" y="12" width="18" height="5" rx="2"/><circle cx="7" cy="17" r="1"/><circle cx="17" cy="17" r="1"/></svg>',
    "🛡️": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3l7 3v6c0 5-3.5 7.5-7 9-3.5-1.5-7-4-7-9V6l7-3z"/><path d="M9 12l2 2 4-4"/></svg>',
    "💳": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20"/><path d="M6 15h4"/></svg>',
    "⚠": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3L2.5 20h19L12 3z"/><path d="M12 9v5"/><circle cx="12" cy="17" r="1"/></svg>',
    "⚠️": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3L2.5 20h19L12 3z"/><path d="M12 9v5"/><circle cx="12" cy="17" r="1"/></svg>',
    "✔": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg>',
    "⏳": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M6 2h12M6 22h12"/><path d="M8 2v5a4 4 0 0 0 1.17 2.83L12 12l2.83-2.17A4 4 0 0 0 16 7V2"/><path d="M16 22v-5a4 4 0 0 0-1.17-2.83L12 12l-2.83 2.17A4 4 0 0 0 8 17v5"/></svg>',
    "🌅": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 18h18"/><path d="M6 18a6 6 0 0 1 12 0"/><path d="M12 4v4M4.5 10.5l2.5 1.5M19.5 10.5L17 12"/></svg>',
    "☀️": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M19.1 4.9l-1.4 1.4M6.3 17.7l-1.4 1.4"/></svg>',
    "🌙": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z"/></svg>',
    "🌌": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 20l4-10 4 6 3-4 7 8"/><circle cx="8" cy="5" r="1"/><circle cx="14" cy="4" r="1"/><circle cx="19" cy="7" r="1"/></svg>',
    "➕": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>',
    "🔍": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.35-4.35"/></svg>',
    "⚕": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2v20M7 7h10M7 17h10"/></svg>',
    "★": '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2l2.9 6 6.6.9-4.8 4.7 1.2 6.7L12 17l-5.9 3.3 1.2-6.7L2.5 8.9l6.6-.9L12 2z"/></svg>',
    "↺": '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>'
  };

  const EMOJIS = Object.keys(ICONS).sort((a, b) => b.length - a.length);
  const escaped = EMOJIS.map((e) => e.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const RE = new RegExp("(" + escaped.join("|") + ")", "g");

  function injectStyle() {
    if (document.getElementById("vl-svgify-style")) return;
    const style = document.createElement("style");
    style.id = "vl-svgify-style";
    style.textContent = ".vl-svg-icon{display:inline-flex;vertical-align:-0.15em;line-height:1}.vl-svg-icon svg{width:1em;height:1em;display:block}";
    document.head.appendChild(style);
  }

  function replaceInTextNode(node) {
    const text = node.nodeValue;
    if (!text || !RE.test(text)) return;
    RE.lastIndex = 0;
    const html = text.replace(RE, function (emoji) {
      return '<span class="vl-svg-icon" data-emoji="' + emoji + '">' + (ICONS[emoji] || "") + "</span>";
    });
    const span = document.createElement("span");
    span.innerHTML = html;
    node.parentNode.replaceChild(span, node);
  }

  function walk(root) {
    if (!root) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (node) {
        if (!node.parentElement) return NodeFilter.FILTER_REJECT;
        const tag = node.parentElement.tagName;
        if (tag === "SCRIPT" || tag === "STYLE" || tag === "TEXTAREA") return NodeFilter.FILTER_REJECT;
        if (node.parentElement.closest("svg")) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const toReplace = [];
    while (walker.nextNode()) {
      toReplace.push(walker.currentNode);
    }
    toReplace.forEach(replaceInTextNode);
  }

  function boot() {
    injectStyle();
    walk(document.body);
    const observer = new MutationObserver(function (mutations) {
      mutations.forEach(function (m) {
        if (m.type === "characterData") {
          replaceInTextNode(m.target);
          return;
        }
        m.addedNodes.forEach(function (n) {
          if (n.nodeType === Node.TEXT_NODE) {
            replaceInTextNode(n);
          } else if (n.nodeType === Node.ELEMENT_NODE) {
            walk(n);
          }
        });
      });
    });
    observer.observe(document.body, { childList: true, subtree: true, characterData: true });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot, { once: true });
  } else {
    boot();
  }
})();
