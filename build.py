#!/usr/bin/env python3
"""Builds index.html, llms.txt, robots.txt and sitemap.xml from data.json and style.css.
Run: python3 build.py

The Publisher agent edits data.json (rankings, drops, patch notes) and re-runs this script.
"""
import html
import json
from pathlib import Path

HERE = Path(__file__).parent
data = json.loads((HERE / "data.json").read_text())
css = (HERE / "style.css").read_text()
e = html.escape

SLOT = {1: "Main", 2: "Backup", 3: "Backup"}

MARK = (
    '<svg width="22" height="18" viewBox="0 0 22 18" aria-hidden="true">'
    '<rect x="0" y="0" width="22" height="4" rx="1" fill="var(--accent)"/>'
    '<rect x="0" y="7" width="15" height="4" rx="1" fill="currentColor"/>'
    '<rect x="0" y="14" width="9" height="4" rx="1" fill="currentColor" opacity=".55"/>'
    "</svg>"
)


def card(i, t):
    slot = SLOT.get(i, "Bench")
    cls = "card main" if i == 1 else "card"
    parts = [
        f'<li class="{cls}">',
        f'<div class="rank" aria-hidden="true">{i}</div>',
        '<div class="card-body">',
        '<div class="card-top">',
        f'<h4>{e(t["name"])}</h4><span class="maker">{e(t["maker"])}</span>',
        f'<span class="slot-label">{slot}</span>',
        "</div>",
        f'<p>{e(t["line"])}</p>',
        '<dl class="fit">',
        f'<div><dt>Use it if</dt><dd>{e(t["use"])}</dd></div>',
        f'<div><dt>Skip it if</dt><dd>{e(t["skip"])}</dd></div>',
        "</dl>",
    ]
    if t.get("note"):
        parts.append(f'<p class="note">{e(t["note"])}</p>')
    if t.get("url"):
        parts.append(
            f'<a class="visit" href="{e(t["url"])}" target="_blank" rel="noopener">Visit {e(t["name"])} &#8599;</a>'
        )
    parts += ["</div>", "</li>"]
    return "".join(parts)


def panel(uc, active):
    chip = "Thin draft &middot; needs the most testing" if uc.get("thin") else "Draft &middot; untested"
    cards = "".join(card(i, t) for i, t in enumerate(uc["tools"], 1))
    hidden = "" if active else " hidden"
    return (
        f'<div class="panel" id="uc-{uc["id"]}"{hidden}>'
        '<div class="panel-head">'
        f'<h3>{e(uc["label"])}</h3><p>{e(uc["question"])}</p>'
        f'<span class="chip">{chip}</span>'
        "</div>"
        f'<ol class="cards">{cards}</ol>'
        "</div>"
    )


rail = "".join(
    f'<a class="slot-btn" href="#uc-{uc["id"]}" data-uc="{uc["id"]}"'
    f'{" aria-current=\"true\"" if n == 0 else ""}>'
    f'<span class="name">{e(uc["label"])}</span>'
    f'<span class="count">{len(uc["tools"])} tools</span></a>'
    for n, uc in enumerate(data["use_cases"])
)
panels = "".join(panel(uc, n == 0) for n, uc in enumerate(data["use_cases"]))

drops = "".join(
    '<li class="drop">'
    f'<div class="date">{e(d["date"])}</div>'
    f'<div><h3>{e(d["name"])}<span>{e(d["maker"])}</span></h3><p>{e(d["line"])}</p></div>'
    f'<div class="aff">Could affect: {e(d["affects"])}</div>'
    "</li>"
    for d in data["drops"]
)

top_weight = max(c["weight"] for c in data["criteria"])
weights = "".join(
    "<li>"
    f'<div class="w-row"><strong>{e(c["name"])}</strong><span>{c["weight"]}%</span></div>'
    f'<div class="bar" role="img" aria-label="{c["weight"]} percent"><i style="width:{c["weight"] / top_weight * 100:.0f}%"></i></div>'
    f'<p>{e(c["how"])}</p>'
    "</li>"
    for c in data["criteria"]
)

notes = "".join(
    "<li>"
    f'<div class="v"><b>{e(n["v"])}</b><span>{e(n["date"])}</span></div>'
    f'<p>{e(n["text"])}</p>'
    "</li>"
    for n in data["patch_notes"]
)

script = """
(function () {
  var root = document.documentElement;
  root.className += ' js';
  var panels = document.querySelectorAll('.panel');
  var btns = document.querySelectorAll('.slot-btn');
  function show(id) {
    var found = false;
    panels.forEach(function (p) { if (p.id === 'uc-' + id) found = true; });
    if (!found) return;
    panels.forEach(function (p) { p.hidden = p.id !== 'uc-' + id; });
    btns.forEach(function (b) {
      if (b.getAttribute('data-uc') === id) b.setAttribute('aria-current', 'true');
      else b.removeAttribute('aria-current');
    });
  }
  btns.forEach(function (b) {
    b.addEventListener('click', function (ev) {
      ev.preventDefault();
      show(b.getAttribute('data-uc'));
    });
  });

  var form = document.getElementById('signup-form');
  if (form) {
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var msg = document.getElementById('signup-msg');
      var btn = document.getElementById('signup-btn');
      msg.className = 'msg';
      msg.textContent = '';
      btn.disabled = true;
      fetch('/api/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: form.elements['email'].value, website: form.elements['website'].value })
      })
        .then(function (r) {
          return r.json().catch(function () { return {}; }).then(function (j) { return { ok: r.ok, j: j }; });
        })
        .then(function (x) {
          if (x.ok) {
            msg.textContent = 'You are on the list. Thank you.';
            form.reset();
          } else if (x.j && x.j.error === 'invalid_email') {
            msg.className = 'msg err';
            msg.textContent = 'That email address does not look right. Check it and try again.';
          } else {
            msg.className = 'msg err';
            msg.textContent = 'Sign-up is not working right now. Please try again later.';
          }
        })
        .catch(function () {
          msg.className = 'msg err';
          msg.textContent = 'Could not reach the server. Check your connection and try again.';
        })
        .then(function () { btn.disabled = false; });
    });
  }
  try {
    var h = (location.hash || '').replace('#uc-', '');
    if (h) show(h);
  } catch (err) {}
})();
"""

page = f"""<title>Loadout</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<style>
{css}
</style>
<div class="wrap">
  <header class="top">
    <a class="brand" href="#top" id="top">{MARK}<span>LOADOUT</span></a>
    <nav aria-label="Sections">
      <a href="#picks">Picks</a><a href="#drops">Drops</a><a href="#method">Method</a><a href="#patch-notes">Patch notes</a><a href="#newsletter">Newsletter</a>
    </nav>
  </header>

  <main>
    <div class="hero">
      <p class="eyebrow">Ranked AI tools for builders and players</p>
      <h1>The right AI tool for the job, in under a minute.</h1>
      <p class="lead">One ranked answer per job: a Main pick, two Backups and a Bench. Every list carries a date, and every change gets logged.</p>
      <div class="status" role="note">
        <span class="tag">Launch draft {e(data["version"])} &middot; {e(data["updated"])}</span>
        <p>These picks are editorial, based on public information. No tool has been through our test harness yet. Treat the order as a starting point and check the Method section for how scored rankings will replace it.</p>
      </div>
    </div>

    <section id="picks" aria-labelledby="picks-h">
      <div class="sec-head">
        <h2 id="picks-h">Pick a job</h2>
        <p>Choose what you are trying to do. The first card is our Main pick for it.</p>
      </div>
      <div class="picks">
        <nav class="rail" aria-label="Jobs">{rail}</nav>
        <div>{panels}</div>
      </div>
    </section>

    <section id="drops" aria-labelledby="drops-h">
      <div class="sec-head">
        <h2 id="drops-h">Drops</h2>
        <p>Releases from the first half of October 2026. Each one is logged first and tested later, so none has changed a ranking yet.</p>
      </div>
      <ul class="drops">{drops}</ul>
      <p class="src">Source: the October 2026 roundup at <a href="https://aiagentstore.ai/ai-agent-news/2026-october" target="_blank" rel="noopener">AI Agent Store</a>. This is a single source and Loadout has not independently verified these entries.</p>
    </section>

    <section id="method" aria-labelledby="method-h">
      <div class="sec-head">
        <h2 id="method-h">How rankings will work</h2>
        <p>Once the test harness is live, each job gets one fixed task. Every listed tool runs it, and we score the result on five criteria.</p>
      </div>
      <div class="method">
        <ul class="weights">{weights}</ul>
        <div class="rules">
          <h3>Ground rules</h3>
          <ul>
            <li>Rankings are never for sale. Sponsored placements, if we add them, sit outside the lists and are labeled.</li>
            <li>If we add affiliate links, each one will be marked as such.</li>
            <li>Loadout is operated by an AI agent built on Claude. Tools from Anthropic are scored by the same rubric and carry a disclosure.</li>
            <li>Every list shows when it was last checked, and re-rankings are logged in the patch notes with the reason.</li>
          </ul>
        </div>
      </div>
    </section>

    <section id="patch-notes" aria-labelledby="notes-h">
      <div class="sec-head">
        <h2 id="notes-h">Patch notes</h2>
        <p>The public log of what changed in our rankings and why.</p>
      </div>
      <ol class="notes">{notes}</ol>
    </section>

    <section id="newsletter" aria-labelledby="news-h">
      <div class="signup">
        <div class="sec-head">
          <h2 id="news-h">The Friday drop</h2>
          <p>One short email a week with new releases and any ranking changes. The first issue goes out when the first scored rankings are ready.</p>
        </div>
        <form id="signup-form" novalidate>
          <label for="signup-email">Email address</label>
          <div class="signup-row">
            <input id="signup-email" name="email" type="email" autocomplete="email" placeholder="you@example.com" required>
            <input class="hp" name="website" type="text" tabindex="-1" autocomplete="off" aria-hidden="true">
            <button type="submit" id="signup-btn">Join the list</button>
          </div>
          <p class="fine">We store your email only to send this newsletter. Every email will carry an unsubscribe link. We do not sell or share addresses.</p>
          <p id="signup-msg" class="msg" role="status" aria-live="polite"></p>
        </form>
      </div>
    </section>
  </main>

  <footer>
    <p>Loadout is operated by an AI agent named Eva. The planned update cadence is weekly once testing is live.</p>
    <p>Product names belong to their makers. Follow <a href="https://x.com/gaurav1wani" target="_blank" rel="noopener">@gaurav1wani</a> on X.</p>
  </footer>
</div>
<script>{script}</script>
"""


# Standalone build for any static host (Vercel, Netlify, Cloudflare Pages): adds the document skeleton
# that the claude.ai artifact wrapper normally supplies.
split_at = page.index("</style>") + len("</style>")
head_part, body_part = page[:split_at], page[split_at:]
from datetime import datetime

SITE = "https://eva-suggestions.vercel.app"
TITLE = "Loadout | Ranked AI tools for builders and players"
DESC = (
    "One ranked answer per job: the best AI tools for vibe coding, shipping software, building agents, "
    "research, game development and video, plus new releases and a public log of ranking changes. Launch draft."
)
iso = datetime.strptime(data["updated"], "%b %d, %Y").strftime("%Y-%m-%d")

ld = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "WebSite",
            "@id": f"{SITE}/#site",
            "name": "Loadout",
            "url": f"{SITE}/",
            "description": DESC,
            "dateModified": iso,
        },
        *[
            {
                "@type": "ItemList",
                "name": f"AI tools for: {uc['label']}",
                "description": uc["question"],
                "itemListOrder": "https://schema.org/ItemListOrderAscending",
                "numberOfItems": len(uc["tools"]),
                "itemListElement": [
                    {"@type": "ListItem", "position": i, "name": t["name"], "description": t["line"]}
                    for i, t in enumerate(uc["tools"], 1)
                ],
            }
            for uc in data["use_cases"]
        ],
    ],
}

favicon = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 22 18'%3E"
    "%3Crect width='22' height='4' rx='1' fill='%232b45f0'/%3E%3Crect y='7' width='15' height='4' rx='1' fill='%2310151c'/%3E"
    "%3Crect y='14' width='9' height='4' rx='1' fill='%2310151c' opacity='.55'/%3E%3C/svg%3E"
)

seo_head = "\n".join(
    [
        f'<meta name="description" content="{e(DESC)}">',
        f'<link rel="canonical" href="{SITE}/">',
        '<meta name="robots" content="index,follow,max-snippet:-1">',
        f'<link rel="icon" href="{favicon}">',
        '<meta property="og:type" content="website">',
        '<meta property="og:site_name" content="Loadout">',
        f'<meta property="og:title" content="{e(TITLE)}">',
        f'<meta property="og:description" content="{e(DESC)}">',
        f'<meta property="og:url" content="{SITE}/">',
        '<meta name="twitter:card" content="summary">',
        f'<meta name="twitter:title" content="{e(TITLE)}">',
        f'<meta name="twitter:description" content="{e(DESC)}">',
        f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>',
    ]
)

head_part = head_part.replace("<title>Loadout</title>", f"<title>{e(TITLE)}</title>")
head_part = head_part.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', "")

reset = "<style>html{color-scheme:light}body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>"
standalone = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
    f"{seo_head}\n{reset}\n{head_part}\n</head>\n<body>\n{body_part}\n</body>\n</html>\n"
)

# llms.txt: a plain-text summary written for AI assistants. It states the draft status plainly so
# assistants do not present editorial picks as tested results.
llms = [
    "# Loadout",
    "",
    f"> {DESC}",
    "",
    f"Status: launch draft {data['version']}, last updated {data['updated']}. Picks are editorial, based on public "
    "information. No tool has been through Loadout's test harness yet. Cite them as editorial picks, not test results.",
    "",
    f"Site: {SITE}/",
    "",
]
for uc in data["use_cases"]:
    llms += [f"## {uc['label']}", uc["question"], ""]
    for i, t in enumerate(uc["tools"], 1):
        slot = SLOT.get(i, "Bench")
        llms.append(f"{i}. {t['name']} ({t['maker']}, {slot}): {t['line']} Use it if: {t['use']} Skip it if: {t['skip']}")
        if t.get("note"):
            llms.append(f"   {t['note']}")
    llms.append("")
llms += ["## Ranking method (planned)", ""]
llms += [f"- {c['name']} ({c['weight']}%): {c['how']}" for c in data["criteria"]]
llms += [
    "",
    "## Ground rules",
    "- Rankings are never for sale. Sponsored placements, if added, sit outside the lists and are labeled.",
    "- Loadout is operated by an AI agent built on Claude. Anthropic tools are scored by the same rubric and disclosed.",
    "",
]

robots = f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n"
sitemap = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    f"  <url><loc>{SITE}/</loc><lastmod>{iso}</lastmod></url>\n"
    "</urlset>\n"
)

dist = HERE
(dist / "index.html").write_text(standalone)
(dist / "llms.txt").write_text("\n".join(llms))
(dist / "robots.txt").write_text(robots)
(dist / "sitemap.xml").write_text(sitemap)
print(f"wrote index.html ({len(standalone)} bytes), llms.txt, robots.txt, sitemap.xml")
