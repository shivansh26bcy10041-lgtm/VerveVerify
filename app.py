import streamlit as st
import sqlite3
import uuid
import qrcode
import base64
from datetime import datetime
from io import BytesIO

# ================= CONFIG =================
DB = "tickets.db"
APP_URL = "https://verveverify.streamlit.app"   # ← REPLACE with YOUR EXACT URL from browser bar
FEST_NAME = "AURORA'26"
FEST_TAGLINE = "One Night. Zero Regrets. ✨"
VOLUNTEER_PASSWORD = st.secrets.get("VOLUNTEER_PASSWORD", "FEST2026")

st.set_page_config(page_title=f"{FEST_NAME} · Tickets", page_icon="🎟️", layout="centered")

# ================= CORE LOGIC =================
def calculate_discount(cgpa: float) -> int:
    if cgpa > 9.5: return 20
    elif cgpa > 9.0: return 15
    elif cgpa > 8.5: return 10
    return 0

@st.cache_resource
def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_code TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                cgpa REAL NOT NULL,
                discount INTEGER NOT NULL,
                price_paid REAL NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
init_db()

def make_qr_b64(url: str) -> str:
    buf = BytesIO()
    qrcode.make(url).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def make_qr_bytes(url: str) -> bytes:
    buf = BytesIO()
    qrcode.make(url).save(buf, format="PNG")
    return buf.getvalue()

def qr_url(code: str) -> str:
    return f"{APP_URL}/?page=verify&code={code}"

# ================= CUSTOM CSS =================
st.markdown("""
<style>
    .stApp { background: #0e1117; }
    .hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 55%, #f093fb 100%);
        border-radius: 20px; padding: 34px 28px; text-align: center;
        color: white; margin-bottom: 22px; box-shadow: 0 8px 32px rgba(118, 75, 162, 0.4);
    }
    .hero h1 { margin: 0; font-size: 2.6em; letter-spacing: 2px; }
    .hero p { margin: 8px 0 0; font-size: 1.1em; opacity: 0.9; }
    .tier {
        border-radius: 14px; padding: 14px 8px; text-align: center;
        background: #1a2030; border: 2px solid #2a3245;
        transition: all 0.3s ease; color: #8892b0;
    }
    .tier .pct { font-size: 1.9em; font-weight: 800; color: #4a5568; }
    .tier .rng { font-size: 0.78em; margin-top: 4px; }
    .tier.active {
        background: linear-gradient(135deg, #11998e, #38ef7d);
        border-color: #38ef7d; color: white;
        box-shadow: 0 0 24px rgba(56, 239, 125, 0.45); transform: scale(1.06);
    }
    .tier.active .pct { color: white; }
    .save-banner {
        background: linear-gradient(90deg, #f7971e, #ffd200);
        border-radius: 12px; padding: 14px 18px; text-align: center;
        font-weight: 700; color: #3b2708; font-size: 1.05em; margin: 10px 0;
    }
    .save-banner.none { background: #2a3245; color: #8892b0; }
    .ticket {
        background: linear-gradient(145deg, #1e2a4a, #16213e);
        border-radius: 18px; padding: 0; overflow: hidden;
        border: 1px solid #3a4a6b; max-width: 400px; margin: 0 auto;
        box-shadow: 0 12px 40px rgba(0,0,0,0.5);
    }
    .ticket-top {
        background: linear-gradient(135deg, #667eea, #764ba2);
        padding: 18px; text-align: center; color: white;
    }
    .ticket-top h3 { margin: 0; letter-spacing: 3px; }
    .ticket-body { padding: 20px; text-align: center; color: #e0e6f0; }
    .ticket-qr {
        background: white; border-radius: 12px; padding: 10px;
        display: inline-block; margin: 10px 0;
    }
    .ticket-row {
        display: flex; justify-content: space-between;
        padding: 8px 6px; border-bottom: 1px dashed #3a4a6b; font-size: 0.95em;
    }
    .ticket-row:last-child { border-bottom: none; }
    .ticket-row .lbl { color: #8892b0; }
    .ticket-row .val { font-weight: 700; }
    .verdict {
        border-radius: 20px; padding: 50px 30px; text-align: center;
        font-size: 1.6em; font-weight: 800; margin: 20px 0;
    }
    .verdict.ok { background: linear-gradient(135deg, #11998e, #38ef7d); color: white; }
    .verdict.bad { background: linear-gradient(135deg, #cb2d3e, #ef473a); color: white; }
</style>
""", unsafe_allow_html=True)

# ================= HELPERS =================
TIERS = [
    ("20%", "CGPA above 9.5"),
    ("15%", "9.0 – 9.5"),
    ("10%", "8.5 – 9.0"),
    ("0%", "below 8.5"),
]

def tier_cards(cgpa: float):
    active_idx = 3
    if cgpa > 9.5: active_idx = 0
    elif cgpa > 9.0: active_idx = 1
    elif cgpa > 8.5: active_idx = 2
    cols = st.columns(4)
    for i, (pct, rng) in enumerate(TIERS):
        cls = "tier active" if i == active_idx else "tier"
        cols[i].markdown(
            f'<div class="{cls}"><div class="pct">{pct}</div><div class="rng">{rng}</div></div>',
            unsafe_allow_html=True,
        )

def ticket_card(code: str, discount: int, price_paid: float, cgpa: float, qr_b64: str):
    st.markdown(f"""
    <div class="ticket">
      <div class="ticket-top"><h3>🎟️ {FEST_NAME} 🎟️</h3></div>
      <div class="ticket-body">
        <div class="ticket-qr"><img src="data:image/png;base64,{qr_b64}" width="200"></div>
        <div class="ticket-row"><span class="lbl">Ticket Code</span><span class="val">{code[:13]}…</span></div>
        <div class="ticket-row"><span class="lbl">CGPA</span><span class="val">{cgpa:.2f}</span></div>
        <div class="ticket-row"><span class="lbl">Discount</span><span class="val">{discount}% OFF</span></div>
        <div class="ticket-row"><span class="lbl">Amount Paid</span><span class="val">₹ {price_paid:.2f}</span></div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.caption("📸 Screenshot this · Show the QR at the entrance")

def download_qr_button(code: str):
    qr_bytes = make_qr_bytes(qr_url(code))
    st.download_button(
        label="⬇️ Download QR Ticket (PNG)",
        data=qr_bytes,
        file_name=f"aurora26_ticket_{code[:8]}.png",
        mime="image/png",
        use_container_width=True,
    )
    st.info("💾 Save this PNG to your gallery — it works even without internet.", icon="📸")

# ================= VERIFICATION VIEW (VOLUNTEER) =================
params = st.query_params
if params.get("page") == "verify":
    code = params.get("code", "")
    if "volunteer_ok" not in st.session_state:
        st.markdown(f'<div class="hero"><h1>🛡️ Gate Check</h1><p>{FEST_NAME} staff access</p></div>',
                    unsafe_allow_html=True)
        pw = st.text_input("Volunteer access code", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            if pw == VOLUNTEER_PASSWORD:
                st.session_state.volunteer_ok = True
                st.rerun()
            else:
                st.error("Wrong code")
        st.stop()

    st.markdown('<div class="hero"><h1>🛡️ Gate Check</h1><p>Scan result for this ticket</p></div>',
                unsafe_allow_html=True)

    if not code:
        st.info("📷 No code in URL — enter it manually")
        code = st.text_input("Ticket code", placeholder="paste or type ticket code").strip()

    if code:
        with sqlite3.connect(DB) as conn:
            row = conn.execute(
                "SELECT cgpa, discount, price_paid, used FROM tickets WHERE ticket_code = ?",
                (code,)).fetchone()

        if row:
            t_cgpa, t_disc, t_price, t_used = row
            status = "🟢 NOT USED" if t_used == 0 else "🔴 ALREADY USED"
            st.markdown(f"""
            <div class="ticket">
              <div class="ticket-top"><h3>🎫 Ticket Details</h3></div>
              <div class="ticket-body">
                <div class="ticket-row"><span class="lbl">Code</span><span class="val">{code[:13]}…</span></div>
                <div class="ticket-row"><span class="lbl">CGPA</span><span class="val">{t_cgpa:.2f}</span></div>
                <div class="ticket-row"><span class="lbl">Discount</span><span class="val">{t_disc}% OFF</span></div>
                <div class="ticket-row"><span class="lbl">Paid</span><span class="val">₹ {t_price:.2f}</span></div>
                <div class="ticket-row"><span class="lbl">Status</span><span class="val">{status}</span></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("✅ Check & Grant Entry", type="primary", use_container_width=True,
                     disabled=(row is None)):
            with sqlite3.connect(DB) as conn:
                cur = conn.execute(
                    "UPDATE tickets SET used = 1 WHERE ticket_code = ? AND used = 0", (code,))
                conn.commit()
                if cur.rowcount == 1:
                    st.session_state.verdict = "ok"
                else:
                    r = conn.execute("SELECT used FROM tickets WHERE ticket_code = ?", (code,)).fetchone()
                    st.session_state.verdict = "none" if r is None else "used"

    v = st.session_state.get("verdict")
    if v == "ok":
        st.markdown('<div class="verdict ok">✅ VALID<br>Entry Granted</div>', unsafe_allow_html=True)
        st.balloons()
    elif v == "used":
        st.markdown('<div class="verdict bad">⛔ ALREADY USED<br>Deny Entry</div>', unsafe_allow_html=True)
    elif v == "none":
        st.markdown('<div class="verdict bad">❌ INVALID<br>No such ticket</div>', unsafe_allow_html=True)
    st.stop()

# ================= MY TICKET VIEW (BUYER RECOVERY) =================
if params.get("page") == "myticket":
    st.markdown('<div class="hero"><h1>🎫 My Ticket</h1><p>Retrieve your pass anytime</p></div>',
                unsafe_allow_html=True)

    lookup = st.text_input("Enter your ticket code", placeholder="e.g. 3f2a9c1e-...")
    if st.button("🔍 Find My Ticket", type="primary", use_container_width=True):
        with sqlite3.connect(DB) as conn:
            row = conn.execute(
                "SELECT ticket_code, cgpa, discount, price_paid, used FROM tickets WHERE ticket_code = ?",
                (lookup.strip(),)).fetchone()
        if row is None:
            st.error("❌ No ticket found with that code. Check for typos.")
        else:
            code, t_cgpa, t_disc, t_price, t_used = row
            st.session_state.my_ticket = code
            st.session_state.purchase = {"discount": t_disc, "final": t_price}
            st.session_state.my_cgpa = t_cgpa
            st.success("✅ Ticket found!" + (" (Already checked in)" if t_used else ""))

    if "my_ticket" in st.session_state and st.session_state.get("purchase"):
        info = st.session_state["purchase"]
        qr_b64 = make_qr_b64(qr_url(st.session_state.my_ticket))
        ticket_card(st.session_state.my_ticket, info["discount"], info["final"],
                    st.session_state.get("my_cgpa", 0.0), qr_b64)
        download_qr_button(st.session_state.my_ticket)
    st.stop()

# ================= MAIN / PURCHASE VIEW =================
# --- Hero ---
st.markdown(f"""
<div class="hero">
  <h1>🎟️ {FEST_NAME}</h1>
  <p>{FEST_TAGLINE}</p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar: live stats ---
with st.sidebar:
    st.header("📊 Live Stats")
    with sqlite3.connect(DB) as conn:
        sold = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        given = conn.execute("SELECT COALESCE(SUM(price_paid),0) FROM tickets").fetchone()[0]
        entered = conn.execute("SELECT COUNT(*) FROM tickets WHERE used = 1").fetchone()[0]
    c1, c2 = st.columns(2)
    c1.metric("Tickets sold", sold)
    c2.metric("Checked in", entered)
    st.metric("Revenue collected", f"₹ {given:,.0f}")
    st.divider()
    st.caption("🎓 Discounts: 20% · 15% · 10% based on CGPA")

# --- Discount tiers ---
st.subheader("🎯 Your CGPA unlocks your discount")
cgpa = st.slider("Slide to your CGPA", 0.0, 10.0, 8.0, 0.01, format="%.2f")
tier_cards(cgpa)

# --- Live savings preview ---
price = st.number_input("Ticket price (₹)", 0.0, value=500.0, step=50.0)
discount = calculate_discount(cgpa)
savings = price * discount / 100

if discount > 0:
    st.markdown(
        f'<div class="save-banner">🎉 You unlock <b>{discount}% OFF</b> — '
        f'you save <b>₹ {savings:.0f}</b> and pay only <b>₹ {price - savings:.2f}</b></div>',
        unsafe_allow_html=True)
else:
    st.markdown('<div class="save-banner none">📖 Push your CGPA above 8.5 to start saving!</div>',
                unsafe_allow_html=True)

st.progress(cgpa / 10)

# --- Purchase ---
if st.button("🛒 Buy Ticket Now", type="primary", use_container_width=True):
    device_id = st.session_state.setdefault("device_id", str(uuid.uuid4()))
    with sqlite3.connect(DB) as conn:
        existing = conn.execute(
            "SELECT ticket_code FROM tickets WHERE device_id = ?", (device_id,)).fetchone()

    if existing:
        st.warning("⚠️ You already own a ticket — showing it below.")
        st.session_state.my_ticket = existing[0]
        st.session_state.purchase = None
    else:
        final_price = round(price - savings, 2)
        code = str(uuid.uuid4())
        with sqlite3.connect(DB) as conn:
            conn.execute(
                """INSERT INTO tickets
                   (ticket_code, device_id, cgpa, discount, price_paid, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (code, device_id, cgpa, discount, final_price, datetime.now().isoformat()))
        st.session_state.my_ticket = code
        st.session_state.my_cgpa = cgpa
        st.session_state.purchase = {"discount": discount, "final": final_price}
        st.toast("Ticket booked successfully! 🎉")
        st.balloons()

# --- Show my ticket (persists across reruns) ---
if "my_ticket" in st.session_state:
    st.divider()
    info = st.session_state.get("purchase")
    if info:
        st.success(f"✅ Payment confirmed — {info['discount']}% off, paid ₹ {info['final']:.2f}")
    qr_b64 = make_qr_b64(qr_url(st.session_state.my_ticket))
    ticket_card(st.session_state.my_ticket,
                info["discount"] if info else 0,
                info["final"] if info else 0,
                st.session_state.get("my_cgpa", cgpa), qr_b64)
    download_qr_button(st.session_state.my_ticket)