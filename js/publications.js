"use strict";

(() => {
  const form = document.querySelector(".publication-tools");
  if (!form) return;
  const search = document.getElementById("paper-search");
  const year = document.getElementById("paper-year");
  const count = document.getElementById("paper-count");
  const empty = document.getElementById("no-results");
  const papers = Array.from(document.querySelectorAll(".publication"));
  const groups = Array.from(document.querySelectorAll(".publication-year-group"));
  const sections = Array.from(document.querySelectorAll(".publication-section"));
  const searchable = new Map(papers.map(paper => [paper, paper.textContent.toLowerCase()]));

  function filter() {
    const words = search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    let visible = 0;
    papers.forEach(paper => {
      const text = searchable.get(paper);
      const matchesYear = year.value === "all" ||
        (year.value === "under-review" ? paper.dataset.kind === "under-review" :
          paper.dataset.kind !== "under-review" && paper.dataset.year === year.value);
      paper.hidden = !matchesYear || !words.every(word => text.includes(word));
      if (!paper.hidden) visible += 1;
    });
    groups.forEach(group => { group.hidden = !group.querySelector(".publication:not([hidden])"); });
    sections.forEach(section => { section.hidden = !section.querySelector(".publication:not([hidden])"); });
    count.textContent = visible === papers.length ? `${visible} publications` : `${visible} of ${papers.length} publications`;
    empty.hidden = visible !== 0;
  }

  form.hidden = false;
  count.hidden = false;
  form.addEventListener("submit", event => event.preventDefault());
  search.addEventListener("input", filter);
  year.addEventListener("change", filter);
  form.addEventListener("reset", () => setTimeout(filter, 0));
  filter();
})();
