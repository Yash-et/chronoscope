const dateInput = document.querySelector("#dateInput");
const exploreBtn = document.querySelector("#exploreBtn");
const dateLabel = document.querySelector("#dateLabel");
const gallery = document.querySelector("#gallery");
const timeline = document.querySelector("#timeline");
const eventCount = document.querySelector("#eventCount");
const sourceNote = document.querySelector("#sourceNote");
const filters = document.querySelector("#filters");

let allEvents = [];
let activeFilter = "all";

const today = new Date();
const localISODate = `${today.getFullYear()}-${String(today.getMonth()+1).padStart(2,"0")}-${String(today.getDate()).padStart(2,"0")}`;
dateInput.value = localISODate;

function escapeHTML(value = "") {
  return String(value).replace(/[&<>"']/g, char => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
  })[char]);
}

function niceCategory(category) {
  return ({events:"Historical event", births:"Born on this day", deaths:"Remembered", holidays:"Observance"})[category] || category;
}

function renderGallery(images) {
  if (!images || !images.length) {
    gallery.innerHTML = '<div class="gallery-placeholder">No suitable images were found for this date. The historical timeline is still available below.</div>';
    return;
  }
  gallery.innerHTML = images.slice(0,3).map((item, index) => `
    <article class="photo-card">
      <img src="${escapeHTML(item.image)}" alt="${escapeHTML(item.title)}" loading="lazy">
      <div class="photo-caption">
        ${escapeHTML(item.title || "A moment in history")}
        <small>${escapeHTML(item.license || "Image source")} · <a href="${escapeHTML(item.page)}" target="_blank" rel="noopener noreferrer">View source ↗</a></small>
      </div>
    </article>`).join("");
}

function renderEvents() {
  const visible = activeFilter === "all" ? allEvents : allEvents.filter(e => e.category === activeFilter);
  eventCount.textContent = `${visible.length} ${visible.length === 1 ? "MOMENT" : "MOMENTS"} FOUND`;
  if (!visible.length) {
    timeline.innerHTML = '<div class="empty-state">No entries in this category were returned for this date. Try another filter or explore another day.</div>';
    return;
  }
  timeline.innerHTML = visible.map(event => `
    <article class="event-card">
      <div class="event-year">${event.year ?? "—"}</div>
      <div class="event-content">
        <div class="event-type">${niceCategory(event.category)}</div>
        <p>${escapeHTML(event.text)}</p>
        ${event.url ? `<a href="${escapeHTML(event.url)}" target="_blank" rel="noopener noreferrer">Explore this story ↗</a>` : ""}
      </div>
    </article>`).join("");
}

async function loadDate(value) {
  if (!value) return;
  dateLabel.textContent = "EXPLORING THE ARCHIVES…";
  gallery.innerHTML = '<div class="gallery-placeholder">Gathering moments from the archives…</div>';
  timeline.innerHTML = '<div class="loading-card">Finding stories from this date…</div>';
  exploreBtn.disabled = true;
  exploreBtn.style.opacity = ".65";

  try {
    const response = await fetch(`/api/day?date=${encodeURIComponent(value)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Something went wrong.");
    const parsed = new Date(`${value}T12:00:00`);
    dateLabel.textContent = parsed.toLocaleDateString(undefined, {weekday:"long", month:"long", day:"numeric", year:"numeric"}).toUpperCase();
    allEvents = data.events || [];
    activeFilter = "all";
    filters.querySelectorAll("button").forEach(btn => btn.classList.toggle("active", btn.dataset.filter === "all"));
    renderGallery(data.gallery);
    renderEvents();
    sourceNote.textContent = `${data.source}. ${data.note} Image credits and license details link to their source pages.`;
  } catch (error) {
    dateLabel.textContent = "THE ARCHIVES ARE TEMPORARILY UNAVAILABLE";
    gallery.innerHTML = '<div class="gallery-placeholder">We could not load the image archive.</div>';
    timeline.innerHTML = `<div class="empty-state error">${escapeHTML(error.message)}</div>`;
    sourceNote.textContent = "Check your internet connection and try again.";
  } finally {
    exploreBtn.disabled = false;
    exploreBtn.style.opacity = "1";
  }
}

exploreBtn.addEventListener("click", () => loadDate(dateInput.value));
dateInput.addEventListener("keydown", event => {
  if (event.key === "Enter") loadDate(dateInput.value);
});
filters.addEventListener("click", event => {
  const button = event.target.closest("button[data-filter]");
  if (!button) return;
  activeFilter = button.dataset.filter;
  filters.querySelectorAll("button").forEach(btn => btn.classList.toggle("active", btn === button));
  renderEvents();
});

loadDate(localISODate);
