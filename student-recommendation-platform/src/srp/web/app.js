const CAMPUS = { lat: 19.1044, lon: 72.8365 };
const CATEGORY_NAMES = { pg_hostel: "PG / Hostel", restaurant: "Restaurant", stationery: "Stationery shop", sports: "Sports facility", event: "Event" };
const PRICE = ["Free", "Low", "Medium", "High"];
const state = { token: sessionStorage.getItem("token"), role: sessionStorage.getItem("role"), name: sessionStorage.getItem("name"), view: "search", lastSearch: null };
const main = document.getElementById("main");
const nav = document.getElementById("nav");
const banner = document.getElementById("banner");

function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "class") el.className = value;
    else if (key.startsWith("on")) el.addEventListener(key.slice(2), value);
    else if (value !== false && value !== null && value !== undefined) el.setAttribute(key, value === true ? "" : value);
  }
  for (const child of children.flat()) el.append(child instanceof Node ? child : document.createTextNode(String(child ?? "")));
  return el;
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json" };
  if (state.token) headers.Authorization = "Bearer " + state.token;
  const response = await fetch(path, { method: options.method || "GET", headers, body: options.body ? JSON.stringify(options.body) : undefined });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && state.token && data.error === "LoginRequired") signOut(false);
    throw new Error(data.message || "Request failed");
  }
  return data;
}

function say(text, kind = "ok") {
  banner.replaceChildren(h("p", { class: "msg " + kind }, text));
}

function field(label, control) {
  return h("label", {}, label, control);
}

function option(value, text, selected) {
  return h("option", { value, selected: !!selected }, text);
}

function categorySelect(id, includeAny) {
  return h("select", { id }, includeAny ? option("", "All types") : [], Object.entries(CATEGORY_NAMES).map(([v, t]) => option(v, t)));
}

function stars(rating) {
  return rating > 0 ? `${rating.toFixed(1)} / 5` : "No ratings yet";
}

function signOut(callApi = true) {
  if (callApi && state.token) api("/logout", { method: "POST" }).catch(() => {});
  state.token = state.role = state.name = null;
  sessionStorage.clear();
  show("search");
}

function renderNav() {
  const items = [["search", "Search"], ["events", "Events"]];
  if (state.token) items.push(["foryou", "For you"], ["notifications", "Notifications"]);
  if (state.role === "admin") items.push(["admin", "Admin"]);
  items.push(state.token ? ["logout", "Log out"] : ["account", "Log in / Register"]);
  nav.replaceChildren(...items.map(([key, text]) => h("button", { type: "button", "aria-current": key === state.view ? "page" : false, onclick: () => (key === "logout" ? signOut() : show(key)) }, text)));
}

function show(view, arg) {
  state.view = view;
  banner.replaceChildren();
  renderNav();
  const views = { search: viewSearch, events: viewEvents, foryou: viewForYou, notifications: viewNotifications, account: viewAccount, admin: viewAdmin, detail: viewDetail };
  main.replaceChildren(h("p", {}, "Loading..."));
  Promise.resolve(views[view](arg)).catch((err) => say(err.message, "err"));
}

function listingCard(item) {
  const parts = [h("span", { class: "badge" }, CATEGORY_NAMES[item.category]), item.event_date ? h("span", { class: "badge" }, item.event_date) : ""];
  const meta = [`Rating: ${stars(item.rating)}`];
  if (item.review_count !== undefined) meta.push(`${item.review_count} verified review(s)`);
  if (item.category !== "event") meta.push(`Cost: ${PRICE[item.price_level]}`);
  if (item.distance_km !== undefined) meta.push(`${item.distance_km} km away`);
  return h("article", { class: "card" }, h("h3", {}, item.name), h("p", {}, parts), h("p", { class: "meta" }, meta.join(" | ")), h("p", {}, item.description), h("button", { type: "button", class: "secondary", onclick: () => show("detail", item.id) }, "View details of " + item.name));
}

function resultsBox(data) {
  if (!data.results.length) return h("p", { class: "msg" }, data.message || "No results.");
  return h("section", { "aria-label": "Results" }, data.results.map(listingCard));
}

function viewSearch() {
  const out = h("div", { id: "results" });
  const form = h("form", { class: "card", "aria-label": "Search places" },
    h("div", { class: "row" }, field("Category", categorySelect("category")),
      field("Latitude", h("input", { id: "lat", type: "number", step: "any", value: CAMPUS.lat, required: true })),
      field("Longitude", h("input", { id: "lon", type: "number", step: "any", value: CAMPUS.lon, required: true })),
      field("Radius (km)", h("input", { id: "radius", type: "number", step: "any", min: "0.5", max: "100", value: "5" }))),
    h("div", { class: "row" },
      field("Maximum cost", h("select", { id: "price" }, option("", "Any"), PRICE.map((p, i) => option(i, p)))),
      field("Minimum rating", h("select", { id: "rating" }, option("", "Any"), [1, 2, 3, 4, 5].map((n) => option(n, n + " and above"))))),
    h("div", { class: "actions" },
      h("button", { type: "submit", class: "primary" }, "Search"),
      h("button", { type: "button", class: "secondary", onclick: () => { form.querySelector("#price").value = ""; form.querySelector("#rating").value = ""; form.querySelector("#radius").value = "5"; form.requestSubmit(); } }, "Reset filters"),
      h("button", { type: "button", class: "secondary", onclick: locate }, "Use my location")));
  function locate() {
    if (!navigator.geolocation) return say("Location is not available in this browser.", "err");
    navigator.geolocation.getCurrentPosition((pos) => { form.querySelector("#lat").value = pos.coords.latitude.toFixed(5); form.querySelector("#lon").value = pos.coords.longitude.toFixed(5); say("Location updated."); }, () => say("Location permission was denied. Enter coordinates manually.", "err"));
  }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const q = new URLSearchParams({ category: form.querySelector("#category").value, lat: form.querySelector("#lat").value, lon: form.querySelector("#lon").value, radius: form.querySelector("#radius").value });
    if (form.querySelector("#price").value) q.set("max_price", form.querySelector("#price").value);
    if (form.querySelector("#rating").value) q.set("min_rating", form.querySelector("#rating").value);
    try { banner.replaceChildren(); out.replaceChildren(resultsBox(await api("/search?" + q))); } catch (err) { say(err.message, "err"); }
  });
  main.replaceChildren(h("h2", {}, "Search nearby places"), form, out);
}

async function viewEvents() {
  const out = h("div");
  const form = h("form", { class: "card", "aria-label": "Filter events" },
    h("div", { class: "row" }, field("Event type", h("select", { id: "etype" }, option("", "All types"), ["Cultural", "Sports", "Technical"].map((t) => option(t, t)))),
      field("From date", h("input", { id: "efrom", type: "date" })), field("To date", h("input", { id: "eto", type: "date" }))),
    h("div", { class: "actions" }, h("button", { type: "submit", class: "primary" }, "Apply filters"), h("button", { type: "button", class: "secondary", onclick: () => { form.reset(); form.requestSubmit(); } }, "Reset filters")));
  async function load() {
    const q = new URLSearchParams();
    for (const [id, key] of [["etype", "event_type"], ["efrom", "date_from"], ["eto", "date_to"]]) if (form.querySelector("#" + id).value) q.set(key, form.querySelector("#" + id).value);
    out.replaceChildren(resultsBox(await api("/events?" + q)));
  }
  form.addEventListener("submit", (event) => { event.preventDefault(); load().catch((err) => say(err.message, "err")); });
  main.replaceChildren(h("h2", {}, "Upcoming events"), form, out);
  await load();
}

async function viewDetail(id) {
  const item = await api("/listings/" + id);
  const details = Object.entries(item.details).map(([k, v]) => h("li", {}, `${k.replaceAll("_", " ")}: ${v}`));
  const reviews = item.reviews.length ? item.reviews.map((r) => h("article", { class: "card" }, h("p", {}, h("strong", {}, r.author), ` rated ${r.rating} / 5`), h("p", {}, r.comment),
    state.token ? h("button", { type: "button", class: "secondary", onclick: () => reportReview(r.id) }, "Report this review") : "")) : [h("p", { class: "msg" }, "No published reviews yet.")];
  const children = [h("button", { type: "button", class: "secondary", onclick: () => show("search") }, "Back to search"),
    h("section", { class: "card" }, h("h2", {}, item.name), h("p", {}, h("span", { class: "badge" }, CATEGORY_NAMES[item.category])), h("p", {}, item.description),
      h("p", { class: "meta" }, `Rating: ${stars(item.rating)} from ${item.review_count} verified review(s)`), item.address ? h("p", { class: "meta" }, item.address) : "", h("ul", {}, details)),
    h("h2", {}, "Student reviews"), reviews];
  if (state.role === "student") {
    const form = h("form", { class: "card", "aria-label": "Write a review" }, h("h3", {}, "Write a review"),
      field("Rating", h("select", { id: "stars", required: true }, [5, 4, 3, 2, 1].map((n) => option(n, n + " star" + (n > 1 ? "s" : ""))))),
      field("Comment", h("textarea", { id: "comment", rows: "3", maxlength: "1000", required: true })), h("button", { type: "submit", class: "primary" }, "Submit review"));
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      try { await api("/reviews", { method: "POST", body: { rec_id: id, rating: Number(form.querySelector("#stars").value), comment: form.querySelector("#comment").value } }); form.reset(); say("Review submitted. It will appear after administrator approval."); } catch (err) { say(err.message, "err"); }
    });
    children.push(form);
  } else if (!state.token) children.push(h("p", { class: "msg" }, "Log in with your college email to write a review."));
  main.replaceChildren(...children);
}

async function reportReview(id) {
  const reason = prompt("Why are you reporting this review?");
  if (!reason) return;
  try { await api(`/reviews/${id}/report`, { method: "POST", body: { reason } }); say("Thanks. The review is now under review by an administrator."); } catch (err) { say(err.message, "err"); }
}

async function viewForYou() {
  const me = await api("/me");
  const out = h("div");
  const boxes = me.categories.map((c) => h("label", {}, h("span", {}, h("input", { type: "checkbox", name: "pref", value: c, checked: me.preferences.includes(c) }), " " + CATEGORY_NAMES[c])));
  const form = h("form", { class: "card", "aria-label": "Preferences" }, h("fieldset", {}, h("legend", {}, "What are you interested in?"), boxes), h("button", { type: "submit", class: "primary" }, "Save and show recommendations"));
  async function load() { out.replaceChildren(resultsBox(await api(`/recommend?lat=${CAMPUS.lat}&lon=${CAMPUS.lon}`).then((d) => ({ results: d.results, message: "No recommendations match your preferences nearby." })))); }
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try { await api("/me/preferences", { method: "PUT", body: { categories: [...form.querySelectorAll("input:checked")].map((i) => i.value) } }); say("Preferences saved."); await load(); } catch (err) { say(err.message, "err"); }
  });
  main.replaceChildren(h("h2", {}, "Recommended for you"), form, out);
  await load();
}

async function viewNotifications() {
  const [list, me] = await Promise.all([api("/notifications"), api("/me")]);
  const items = list.length ? list.map((n) => h("article", { class: "card" + (n.read ? "" : " unread") }, h("p", {}, h("span", { class: "badge" }, n.category), n.read ? "" : h("strong", {}, "New: "), n.message),
    h("p", { class: "meta" }, n.created_at.replace("T", " ").slice(0, 16)), n.read ? "" : h("button", { type: "button", class: "secondary", onclick: async () => { await api(`/notifications/${n.id}/read`, { method: "POST" }); show("notifications"); } }, "Mark as read"))) : [h("p", { class: "msg" }, "No notifications yet.")];
  const names = ["event", "review", "moderation", "account"];
  const form = h("form", { class: "card", "aria-label": "Notification settings" }, h("fieldset", {}, h("legend", {}, "Turn off these notification types"), names.map((c) => h("label", {}, h("span", {}, h("input", { type: "checkbox", value: c, checked: me.disabled_notifications.includes(c) }), " " + c)))), h("button", { type: "submit", class: "primary" }, "Save settings"));
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try { await api("/me/notification-settings", { method: "PUT", body: { disabled: [...form.querySelectorAll("input:checked")].map((i) => i.value) } }); say("Notification settings saved."); } catch (err) { say(err.message, "err"); }
  });
  main.replaceChildren(h("h2", {}, "Notifications"), ...items, form);
}

async function viewAccount() {
  const colleges = await api("/colleges");
  const login = h("form", { class: "card", "aria-label": "Log in" }, h("h2", {}, "Log in"),
    field("College email", h("input", { id: "login-email", type: "email", required: true, autocomplete: "username" })),
    field("Password", h("input", { id: "login-password", type: "password", required: true, autocomplete: "current-password" })), h("button", { type: "submit", class: "primary" }, "Log in"));
  const register = h("form", { class: "card", "aria-label": "Register" }, h("h2", {}, "Create an account"),
    field("Full name", h("input", { id: "reg-name", required: true, autocomplete: "name" })),
    field("College", h("select", { id: "reg-college", required: true }, colleges.map((c) => option(c.id, c.name)))),
    field("College email", h("input", { id: "reg-email", type: "email", required: true, autocomplete: "email" })),
    field("Password (8 or more characters)", h("input", { id: "reg-password", type: "password", minlength: "8", required: true, autocomplete: "new-password" })), h("button", { type: "submit", class: "primary" }, "Register"));
  async function signIn(email, password) {
    const session = await api("/login", { method: "POST", body: { email, password } });
    state.token = session.token; state.role = session.role; state.name = session.name;
    for (const key of ["token", "role", "name"]) sessionStorage.setItem(key, state[key]);
    show(session.role === "admin" ? "admin" : "search");
    say(`Welcome, ${session.name}.`);
  }
  login.addEventListener("submit", (event) => { event.preventDefault(); signIn(login.querySelector("#login-email").value, login.querySelector("#login-password").value).catch((err) => say(err.message, "err")); });
  register.addEventListener("submit", async (event) => {
    event.preventDefault();
    const email = register.querySelector("#reg-email").value, password = register.querySelector("#reg-password").value;
    try {
      await api("/register", { method: "POST", body: { name: register.querySelector("#reg-name").value, email, password, college_id: register.querySelector("#reg-college").value } });
      await signIn(email, password);
      say("Account created and college email verified. You are logged in.");
    } catch (err) { say(err.message, "err"); }
  });
  main.replaceChildren(login, register);
}

async function viewAdmin() {
  const [queue, users, audit, cities, colleges] = await Promise.all([api("/admin/reviews"), api("/admin/users"), api("/admin/audit"), api("/cities"), api("/colleges")]);
  const act = (path, body) => async () => { try { await api(path, { method: "POST", body }); show("admin"); } catch (err) { say(err.message, "err"); } };
  const reviewCards = queue.length ? queue.map((r) => h("article", { class: "card" }, h("p", {}, h("span", { class: "badge" }, r.status), h("strong", {}, r.listing), ` by ${r.author}: ${r.rating} / 5`), h("p", {}, r.comment), r.reports.length ? h("p", { class: "meta" }, "Reports: " + r.reports.join("; ")) : "",
    h("div", { class: "actions" }, h("button", { type: "button", class: "primary", onclick: act(`/reviews/${r.id}/validate`, { approve: true }) }, "Approve / keep"), h("button", { type: "button", class: "danger", onclick: act(`/reviews/${r.id}/validate`, { approve: false }) }, "Reject / remove")))) : [h("p", { class: "msg" }, "No reviews are waiting for moderation.")];
  const userRows = users.map((u) => h("tr", {}, h("td", {}, u.name), h("td", {}, u.email), h("td", {}, u.verified ? "Verified" : "Unverified"), h("td", {}, u.suspended ? "Suspended" : "Active"),
    h("td", {}, h("div", { class: "actions" }, !u.verified ? h("button", { type: "button", class: "secondary", onclick: act(`/admin/users/${u.id}/verify`, {}) }, "Verify") : "", u.suspended ? h("button", { type: "button", class: "secondary", onclick: act(`/admin/users/${u.id}/reinstate`, {}) }, "Reinstate " + u.name) : h("button", { type: "button", class: "danger", onclick: act(`/admin/users/${u.id}/suspend`, {}) }, "Suspend " + u.name)))));
  const listingForm = h("form", { class: "card", "aria-label": "Add listing" }, h("h3", {}, "Add a listing"),
    h("div", { class: "row" }, field("Name", h("input", { id: "l-name", required: true })), field("Category", categorySelect("l-cat")), field("City", h("select", { id: "l-city" }, cities.map((c) => option(c.id, c.name))))),
    h("div", { class: "row" }, field("Latitude", h("input", { id: "l-lat", type: "number", step: "any", required: true, value: CAMPUS.lat })), field("Longitude", h("input", { id: "l-lon", type: "number", step: "any", required: true, value: CAMPUS.lon })),
      field("Cost level", h("select", { id: "l-price" }, PRICE.map((p, i) => option(i, p)))), field("Event date (events only)", h("input", { id: "l-date", type: "date" }))),
    field("Description", h("input", { id: "l-desc" })), h("button", { type: "submit", class: "primary" }, "Add listing"));
  listingForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const f = (id) => listingForm.querySelector("#" + id).value;
    const body = { name: f("l-name"), category: f("l-cat"), city_id: f("l-city"), lat: Number(f("l-lat")), lon: Number(f("l-lon")), price_level: Number(f("l-price")), description: f("l-desc") };
    if (body.category === "event") { body.event_date = f("l-date"); body.details = { event_type: "Cultural" }; }
    try { await api("/admin/listings", { method: "POST", body }); say("Listing added."); listingForm.reset(); } catch (err) { say(err.message, "err"); }
  });
  const collegeForm = h("form", { class: "card", "aria-label": "Add college" }, h("h3", {}, "Add a college"),
    h("div", { class: "row" }, field("College name", h("input", { id: "c-name", required: true })), field("Email domain", h("input", { id: "c-domain", required: true, placeholder: "example.edu.in" })), field("City", h("select", { id: "c-city" }, cities.map((c) => option(c.id, c.name))))), h("button", { type: "submit", class: "primary" }, "Add college"));
  collegeForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const f = (id) => collegeForm.querySelector("#" + id).value;
    try { await api("/admin/colleges", { method: "POST", body: { name: f("c-name"), domain: f("c-domain"), city_id: f("c-city") } }); say("College added."); collegeForm.reset(); } catch (err) { say(err.message, "err"); }
  });
  const cityForm = h("form", { class: "card", "aria-label": "Add city" }, h("h3", {}, "Add a city"),
    h("div", { class: "row" }, field("City name", h("input", { id: "ct-name", required: true })), field("State", h("input", { id: "ct-state", required: true }))), h("button", { type: "submit", class: "primary" }, "Add city"));
  cityForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try { await api("/admin/cities", { method: "POST", body: { name: cityForm.querySelector("#ct-name").value, state: cityForm.querySelector("#ct-state").value } }); say("City added."); cityForm.reset(); } catch (err) { say(err.message, "err"); }
  });
  const auditRows = audit.slice(0, 15).map((e) => h("tr", {}, h("td", {}, e.at.replace("T", " ").slice(0, 19)), h("td", {}, e.actor), h("td", {}, e.action), h("td", {}, e.target)));
  main.replaceChildren(h("h2", {}, "Administrator dashboard"), h("h3", {}, "Reviews awaiting moderation"), ...reviewCards,
    h("h3", {}, "Students"), h("table", {}, h("caption", { class: "meta" }, `${colleges.length} college(s), ${cities.length} city(ies) registered`), h("thead", {}, h("tr", {}, ["Name", "Email", "Verification", "Status", "Actions"].map((t) => h("th", { scope: "col" }, t)))), h("tbody", {}, userRows)),
    listingForm, collegeForm, cityForm, h("h3", {}, "Recent audit log"), h("table", {}, h("thead", {}, h("tr", {}, ["Time", "Actor", "Action", "Target"].map((t) => h("th", { scope: "col" }, t)))), h("tbody", {}, auditRows)));
}

show("search");
