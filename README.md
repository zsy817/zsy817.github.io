# Shengyu Zhang's academic homepage

Static website published at https://zsy817.github.io/.

The public URLs and portrait are preserved. The site uses local CSS and JavaScript,
with no build dependencies. The homepage includes a third-party visitor map.

## Edit and rebuild

Editable text lives in `sources/`:

- `index.jemdoc`: biography and research interests.
- `publication.jemdoc`: all journal and conference records; preserve the J/C identifiers.
- `awards.jemdoc`: honors, scholarships, and teaching awards.
- `service.jemdoc`: editorial service, conferences, committees, and talks.
- `publication_links.json`: verified exact-title DOI links only.

Run `python3 scripts/build_site.py` from the repository. The builder uses only the
Python standard library. Update `UPDATED` and the footer's ISO date in the builder
when publishing a subsequent update. The profile, education, and selected-paper
identifiers are also defined in the builder.

Publication groups follow the bibliographic year in each citation. The site shows
every publication without JavaScript; JavaScript progressively adds search and
year filters. `css/site.css` controls the responsive layout.

## Preview and publish

Run `python3 -m http.server 8765` and visit http://localhost:8765/.

GitHub Pages serves the HTML files from the root of the `main` branch. Commit and
push the generated HTML, source files, CSS, and JavaScript together. Keep credentials
outside this repository. Never publish the original project's `token.rtf`.

## Visitor map

The bottom of `sources/index.jemdoc` contains a native jemdoc raw HTML block
(`~~~`, `{}{raw}`, HTML, `~~~`). It embeds the Flag Counter world map with
the site's counter ID `5FDt`. The builder preserves the raw HTML without
escaping it, so rebuilding does not remove the map.

The owner approved activation and the provider's terms on 7 October 2026.
The map image request sends the visitor's IP to Flag Counter for country-level
statistics. The homepage links to the provider's privacy policy. It starts with
new widget loads, not historical website traffic. No email or paid account was
created, and no third-party JavaScript is required. Keep this counter ID private
to this site's embed so unrelated traffic does not enter its statistics.
