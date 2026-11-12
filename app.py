import base64
import sqlite3
import uuid
from datetime import datetime
from html import escape
from io import BytesIO

import qrcode
import streamlit as st


# ================= CONFIG =================

DB = "tickets.db"
APP_URL = "https://verveverify.streamlit.app"  # Replace with your deployed app URL
FEST_NAME = "AURORA'26"
FEST_TAGLINE = "One Night. Zero Regrets. ✨"

# Set VOLUNTEER_PASSWORD in Streamlit secrets for deployment.
# Example secrets.toml:
# VOLUNTEER_PASSWORD = "use-a-long-unique-password"
VOLUNTEER_PASSWORD = st.secrets.get("VOLUNTEER_PASSWORD", "FEST2026")

st.set_page_config(
    page_title=f"{FEST_NAME} · Tickets",
    page_icon="🎟️",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ================= DATABASE =================

def get_connection():
    return sqlite3.connect(DB, timeout=10)


@st.cache_resource
def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_code TEXT UNIQUE NOT NULL,
                device_id TEXT NOT NULL,
                cgpa REAL NOT NULL,
                discount INTEGER NOT NULL,
                price_paid REAL NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


init_db()


# ================= CORE LOGIC =================

def calculate_discount(cgpa: float) -> int:
    if cgpa > 9.5:
        return 20
    if cgpa > 9.0:
        return 15
    if cgpa > 8.5:
        return 10
    return 0


def make_qr_bytes(url: str) -> bytes:
    buf = BytesIO()
    qrcode.make(url).save(buf, format="PNG")
    return buf.getvalue()


def make_qr_b64(url: str) -> str:
    return base64.b64encode(make_qr_bytes(url)).decode("ascii")


def qr_url(code: str) -> str:
    return f"{APP_URL}/?page=verify&code={code}"


def get_ticket(code: str):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT ticket_code, cgpa, discount, price_paid, used, created_at
            FROM tickets
            WHERE ticket_code = ?
            """,
            (code,),
        ).fetchone()


# ================= STYLING =================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --muted: #aab2ce;
    --border: rgba(255, 255, 255, .13);
    --panel: rgba(21, 26, 47, .78);
}

.stApp {
    color: #f7f7ff;
    font-family: 'DM Sans', sans-serif;
    background:
        radial-gradient(ellipse at 12% 3%, rgba(118, 75, 162, .26), transparent 34%),
        radial-gradient(ellipse at 92% 18%, rgba(255, 100, 200, .16), transparent 32%),
        radial-gradient(ellipse at 48% 100%, rgba(67, 97, 238, .16), transparent 42%),
        #090b16;
}

.block-container {
    max-width: 940px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: #fff;
    font-family: 'Space Grotesk', sans-serif !important;
}

.hero {
    position: relative;
    overflow: hidden;
    margin-bottom: 26px;
    padding: 44px 22px;
    border: 1px solid rgba(255,255,255,.2);
    border-radius: 28px;
    color: white;
    text-align: center;
    background: linear-gradient(120deg, #596fe0, #8650b2 55%, #e77acb);
    box-shadow: 0 18px 60px rgba(118,75,162,.28);
}
.hero h1 {
    margin: 0;
    color: white;
    font-size: clamp(2rem, 7vw, 3.6rem);
    letter-spacing: 2px;
    text-shadow: 0 4px 22px rgba(0,0,0,.22);
}
.hero p {
    margin: 10px 0 0;
    font-size: 1.08rem;
    opacity: .95;
}
.hero .eyebrow {
    margin-bottom: 8px;
    font-size: .75rem;
    font-weight: 800;
    letter-spacing: 3px;
    text-transform: uppercase;
    opacity: .82;
}
.sparkle {
    position: absolute;
    font-size: 2rem;
    opacity: .65;
    animation: float 4s ease-in-out infinite;
}
.sparkle.one { left: 9%; top: 18%; }
.sparkle.two { right: 10%; bottom: 14%; animation-delay: .8s; }

@keyframes float {
    0%, 100% { transform: translateY(0) rotate(0); }
    50% { transform: translateY(-9px) rotate(8deg); }
}

.stButton > button,
.stDownloadButton > button {
    min-height: 48px;
    border: 1px solid rgba(255,255,255,.2);
    border-radius: 14px;
    color: white;
    font-weight: 800;
    background: linear-gradient(100deg, #7665f5, #b653dc);
    box-shadow: 0 8px 24px rgba(120,101,245,.25);
    transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
}
.stButton > button:hover,
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    filter: brightness(1.1);
    box-shadow: 0 12px 30px rgba(181,83,220,.35);
    border-color: rgba(255,255,255,.42);
}

div[data-testid="stMetric"] {
    padding: 14px;
    border: 1px solid var(--border);
    border-radius: 16px;
    background: var(--panel);
}

.tier {
    min-height: 98px;
    padding: 14px 6px;
    border: 1px solid var(--border);
    border-radius: 17px;
    color: var(--muted);
    text-align: center;
    background: rgba(255,255,255,.045);
    transition: transform .2s ease, background .2s ease, box-shadow .2s ease;
}
.tier:hover {
    transform: translateY(-3px);
    background: rgba(255,255,255,.09);
}
.tier .pct {
    color: #e0e4f7;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.8rem;
    font-weight: 800;
}
.tier .rng {
    margin-top: 4px;
    font-size: .72rem;
    line-height: 1.25;
}
.tier.active {
    transform: translateY(-4px) scale(1.03);
    border-color: rgba(255,255,255,.6);
    color: white;
    background: linear-gradient(145deg, rgba(17,153,142,.96), rgba(56,239,125,.86));
    box-shadow: 0 0 26px rgba(56,239,125,.25);
}
.tier.active .pct { color: white; }
.tier .badge {
    margin-top: 6px;
    font-size: .58rem;
    font-weight: 800;
    letter-spacing: 1px;
}

.save-banner {
    margin: 14px 0;
    padding: 17px;
    border: 1px solid rgba(255,255,255,.25);
    border-radius: 16px;
    color: #26152a;
    text-align: center;
    background: linear-gradient(100deg, #ffd166, #ff9f68, #ff78c8);
    box-shadow: 0 10px 30px rgba(255,120,200,.14);
}
.save-banner.none {
    color: #d8def5;
    background: rgba(255,255,255,.07);
}

.ticket {
    max-width: 440px;
    margin: 12px auto;
    overflow: hidden;
    border: 1px solid rgba(255,255,255,.18);
    border-radius: 22px;
    background: linear-gradient(145deg, rgba(30,42,74,.98), rgba(16,20,40,.98));
    box-shadow: 0 18px 50px rgba(0,0,0,.35);
}
.ticket-top {
    padding: 20px;
    color: white;
    text-align: center;
    background: linear-gradient(120deg, #667eea, #9b55bd, #ed72c5);
}
.ticket-top h3 {
    margin: 0;
    color: white;
    letter-spacing: 2px;
}
.ticket-top p {
    margin: 6px 0 0;
    font-size: .85rem;
    opacity: .9;
}
.ticket-body {
    padding: 20px;
    color: #e0e6f0;
    text-align: center;
}
.ticket-qr {
    display: inline-block;
    margin: 8px 0 14px;
    padding: 10px;
    border-radius: 14px;
    background: white;
}
.ticket-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    padding: 10px 6px;
    border-bottom: 1px dashed rgba(255,255,255,.17);
    font-size: .94rem;
}
.ticket-row:last-child { border-bottom: none; }
.ticket-row .lbl { color: var(--muted); }
.ticket-row .val { font-weight: 700; }

.verdict {
    margin: 20px 0;
    padding: 42px 24px;
    border-radius: 22px;
    color: white;
    text-align: center;
    font-size: 1.5rem;
    font-weight: 800;
}
.verdict.ok { background: linear-gradient(130deg, #11998e, #38ef7d); }
.verdict.bad { background: linear-gradient(130deg, #cb2d3e, #ef473a); }

section[data-testid="stSidebar"] {
    border-right: 1px solid var(--border);
    background: rgba(12, 15, 29, .94);
}

.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #67e8f9, #9b7bff, #ff64c8);
}

@media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .hero { padding: 34px 16px; border-radius: 22px; }
    .tier { min-height: 88px; padding: 12px 3px; }
    .tier .pct { font-size: 1.45rem; }
    .tier .rng { font-size: .63rem; }
}
</style>
""", unsafe_allow_html=True)


# ================= UI HELPERS =================

TIERS = [
    ("20%", "CGPA above 9.5"),
    ("15%", "CGPA above 9.0"),
    ("10%", "CGPA above 8.5"),
    ("0%", "CGPA 8.5 or below"),
]


def show_hero(title: str, subtitle: str, eyebrow: str = "AURORA FESTIVAL · 2026"):
    st.markdown(
        f"""
        <div class="hero">
            <span class="sparkle one">✦</span>
            <span class="sparkle two">✧</span>
            <div class="eyebrow">{escape(eyebrow)}</div>
            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def tier_cards(cgpa: float):
    if cgpa > 9.5:
        active_idx = 0
    elif cgpa > 9.0:
        active_idx = 1
    elif cgpa > 8.5:
        active_idx = 2
    else:
        active_idx = 3

    cols = st.columns(4)
    for index, (percent, label) in enumerate(TIERS):
        active = index == active_idx
        badge = '<div class="badge">YOUR TIER</div>' if active else ""
        class_name = "tier active" if active else "tier"
        cols[index].markdown(
            f"""
            <div class="{class_name}">
                <div class="pct">{percent}</div>
                <div class="rng">{label}</div>
                {badge}
            </div>
            """,
            unsafe_allow_html=True,
        )


def ticket_card(code: str, discount: int, price_paid: float, cgpa: float):
    safe_code = escape(code)
    qr_b64 = make_qr_b64(qr_url(code))

    st.markdown(
        f"""
        <div class="ticket">
            <div class="ticket-top">
                <h3>🎟️ {escape(FEST_NAME)} 🎟️</h3>
                <p>Your festival pass</p>
            </div>
            <div class="ticket-body">
                <div class="ticket-qr">
                    <img src="data:image/png;base64,{qr_b64}" width="190" alt="Ticket QR code">
                </div>
                <div class="ticket-row">
                    <span class="lbl">Ticket code</span>
                    <span class="val">{safe_code[:13]}…</span>
                </div>
                <div class="ticket-row">
                    <span class="lbl">CGPA</span>
                    <span class="val">{cgpa:.2f}</span>
                </div>
                <div class="ticket-row">
                    <span class="lbl">Discount</span>
                    <span class="val">{discount}% OFF</span>
                </div>
                <div class="ticket-row">
                    <span class="lbl">Reservation total</span>
                    <span class="val">₹ {price_paid:.2f}</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption("Save your QR ticket and show it to the gate volunteer.")


def download_qr_button(code: str):
    st.download_button(
        label="⬇️ Download ticket QR",
        data=make_qr_bytes(qr_url(code)),
        file_name=f"aurora26_ticket_{code[:8]}.png",
        mime="image/png",
        use_container_width=True,
    )


def show_ticket_from_database(code: str):
    row = get_ticket(code)
    if row is None:
        st.error("No ticket found for that code.")
        return

    ticket_code, cgpa, discount, price_paid, used, _created_at = row

    if used:
        st.warning("This ticket has already been checked in.")
    else:
        st.success("Ticket found. Keep the QR ready for entry.")

    ticket_card(ticket_code, discount, price_paid, cgpa)
    download_qr_button(ticket_code)


# ================= PAGE ROUTING =================

params = st.query_params
page = params.get("page", "")


# ================= VOLUNTEER VERIFICATION =================

if page == "verify":
    code = str(params.get("code", "")).strip()

    if not st.session_state.get("volunteer_ok", False):
        show_hero("Gate Check", "Volunteer access", "AURORA FESTIVAL · STAFF")

        password = st.text_input("Volunteer access code", type="password")

        if st.button("🔐 Sign in", type="primary", use_container_width=True):
            if password == VOLUNTEER_PASSWORD:
                st.session_state.volunteer_ok = True
                st.session_state.pop("gate_verdict", None)
                st.rerun()
            else:
                st.error("That access code is incorrect.")

        st.stop()

    show_hero("Gate Check", "Scan a ticket QR or enter the ticket code", "AURORA FESTIVAL · STAFF")

    if not code:
        st.info("No ticket code was included in the link. Enter one below.")
        code = st.text_input(
            "Ticket code",
            placeholder="Paste or type the full ticket code",
        ).strip()

    if code:
        row = get_ticket(code)

        if row:
            ticket_code, t_cgpa, t_discount, t_price, t_used, _created_at = row
            status = "🟢 NOT USED" if not t_used else "🔴 ALREADY USED"

            st.markdown(
                f"""
                <div class="ticket">
                    <div class="ticket-top"><h3>🎫 Ticket details</h3></div>
                    <div class="ticket-body">
                        <div class="ticket-row">
                            <span class="lbl">Code</span>
                            <span class="val">{escape(ticket_code[:13])}…</span>
                        </div>
                        <div class="ticket-row">
                            <span class="lbl">CGPA</span>
                            <span class="val">{t_cgpa:.2f}</span>
                        </div>
                        <div class="ticket-row">
                            <span class="lbl">Discount</span>
                            <span class="val">{t_discount}% OFF</span>
                        </div>
                        <div class="ticket-row">
                            <span class="lbl">Reservation total</span>
                            <span class="val">₹ {t_price:.2f}</span>
                        </div>
                        <div class="ticket-row">
                            <span class="lbl">Status</span>
                            <span class="val">{status}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if not t_used:
                if st.button("✅ Check in and grant entry", type="primary", use_container_width=True):
                    with get_connection() as conn:
                        cursor = conn.execute(
                            """
                            UPDATE tickets
                            SET used = 1
                            WHERE ticket_code = ? AND used = 0
                            """,
                            (code,),
                        )
                        conn.commit()

                    if cursor.rowcount == 1:
                        st.session_state.gate_verdict = "ok"
                    else:
                        st.session_state.gate_verdict = "used"
                    st.rerun()
            else:
                st.session_state.gate_verdict = "used"

        else:
            st.error("❌ No ticket found with that code.")
            st.session_state.gate_verdict = "none"

    verdict = st.session_state.get("gate_verdict")

    if verdict == "ok":
        st.markdown(
            '<div class="verdict ok">✅ VALID<br>Entry granted</div>',
            unsafe_allow_html=True,
        )
        st.balloons()
    elif verdict == "used":
        st.markdown(
            '<div class="verdict bad">⛔ ALREADY USED<br>Deny entry</div>',
            unsafe_allow_html=True,
        )
    elif verdict == "none":
        st.markdown(
            '<div class="verdict bad">❌ INVALID<br>No such ticket</div>',
            unsafe_allow_html=True,
        )

    st.stop()


# ================= TICKET RECOVERY =================

if page == "myticket":
    show_hero("My Ticket", "Retrieve your festival pass", "AURORA FESTIVAL · TICKET RECOVERY")

    lookup = st.text_input(
        "Enter your ticket code",
        placeholder="Paste the full ticket code here",
    ).strip()

    if st.button("🔍 Find my ticket", type="primary", use_container_width=True):
        row = get_ticket(lookup) if lookup else None

        if row is None:
            st.error("No ticket found. Check the code and try again.")
        else:
            st.session_state.recovered_ticket = row[0]
            st.rerun()

    recovered_code = st.session_state.get("recovered_ticket")
    if recovered_code:
        show_ticket_from_database(recovered_code)

    st.stop()


# ================= MAIN PURCHASE / RESERVATION VIEW =================

show_hero(FEST_NAME, FEST_TAGLINE)

# Sidebar stats
with st.sidebar:
    st.markdown("## ✨ Festival dashboard")
    with get_connection() as conn:
        sold = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        reserved_total = conn.execute(
            "SELECT COALESCE(SUM(price_paid), 0) FROM tickets"
        ).fetchone()[0]
        checked_in = conn.execute(
            "SELECT COUNT(*) FROM tickets WHERE used = 1"
        ).fetchone()[0]

    col1, col2 = st.columns(2)
    col1.metric("Reserved", sold)
    col2.metric("Checked in", checked_in)
    st.metric("Reserved total", f"₹ {reserved_total:,.0f}")
    st.divider()
    st.caption("🎓 Discounts are based on CGPA.")
    st.caption("🔎 Already have a ticket? Use the recovery link below.")
    st.page_link(
        f"{APP_URL}/?page=myticket",
        label="🎫 Recover my ticket",
        icon="🔗",
    )

st.markdown("### 🎓 Unlock your student discount")
st.caption("Move the slider to see your discount tier update.")

cgpa = st.slider(
    "Your CGPA",
    min_value=0.0,
    max_value=10.0,
    value=8.0,
    step=0.01,
    format="%.2f",
)

tier_cards(cgpa)

st.progress(cgpa / 10, text=f"CGPA: {cgpa:.2f} / 10.00")

st.markdown("### 🎟️ Choose your ticket price")
price = st.number_input(
    "Ticket price (₹)",
    min_value=0.0,
    value=500.0,
    step=50.0,
    help="Your discount and reservation total update automatically.",
)

discount = calculate_discount(cgpa)
savings = price * discount / 100
final_price = round(price - savings, 2)

if discount:
    st.markdown(
        f"""
        <div class="save-banner">
            🎉 You unlocked <b>{discount}% OFF</b><br>
            You save <b>₹ {savings:.2f}</b> and your reservation total is
            <b>₹ {final_price:.2f}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
        <div class="save-banner none">
            ✨ Your discount starts when your CGPA is above 8.5.
        </div>
        """,
        unsafe_allow_html=True,
    )

st.caption("This app creates a ticket reservation; it does not process a payment.")

# Reservation action
if st.button("🎟️ Reserve my ticket", type="primary", use_container_width=True):
    device_id = st.session_state.setdefault("device_id", str(uuid.uuid4()))

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT ticket_code FROM tickets WHERE device_id = ?",
            (device_id,),
        ).fetchone()

    if existing:
        st.session_state.my_ticket = existing[0]
        st.warning("A ticket is already linked to this session. Showing it below.")
    else:
        ticket_code = str(uuid.uuid4())

        try:
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO tickets
                        (ticket_code, device_id, cgpa, discount, price_paid, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ticket_code,
                        device_id,
                        cgpa,
                        discount,
                        final_price,
                        datetime.now().isoformat(timespec="seconds"),
                    ),
                )
                conn.commit()

            st.session_state.my_ticket = ticket_code
            st.toast("Ticket reserved! 🎉")
            st.balloons()

        except sqlite3.IntegrityError:
            st.error("Could not create the reservation. Please try again.")

# Show the current session's ticket
current_code = st.session_state.get("my_ticket")

if current_code:
    st.divider()
    st.markdown("### 🎉 Your festival pass")
    show_ticket_from_database(current_code)
