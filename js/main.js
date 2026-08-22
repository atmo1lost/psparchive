async function loadManifest(file) {
  const res = await fetch(file);
  return res.json();
}

function highlightNav() {
  const page = document.body.dataset.page;
  document.querySelectorAll("#sidebar-nav a").forEach(a => {
    if (a.dataset.section === page || (page === "guide" && a.dataset.section === "guides")) {
      a.classList.add("active");
    }
  });
}

function renderGrid(items, kind) {
  const grid = document.getElementById("grid");
  grid.innerHTML = "";
  items.forEach(item => {
    const a = document.createElement("a");
    a.className = "card";
    const singular = kind.endsWith("s") ? kind.slice(0, -1) : kind;
    a.href = `${singular}.html?slug=${item.slug}`;
    const compat = (item.compat || []).map(c => `<span class="tag">${c}</span>`).join("");
    a.innerHTML = `
      <img class="thumb" src="${item.thumb || 'https://via.placeholder.com/400x225/2d2d2d/666?text=No+Preview'}" alt="${item.title}">
      <h3>${item.title}</h3>
      <p>${item.description}</p>
      <div class="compat">${compat}</div>
    `;
    grid.appendChild(a);
  });
}

async function initGrid(kind) {
  highlightNav();
  const items = await loadManifest(`${kind}.json`);
  renderGrid(items, kind);
}

async function initDetail(kind) {
  highlightNav();
  const params = new URLSearchParams(window.location.search);
  const slug = params.get("slug");
  const items = await loadManifest(`${kind}.json`);
  const item = items.find(i => i.slug === slug);
  const content = document.getElementById("content");

  if (!item) {
    content.innerHTML = "<h1>not found</h1><p>no entry matches that page.</p>";
    return;
  }

  const compat = (item.compat || []).map(c => `<span class="tag">${c}</span>`).join("");

  content.innerHTML = `
    <img class="thumb" style="max-width:100%; margin-bottom:16px;"
         src="${item.thumb || 'https://via.placeholder.com/700x394/2d2d2d/666?text=No+Preview'}"
         alt="${item.title}">
    <h1>${item.title}</h1>
    <div id="tags">${compat}</div>
    <p>${item.description}</p>
    <p><a href="${item.download}" class="button">download</a></p>
  `;
}

function currentSlug() {
  const params = new URLSearchParams(window.location.search);
  return params.get("g");
}

function buildSidebar(guides, activeSlug) {
  const list = document.getElementById("sidebar-list");
  list.innerHTML = "";
  guides.forEach(g => {
    const li = document.createElement("li");
    li.dataset.title = g.title.toLowerCase();
    const a = document.createElement("a");
    a.href = `guide.html?g=${g.slug}`;
    a.textContent = g.title;
    if (g.slug === activeSlug) a.classList.add("active");
    li.appendChild(a);
    list.appendChild(li);
  });
}

function wireSearch() {
  const input = document.getElementById("sidebar-search");
  if (!input) return;
  input.addEventListener("input", () => {
    const q = input.value.toLowerCase();
    document.querySelectorAll("#sidebar-list li").forEach(li => {
      li.style.display = li.dataset.title.includes(q) ? "" : "none";
    });
  });
}

async function loadGuide(slug, guides) {
  const meta = guides.find(g => g.slug === slug);
  const contentEl = document.getElementById("content");

  if (!meta) {
    contentEl.innerHTML = "<h1>not found</h1><p>no guide matches that page.</p>";
    return;
  }

  const res = await fetch(`guides/${slug}.md`);
  const raw = await res.text();
  const html = marked.parse(raw);

  const tagsHtml = meta.tags.map(t => `<span class="tag">${t}</span>`).join("");

  contentEl.innerHTML = `<div id="tags">${tagsHtml}</div>${html}`;
}

const lastVisit = localStorage.getItem("pspVisitTime");
const now = Date.now();
const oneHour = 60 * 60 * 1000;

if (!lastVisit || now - Number(lastVisit) >= oneHour) {
  console.log("counting visit");

  fetch("https://countapi.mileshilliard.com/api/v1/hit/psp-visits")
    .then(response => response.json())
    .then(data => {
      localStorage.setItem("pspVisitTime", now);

      document.querySelector(".titleandvisits").innerHTML =
        "poques psp archive<br>visits: " + data.value;
    })
    .catch(error => {
      console.error("failed to get visit count:", error);
    });

} else {
  console.log("getting current visits");

  fetch("https://countapi.mileshilliard.com/api/v1/get/psp-visits")
    .then(response => response.json())
    .then(data => {
      document.querySelector(".titleandvisits").innerHTML =
        "poques psp archive<br>visits: " + data.value;
    })
    .catch(error => {
      console.error("failed to get visit count:", error);
    });
}

async function init() {
  highlightNav();
  wireSearch();
  const guides = await loadManifest("guides.json");
  const slug = currentSlug();
  buildSidebar(guides, slug);
  if (document.body.dataset.page === "guide") {
    await loadGuide(slug || (guides[0] && guides[0].slug), guides);
  }
}

if (document.getElementById("sidebar-list")) {
  init();
}
