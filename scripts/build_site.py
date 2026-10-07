"""Build the static academic homepage from its editable jemdoc sources.

No third-party packages are required. Run: python3 scripts/build_site.py
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
UPDATED = "7 October 2026"
SITE = "https://zsy817.github.io"
NAV = [("index.html", "Home"), ("publication.html", "Publications"),
       ("award.html", "Awards"), ("service.html", "Service")]


def inline(text):
    text = text.replace(r"\n", "").replace(r"\[", "[").replace(r"\]", "]")
    text = text.replace(r"\*", "\x00")
    text = html.escape(text.strip())
    text = re.sub(r"\*([^*]+)\*", r"<strong>\1</strong>", text)
    return text.replace("\x00", "<sup>*</sup>")


def normalize(text):
    return re.sub(r"[^a-z0-9]", "", text.lower())


def paper_title(text):
    match = re.search(r'(?:["“]|``)(.*?)["”]', text, re.S)
    return " ".join(match.group(1).rstrip(",").split()) if match else ""


def parse_publications():
    entries, current = [], None
    kind, default_year = "under-review", ""
    for line in (SOURCES / "publication.jemdoc").read_text().splitlines():
        if line.startswith("== "):
            if "Peer-Reviewed" in line:
                kind = "journal"
            elif "Conferences" in line:
                kind = "conference"
        elif line.startswith("=== "):
            default_year = line[4:].strip()
        elif re.match(r"- \\\[[JC]\d+\\\]", line):
            current = {"kind": kind, "default_year": default_year, "text": line[2:]}
            entries.append(current)
        elif current and line.strip() and not line.startswith(("#", "=")):
            current["text"] += " " + line.strip()
    for entry in entries:
        entry["id"] = re.search(r"\[([JC]\d+)\\?\]", entry["text"]).group(1)
        years = re.findall(r"\b(?:19|20)\d{2}\b", entry["text"])
        entry["year"] = years[-1] if years else entry["default_year"]
        entry["title"] = paper_title(entry["text"])
    return entries


def paper_html(entry, links, selected=False):
    text = re.sub(r"^\\\[[JC]\d+\\\]\s*", "", entry["text"])
    text = text.replace("``", '"').replace("“", '"').replace("”", '"')
    text = re.sub(r"\s+", " ", text)
    conference_award = False
    if entry["kind"] == "conference":
        text, award_count = re.subn(r"\s*\(\*Best Paper Award\*\)", "", text)
        conference_award = award_count > 0
    rendered = inline(text)
    candidate = links.get(entry["id"], {})
    matched = normalize(candidate.get("title", "")) == normalize(entry["title"])
    doi = candidate.get("doi", "") if matched else ""
    if not re.fullmatch(r"https://doi\.org/10\.\d{4,9}/[^\s]+", doi):
        doi = ""
    title_html = html.escape(entry["title"])
    if title_html and title_html in rendered:
        replacement = f'<cite class="paper-title">{title_html}</cite>'
        if doi:
            replacement = f'<a class="paper-title" href="{html.escape(doi)}">{title_html}</a>'
        rendered = rendered.replace(title_html, replacement, 1)
    doi_link = f' <a class="paper-link" href="{html.escape(doi)}" aria-label="DOI for {title_html}">DOI <span aria-hidden="true">↗</span></a>' if doi else ""
    number = entry["id"]
    element_id = f"selected-{number}" if selected else number
    badges = []
    if conference_award:
        badges.append('<span class="paper-recognition" title="Best Paper Award">Best Paper Award</span>')
    for recognition in candidate.get("recognitions", []) if matched else []:
        label = html.escape(recognition["label"])
        description = recognition.get("description", recognition["label"])
        if recognition.get("verification") == "author-reported":
            description += " Status supplied by the author; not independently verified against an ESI snapshot."
        attributes = f'class="paper-recognition" title="{html.escape(description, quote=True)}"'
        url = recognition.get("url", "")
        if url.startswith("https://"):
            badges.append(f'<a {attributes} href="{html.escape(url, quote=True)}">{label}</a>')
        else:
            badges.append(f'<span {attributes}>{label}</span>')
    recognition_html = f'<p class="paper-recognitions">{" ".join(badges)}</p>' if badges else ""
    return (f'<li class="publication" id="{element_id}" data-year="{entry["year"]}" '
            f'data-kind="{entry["kind"]}"><span class="paper-number">[{number}]</span>'
            f'<div><p>{rendered}{doi_link}</p>{recognition_html}</div></li>')


def page(filename, title, body, description, publication=False):
    menu = "".join(f'<a href="{url}"'+(' aria-current="page"' if url == filename else '')+f'>{name}</a>' for url, name in NAV)
    css_path = ROOT / "css/site.css"
    if not css_path.exists():
        css_path = ROOT / "html/css/site.css"
    css_version = hashlib.sha256(css_path.read_bytes()).hexdigest()[:10]
    script = '  <script src="js/publications.js" defer></script>' if publication else ""
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(description)}">
  <meta name="author" content="Shengyu Zhang">
  <title>{html.escape(title)} | Shengyu Zhang</title>
  <link rel="canonical" href="{SITE}/{'' if filename == 'index.html' else filename}">
  <link rel="icon" href="img/favicon.png">
  <link rel="stylesheet" href="css/site.css?v={css_version}">
{script}
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="site-layout">
    <aside class="sidebar">
      <a class="site-name" href="index.html">Shengyu Zhang</a>
      <p class="sidebar-affiliation">Xidian University</p>
      <nav aria-label="Main navigation">{menu}</nav>
    </aside>
    <main id="main" tabindex="-1">
      {body}
      <footer>Last updated: <time datetime="2026-10-07">{UPDATED}</time></footer>
    </main>
  </div>
</body>
</html>
'''


def source_sections(filename):
    lines = (SOURCES / filename).read_text().splitlines()
    output, pending, in_list = [], [], False

    def close_paragraph():
        if pending:
            output.append("<p>" + inline(" ".join(pending)) + "</p>")
            pending.clear()

    def close_list():
        nonlocal in_list
        if in_list:
            output.append("</ul>")
            in_list = False

    for line in lines:
        if line.startswith("#") or line.startswith("= "):
            continue
        if line.startswith("== "):
            close_paragraph()
            close_list()
            output.append(f"<h2>{inline(line[3:])}</h2>")
        elif line.startswith("- "):
            close_paragraph()
            if not in_list:
                output.append('<ul class="detail-list">')
                in_list = True
            output.append(f"<li>{inline(line[2:])}</li>")
        elif not line.strip():
            close_paragraph()
        else:
            close_list()
            pending.append(line.strip())
    close_paragraph()
    close_list()
    return "\n".join(output)


def home(entries, links):
    source = (SOURCES / "index.jemdoc").read_text()
    # Preserve jemdoc raw HTML blocks, including the site's visitor-map widget.
    raw_blocks = "\n".join(re.findall(
        r"^~~~[ \t]*\n\{\}\{raw\}[ \t]*\n(.*?)^~~~[ \t]*$",
        source, re.MULTILINE | re.DOTALL,
    ))
    paragraphs = [paragraph.strip() for paragraph in source.split("\n\n") if paragraph.strip().startswith(("I am ", "My research ", "I serve "))]
    about = "\n".join(f"<p>{inline(paragraph)}</p>" for paragraph in paragraphs)
    selected = "\n".join(paper_html(next(entry for entry in entries if entry["id"] == label), links, True) for label in ("J33", "J30", "J9"))
    return f'''<header class="profile">
        <img class="portrait" src="img/zsy.jpg" alt="Portrait of Shengyu Zhang" width="150" height="200">
        <div class="profile-info">
          <h1>Shengyu Zhang <span class="chinese-name" lang="zh">张圣羽</span></h1>
          <p class="position">Full Professor · Member, IEEE</p>
          <p class="affiliation">Hangzhou Institute of Technology<br>Xidian University, China</p>
          <p class="contact"><a href="mailto:zhangshengyu01@xidian.edu.cn">zhangshengyu01@xidian.edu.cn</a><br>
          <a href="tel:+8613813979512">+86 138 1397 9512</a></p>
        </div>
      </header>
      <section aria-labelledby="about-title">
        <h2 id="about-title">About</h2>
        {about}
      </section>
      <section aria-labelledby="education-title">
        <h2 id="education-title">Education</h2>
        <dl class="education">
          <div><dt>2023</dt><dd><strong>Ph.D.</strong>, The University of Hong Kong, Hong Kong, China</dd></div>
          <div><dt>2019</dt><dd><strong>M.Eng.</strong>, Southeast University, Nanjing, China</dd></div>
          <div><dt>2016</dt><dd><strong>B.Eng.</strong>, Southeast University, Nanjing, China</dd></div>
        </dl>
      </section>
      <section aria-labelledby="selected-title">
        <div class="section-heading"><h2 id="selected-title">Selected Publications</h2><a href="publication.html">All publications <span aria-hidden="true">→</span></a></div>
        <ul class="publication-list">{selected}</ul>
      </section>
      <section aria-labelledby="recent-title">
        <h2 id="recent-title">Recent Activities</h2>
        <ul class="detail-list">
          <li><strong>2026</strong> — Associate Editor, IEEE Open Journal of the Communications Society.</li>
          <li><strong>2026</strong> — Track Co-Chair and <a href="https://www.ieee-icct.org/is.html">Invited Speaker, IEEE ICCT</a>, Communication QoS, Reliability &amp; Modeling.</li>
          <li><strong>2026</strong> — Publication Co-Chair, UCOM; Workshop Co-Chair, IEEE GLOBECOM.</li>
        </ul>
        <p class="more-link"><a href="service.html">Academic service →</a> <span aria-hidden="true">·</span> <a href="award.html">Honors and awards →</a></p>
      </section>
      {raw_blocks}'''


def publications(entries, links):
    years = sorted({entry["year"] for entry in entries if entry["kind"] != "under-review"}, reverse=True)
    options = "".join(f'<option value="{year}">{year}</option>' for year in years)
    count = len(entries)
    output = [f'''<header class="page-heading"><h1>Publications</h1></header>
      <p class="publication-key">The author's name is shown in <strong>bold</strong>; <sup>*</sup> denotes a corresponding author.</p>
      <form class="publication-tools" role="search" hidden>
        <div class="search-field"><label for="paper-search">Search publications</label><input type="search" id="paper-search" placeholder="Title, author, or venue" autocomplete="off"></div>
        <div><label for="paper-year">Year</label><select id="paper-year"><option value="all">All years</option>{options}<option value="under-review">Under review</option></select></div>
        <button type="reset">Reset</button>
      </form>
      <p id="paper-count" class="results-count" role="status" aria-live="polite" hidden>{count} publications</p>
      <p id="no-results" hidden>No publications match your search.</p>''']
    kinds = [("under-review", "Manuscripts under Review"), ("journal", "Peer-Reviewed Journal Papers"), ("conference", "International Conferences")]
    for kind, heading in kinds:
        subset = [entry for entry in entries if entry["kind"] == kind]
        output.append(f'<section class="publication-section" data-section="{kind}"><h2>{heading}</h2>')
        kind_years = [""] if kind == "under-review" else sorted({entry["year"] for entry in subset}, reverse=True)
        for year in kind_years:
            group = subset if not year else [entry for entry in subset if entry["year"] == year]
            output.append('<div class="publication-year-group">')
            if year:
                output.append(f'<h3 id="{kind}-{year}">{year}</h3>')
            output.append('<ul class="publication-list">')
            output.extend(paper_html(entry, links) for entry in group)
            output.append('</ul></div>')
        output.append('</section>')
    return "\n".join(output)


def build(output=ROOT):
    output.mkdir(parents=True, exist_ok=True)
    entries = parse_publications()
    ids = [entry["id"] for entry in entries]
    expected = {f"J{i}" for i in range(1, 43)} | {f"C{i}" for i in range(1, 8)}
    assert len(ids) == len(set(ids)) == len(expected) and set(ids) == expected, "Publication records are missing or duplicated"
    assert next(entry for entry in entries if entry["id"] == "J40")["kind"] == "journal"
    links = json.loads((SOURCES / "publication_links.json").read_text())
    (output / "index.html").write_text(page("index.html", "Home", home(entries, links), "Shengyu Zhang, Full Professor at Xidian University. Research on non-terrestrial networks, digital twins, and intelligent wireless systems."))
    (output / "publication.html").write_text(page("publication.html", "Publications", publications(entries, links), "Journal and conference publications by Shengyu Zhang, including research on satellite networks, rate-splitting, and digital twins.", True))
    (output / "award.html").write_text(page("award.html", "Honors and Awards", '<header class="page-heading"><h1>Honors and Awards</h1></header>\n' + source_sections("awards.jemdoc"), "Research awards, scholarships, and teaching honors received by Shengyu Zhang."))
    (output / "service.html").write_text(page("service.html", "Academic Service", '<header class="page-heading"><h1>Academic Service</h1></header>\n' + source_sections("service.jemdoc"), "Editorial appointments, conference organization, technical committees, and invited talks by Shengyu Zhang."))
    print(f"Built 4 pages; preserved {len(entries)} publication records.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    build(args.output_dir)
