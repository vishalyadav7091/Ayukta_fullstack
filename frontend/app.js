const API = (window.AYUKTA_API_URL || "http://localhost:8000").replace(/\/$/, "");
let products = [];
let cart = [];
let filter = "All";

try {
  cart = JSON.parse(localStorage.getItem("ayuktaCart") || "[]");
} catch {
  cart = [];
}

const $ = (id) => document.getElementById(id);
const money = (n) => `₹${Number(n ?? 0).toLocaleString("en-IN")}`;

async function request(path, opts = {}) {
  const res = await fetch(API + path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers || {})
    }
  });

  let data = {};
  try {
    data = await res.json();
  } catch {}

  if (!res.ok) {
    throw new Error(data.detail || data.message || "Request failed");
  }

  return data;
}

function toast(msg) {
  const toastEl = $("toast");
  if (!toastEl) return;
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  setTimeout(() => toastEl.classList.remove("show"), 2400);
}

async function loadProducts() {
  try {
    products = await request("/api/products");
    renderProducts();
  } catch (e) {
    const grid = $("productGrid");
    if (grid) {
      grid.innerHTML = '<p>Could not load products. Start the FastAPI backend and check frontend/config.js.</p>';
    }
    console.error(e);
  }
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[char]));
}

function renderProducts() {
  const q = ($("search")?.value || "").toLowerCase();
  const shown = products.filter((p) => {
    const matchesCategory = filter === "All" || p.category.toLowerCase() === filter.toLowerCase();
    const haystack = `${p.name} ${p.category}`.toLowerCase();
    return matchesCategory && haystack.includes(q);
  });

  const grid = $("productGrid");
  if (!grid) return;

  grid.innerHTML = shown.length
    ? shown.map((p) => `
        <article class="product">
          <div class="product-img">
            <img loading="lazy" src="${esc(p.image_url)}" alt="${esc(p.name)}">
            <span class="tag">${p.featured ? "Featured" : esc(p.category)}</span>
            <button class="add" onclick="addCart(${p.id})">＋ Add to bag · ${money(p.price)}</button>
          </div>
          <div class="product-info">
            <span class="category">${esc(p.category)} / AYUKTA EDIT</span>
            <h3>${esc(p.name)}</h3>
            <div class="price">${money(p.price)} ${p.compare_at_price ? `<span class="old">${money(p.compare_at_price)}</span>` : ""}</div>
          </div>
        </article>
      `).join("")
    : '<p>No products found in this collection.</p>';
}

function saveCart() {
  localStorage.setItem("ayuktaCart", JSON.stringify(cart));
  renderCart();
}

function renderCart() {
  const totalQty = cart.reduce((sum, item) => sum + item.qty, 0);
  const subtotal = cart.reduce((sum, item) => sum + item.price * item.qty, 0);

  const countNode = $("cartCount");
  const bagCountNode = $("bagCount");
  const subtotalNode = $("subtotal");
  const cartItemsNode = $("cartItems");

  if (countNode) countNode.textContent = totalQty;
  if (bagCountNode) bagCountNode.textContent = `(${totalQty})`;
  if (subtotalNode) subtotalNode.textContent = money(subtotal);

  if (!cartItemsNode) return;
  cartItemsNode.innerHTML = cart.length
    ? cart.map((item) => `
        <div class="cart-line">
          <img src="${esc(item.image_url)}" alt="${esc(item.name)}">
          <div>
            <h4>${esc(item.name)}</h4>
            <small>${money(item.price)} · Qty ${item.qty}</small>
            <div>
              <button onclick="qty(${item.id}, -1)">−</button>
              ${item.qty}
              <button onclick="qty(${item.id}, 1)">+</button>
            </div>
          </div>
          <button onclick="removeItem(${item.id})">×</button>
        </div>
      `).join("")
    : '<p style="text-align:center;padding:50px 10px;color:#87776b">Your bag is waiting for something lovely. ✳</p>';
}

function addCart(id) {
  const product = products.find((item) => item.id === id);
  if (!product) return;

  const existing = cart.find((item) => item.id === id);
  if (existing) {
    existing.qty += 1;
  } else {
    cart.push({ id: product.id, name: product.name, price: product.price, image_url: product.image_url, qty: 1 });
  }

  saveCart();
  toast("Added to your bag");
}

function qty(id, delta) {
  const item = cart.find((entry) => entry.id === id);
  if (!item) return;

  item.qty += delta;
  cart = cart.filter((entry) => entry.qty > 0);
  saveCart();
}

function removeItem(id) {
  cart = cart.filter((item) => item.id !== id);
  saveCart();
}

function openCart() {
  const cartEl = $("cart");
  const shade = $("shade");
  if (cartEl) cartEl.classList.add("open");
  if (shade) shade.classList.add("show");
}

function closeCart() {
  const cartEl = $("cart");
  const shade = $("shade");
  if (cartEl) cartEl.classList.remove("open");
  if (shade) shade.classList.remove("show");
}

document.querySelectorAll("#filters button").forEach((button) => {
  button.onclick = () => {
    filter = button.dataset.cat;
    document.querySelectorAll("#filters button").forEach((btn) => {
      btn.classList.toggle("active", btn === button);
    });
    renderProducts();
  };
});

document.querySelectorAll(".collections a").forEach((link) => {
  link.onclick = () => {
    filter = link.dataset.cat;
    document.querySelectorAll("#filters button").forEach((button) => {
      button.classList.toggle("active", button.dataset.cat === filter);
    });
    setTimeout(renderProducts, 20);
  };
});

const allProductsBtn = $("allProducts");
if (allProductsBtn) {
  allProductsBtn.onclick = () => {
    filter = "All";
    document.querySelectorAll("#filters button").forEach((button) => {
      button.classList.toggle("active", button.dataset.cat === "All");
    });
    renderProducts();
  };
}

const cartBtn = $("cartBtn");
if (cartBtn) cartBtn.onclick = openCart;
const closeCartBtn = $("closeCart");
if (closeCartBtn) closeCartBtn.onclick = closeCart;
const shade = $("shade");
if (shade) shade.onclick = closeCart;
const menu = $("menu");
if (menu) menu.onclick = () => $("nav")?.classList.toggle("open");

const searchBtn = $("searchBtn");
if (searchBtn) {
  searchBtn.onclick = () => {
    const searchBar = $("searchBar");
    if (searchBar) searchBar.classList.toggle("open");
    const search = $("search");
    if (search) search.focus();
  };
}

const searchSubmit = $("searchSubmit");
if (searchSubmit) {
  searchSubmit.onclick = () => {
    filter = "All";
    renderProducts();
    $("products")?.scrollIntoView({ behavior: "smooth" });
  };
}

const searchInput = $("search");
if (searchInput) {
  searchInput.addEventListener("input", renderProducts);
}

const accountBtn = $("accountBtn");
if (accountBtn) {
  accountBtn.onclick = () => {
    const token = localStorage.getItem("ayuktaToken");
    if (token) {
      toast("Account token saved in this browser");
      return;
    }

    const email = prompt("Email address for Ayukta account");
    if (!email) return;

    const password = prompt("Password");
    if (!password) return;

    request("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password })
    })
      .then((data) => {
        localStorage.setItem("ayuktaToken", data.access_token);
        toast("Signed in successfully");
      })
      .catch((e) => toast(e.message));
  };
}

const checkoutBtn = $("checkout");
if (checkoutBtn) {
  checkoutBtn.onclick = async () => {
    const token = localStorage.getItem("ayuktaToken");
    if (!cart.length) {
      toast("Your bag is empty");
      return;
    }
    if (!token) {
      toast("Please sign in before placing an order");
      return;
    }

    const customer_name = prompt("Full name for delivery");
    if (!customer_name) return;
    const phone = prompt("Phone number");
    if (!phone) return;
    const address = prompt("Full delivery address");
    if (!address) return;
    const city = prompt("City");
    if (!city) return;
    const postal_code = prompt("PIN / postal code");
    if (!postal_code) return;

    try {
      const order = await request("/api/orders", {
        method: "POST",
        headers: { Authorization: "Bearer " + token },
        body: JSON.stringify({
          items: cart.map((item) => ({ product_id: item.id, quantity: item.qty })),
          customer_name,
          phone,
          address,
          city,
          postal_code
        })
      });

      cart = [];
      saveCart();
      closeCart();
      toast(`Order #${order.id} created. Payment is not configured.`);
    } catch (e) {
      toast(e.message);
    }
  };
}

const newsletterForm = $("newsletter");
if (newsletterForm) {
  newsletterForm.onsubmit = async (event) => {
    event.preventDefault();

    try {
      const data = await request("/api/newsletter", {
        method: "POST",
        body: JSON.stringify({ email: $("email").value })
      });
      const newsMsg = $("newsMsg");
      if (newsMsg) newsMsg.textContent = data.message;
      const emailInput = $("email");
      if (emailInput) emailInput.value = "";
    } catch (err) {
      const newsMsg = $("newsMsg");
      if (newsMsg) newsMsg.textContent = err.message;
    }
  };
}

renderCart();
loadProducts();
