#!/usr/bin/env python3
# build_docs_split_all.py
# Split 1 file Markdown jadi situs multi-halaman:
# - H2 (##) -> direktori bab: docs/guide/NN-slug/index.html
# - H3 (###) -> sub-halaman:  docs/guide/NN-slug/MM-subslug.html
# - Sidebar hierarki (H2+H3), Mini-TOC dari H4, Prev/Next antar halaman
# - Render Markdown & Mermaid di client (marked + DOMPurify)
# Usage:
#   python tools/build_docs_split_all.py --md docs/ServiceNow_Documentation.md --out docs/guide --title "ServiceNow Docs"

import argparse, re, json
from pathlib import Path
from string import Template

def slugify(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r'[^a-z0-9\s\-]+', '', t)
    t = re.sub(r'\s+', '-', t)
    t = re.sub(r'-+', '-', t)
    return t.strip('-') or 'section'

PAGE = Template(r'''<!doctype html>
<html lang="id">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>$title - $site</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/dompurify@3.0.3/dist/purify.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
  <style>
    .drawer-enter { transform: translateX(-100%); }
    .drawer-open { transform: translateX(0); }
    .prose :where(pre):not(:where(.not-prose *)) { background:#0f172a; color:#e2e8f0; padding:1rem; border-radius:.75rem; overflow:auto; }
    .prose :where(code):not(:where(pre code,.not-prose *)){ background:#e2e8f0; padding:.15rem .35rem; border-radius:.35rem; }
    .prose h2,.prose h3,.prose h4 { scroll-margin-top: 90px; }
    .mini-toc a{ color:#475569; }
    .mini-toc a:hover{ text-decoration:underline; }
    .nav-link.active { background:#eef2ff; font-weight:600; }
  </style>
  <script>mermaid.initialize({ startOnLoad:false, theme:'default' });</script>
</head>
<body class="bg-slate-50 text-slate-900">
  <!-- Topbar -->
  <header class="sticky top-0 z-30 flex items-center justify-between gap-3 border-b bg-white px-4 py-3">
    <div class="flex items-center gap-3">
      <button id="btnOpen" class="md:hidden rounded-lg p-2 hover:bg-slate-100" aria-label="Open menu">
        <i data-lucide="menu" class="h-5 w-5"></i>
      </button>
      <div class="flex items-center gap-2">
        <i data-lucide="book-open" class="h-5 w-5"></i>
        <h1 class="text-lg font-semibold">$site</h1>
      </div>
    </div>
    <div class="flex items-center gap-2 text-sm">
      <a href="../index.html" class="rounded-md border px-3 py-1.5 hover:bg-slate-100 flex items-center gap-2">
        <i data-lucide="layout-dashboard" class="h-4 w-4"></i> Dashboard
      </a>
      <a href="./index.html" class="rounded-md border px-3 py-1.5 hover:bg-slate-100 flex items-center gap-2">
        <i data-lucide="book" class="h-4 w-4"></i> Dokumentasi
      </a>
    </div>
  </header>

  <div id="overlay" class="fixed inset-0 z-40 hidden bg-black/40 md:hidden"></div>

  <div class="mx-auto grid max-w-7xl grid-cols-1 md:grid-cols-[300px_minmax(0,1fr)]"><aside id="drawer">
    <!-- Sidebar -->
    <aside id="drawer" class="drawer-enter fixed left-0 top-0 z-50 h-full w-72 overflow-y-auto border-r bg-white p-4 transition-transform md:drawer-open md:sticky md:top-[56px] md:h-[calc(100vh-56px)] md:w-[300px]">
      <div class="mb-4 flex items-center justify-between md:hidden">
        <span class="font-semibold">Menu</span>
        <button id="btnClose" class="rounded-lg p-2 hover:bg-slate-100" aria-label="Close menu"><i data-lucide="x" class="h-5 w-5"></i></button>
      </div>
      <nav id="nav" class="space-y-1 text-sm">$sidebar</nav>
    </aside>

    <!-- Main -->
    <main class="p-4 md:p-6">
      <article class="prose max-w-none">
        <h2 class="mb-2 text-2xl font-bold">$title</h2>
        <div id="docBody"></div>
      </article>

      <div class="mt-8 flex items-center justify-between gap-3">
        <a href="$prev_href" class="flex items-center gap-2 rounded-md border px-3 py-1.5 hover:bg-slate-100 disabled:opacity-40" $prev_disabled>
          <i data-lucide="arrow-left" class="h-4 w-4"></i> Sebelumnya
        </a>
        <a href="$next_href" class="ml-auto flex items-center gap-2 rounded-md border px-3 py-1.5 hover:bg-slate-100 disabled:opacity-40" $next_disabled>
          Selanjutnya <i data-lucide="arrow-right" class="h-4 w-4"></i>
        </a>
      </div>
    </main>

    <!-- Right mini-TOC -->
    <aside class="hidden lg:block sticky top-24 h-max rounded-xl border bg-white p-4 text-sm m-6">
      <div class="mb-2 font-semibold">Di halaman ini</div>
      <nav id="miniTOC" class="space-y-1"></nav>
    </aside>
  </div>

  <script id="mdsrc" type="text/markdown">$md</script>

  <script>
    // Drawer handlers
    const drawer = document.getElementById('drawer');
    const overlay = document.getElementById('overlay');
    document.getElementById('btnOpen').addEventListener('click', () => { drawer.classList.add('drawer-open'); overlay.classList.remove('hidden'); });
    document.getElementById('btnClose').addEventListener('click', () => { drawer.classList.remove('drawer-open'); overlay.classList.add('hidden'); });
    overlay.addEventListener('click', () => { drawer.classList.remove('drawer-open'); overlay.classList.add('hidden'); });

    // Render MD -> HTML + Mermaid
    const raw = document.getElementById('mdsrc').textContent;
    
    // MERMAID SANITIZER: ubah karakter non-ASCII & artefak yang sering bikin error
    const mermaidified = raw.replace(/```mermaid([\s\S]*?)```/g, function(m, code) {let fixed = code
    .replace(/\u2192/g, '-->')        // “→” jadi “-->”
    .replace(/[–—]/g, '-')            // en/em dash jadi hyphen
    .replace(/\r/g, '')               // CRLF -> LF
    .replace(/^\s*%%.*$/gm, '')       // buang komentar gaya Mermaid
    .replace(/[^\S\r\n]+$/gm, '')     // trim trailing spaces per line
    // perapihan “artefak lama” yang sering kebawa dari contoh sebelumnya:
    .replace(/\]\s*TAG.*/g, ']')      // “] TAG …” -> “]”
    .trim();

    // Escape < > agar aman (DOMPurify tetap dipakai setelah ini)
    fixed = fixed.replace(/</g,'&lt;').replace(/>/g,'&gt;');
    return '<div class="mermaid">' + fixed + '</div>';
    });

    
    
    const html = DOMPurify.sanitize(marked.parse(mermaidified, { mangle:false, headerIds:false, breaks:true }));
    const body = document.getElementById('docBody'); body.innerHTML = html;

    // Mini-TOC (H4)
    function slugify(t) { return t.toLowerCase().replace(/[^a-z0-9\u00C0-\u024f\s-]/g,'').trim().replace(/\s+/g,'-').replace(/-+/g,'-'); }
    const heads = body.querySelectorAll('h4');
    const mtoc = document.getElementById('miniTOC');
    heads.forEach(h => { if(!h.id) h.id = slugify(h.textContent); const a = document.createElement('a'); a.href = '#'+h.id; a.textContent = h.textContent; a.className='block rounded px-2 py-1 hover:bg-slate-50'; mtoc.appendChild(a); });

    mermaid.init(undefined, body.querySelectorAll('.mermaid'));

    // Sidebar active highlighting
    const here = document.querySelector('a[data-current="true"]'); if (here) here.classList.add('active');

    lucide.createIcons();
  </script>
</body>
</html>''')

def build_sidebar(structure, current_href):
    items = []
    for h2 in structure:
        cls = "nav-link flex w-full items-center gap-3 px-3 py-2 hover:bg-slate-100 rounded-lg"
        active = ' data-current="true"' if h2["index_href"] == current_href else ''
        items.append(f'<a class="{cls}" href="{h2["index_href"]}"{active}><i data-lucide="book-open" class="h-4 w-4"></i><span>{h2["num"]}. {h2["title"]}</span></a>')
        for h3 in h2["subs"]:
            cls2 = "nav-link ml-6 block rounded-lg px-3 py-1.5 hover:bg-slate-100"
            active2 = ' data-current="true"' if h3["href"] == current_href else ''
            items.append(f'<a class="{cls2}" href="{h3["href"]}"{active2}>{h2["num"]}.{h3["num"]} {h3["title"]}</a>')
    return "\n".join(items)

def parse_md(md_text: str):
    # H2 blocks
    h2_iter = list(re.finditer(r'(?m)^##\s+(.+)$', md_text))
    sections = []
    for i, m in enumerate(h2_iter):
        start = m.end()
        end = h2_iter[i+1].start() if i+1 < len(h2_iter) else len(md_text)
        h2_title = m.group(1).strip()
        h2_block = md_text[start:end]

        # H3 inside H2
        h3_iter = list(re.finditer(r'(?m)^###\s+(.+)$', h2_block))
        h3s = []
        for j, mh3 in enumerate(h3_iter):
            s = mh3.end()
            e = h3_iter[j+1].start() if j+1 < len(h3_iter) else len(h2_block)
            h3_title = mh3.group(1).strip()
            h3_content = h2_block[s:e].strip()
            h3s.append({"title": h3_title, "content": h3_content})
        lead = h2_block[:h3_iter[0].start()].strip() if h3_iter else h2_block.strip()
        sections.append({"title": h2_title, "lead": lead, "subs": h3s})
    return sections

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--md', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--title', default='Docs')
    args = ap.parse_args()

    md_path = Path(args.md)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    md_text = md_path.read_text(encoding='utf-8')
    structure = parse_md(md_text)

    # Build site structure and flat page order
    site = []
    pages = []
    h2_num = 0
    for h2 in structure:
        h2_num += 1
        h2_slug = slugify(h2["title"])
        h2_dir = out_dir / f"{str(h2_num).zfill(2)}-{h2_slug}"
        h2_dir.mkdir(parents=True, exist_ok=True)

        h2_index_href = f"{h2_dir.name}/index.html"
        site.append({"num": h2_num, "title": h2["title"], "index_href": h2_index_href, "subs": []})
        pages.append(h2_index_href)

        h3_num = 0
        for h3 in h2["subs"]:
            h3_num += 1
            h3_slug = slugify(h3["title"])
            h3_file = h2_dir / f"{str(h3_num).zfill(2)}-{h3_slug}.html"
            h3_href = f"{h2_dir.name}/{h3_file.name}"
            site[-1]["subs"].append({"num": h3_num, "title": h3["title"], "href": h3_href})
            pages.append(h3_href)

    # Helper: write a page (H2 index or H3 page)
    def write_page(href: str, title: str, md_fragment: str):
        idx = pages.index(href)
        prev_href = pages[idx-1] if idx > 0 else "#"
        next_href = pages[idx+1] if idx+1 < len(pages) else "#"
        prev_dis = "" if idx > 0 else 'aria-disabled="true" tabindex="-1"'
        next_dis = "" if idx+1 < len(pages) else 'aria-disabled="true" tabindex="-1"'
        sidebar = build_sidebar(site, href)
        html = PAGE.safe_substitute(
            title=title, site=args.title, sidebar=sidebar, md=md_fragment,
            prev_href=prev_href, next_href=next_href,
            prev_disabled=prev_dis, next_disabled=next_dis
        )
        (out_dir / href).write_text(html, encoding='utf-8')

    # Write H3 pages
    for h2 in site:
        h2_dir = out_dir / h2["index_href"].split('/')[0]
        # find the original content for this H2
        src_h2 = next(s for s in structure if slugify(s["title"]) == slugify(h2["title"]))
        for sub in h2["subs"]:
            src_h3 = next(s for s in src_h2["subs"] if slugify(s["title"]) == slugify(sub["title"]))
            md_fragment = "#### Ringkasan\n\n" + src_h3["content"]
            write_page(sub["href"], f"{h2['num']}.{sub['num']} {sub['title']}", md_fragment)

    # Write H2 index pages (lead + daftar sub)
    for h2 in site:
        src_h2 = next(s for s in structure if slugify(s["title"]) == slugify(h2["title"]))
        subs_list = "\n".join([f"- [{s['title']}]({s['href']})" for s in h2["subs"]]) or "_Tidak ada subbab._"
        md_fragment = (src_h2["lead"].strip() + ("\n\n---\n\n### Sub-bab\n\n" + subs_list if subs_list else "")).strip()
        write_page(h2["index_href"], f"{h2['num']}. {h2['title']}", md_fragment)

    # Landing index (guide/)
    landing = ['<!doctype html><html lang="id"><meta charset="utf-8">',
               '<meta name="viewport" content="width=device-width, initial-scale=1">',
               f'<title>Dokumentasi - {args.title}</title>',
               '<script src="https://cdn.tailwindcss.com"></script>',
               '<body class="bg-slate-50 text-slate-900 p-6 max-w-5xl mx-auto">',
               f'<h1 class="text-2xl font-bold mb-4">Dokumentasi – {args.title}</h1>',
               '<ol class="space-y-2">']
    for h2 in site:
        landing.append(f'<li><a class="rounded-md border px-3 py-2 hover:bg-slate-100 inline-block" href="./{h2["index_href"]}">{h2["num"]}. {h2["title"]}</a></li>')
        if h2["subs"]:
            landing.append('<ul class="ml-6 list-disc">')
            for s in h2["subs"]:
                landing.append(f'<li><a class="hover:underline" href="./{s["href"]}">{h2["num"]}.{s["num"]} {s["title"]}</a></li>')
            landing.append('</ul>')
    landing.append('</ol><p class="mt-8"><a href="../index.html" class="text-blue-600 hover:underline">↩ Kembali ke Dashboard</a></p></body></html>')
    (Path(args.out) / "index.html").write_text("\n".join(landing), encoding="utf-8")

    # Simpan struktur (debug)
    (Path(args.out) / "_structure.json").write_text(json.dumps(site, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
