import base64
import re
import sqlite3
import textwrap
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
FEST_TAGLINE = "One Night. Zero Regrets."

# Set VOLUNTEER_PASSWORD in Streamlit secrets for deployment.
VOLUNTEER_PASSWORD = st.secrets.get("VOLUNTEER_PASSWORD", "FEST2026")

st.set_page_config(
    page_title=f"{FEST_NAME} · Tickets",
    page_icon="🎟️",
    layout="centered",
    initial_sidebar_state="collapsed",
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

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --bg: #07060f;
    --muted: #a9a6c9;
    --border: rgba(255,255,255,.12);
    --glass: rgba(255,255,255,.055);
    --pink: #ff4fd8;
    --violet: #8b5cf6;
    --cyan: #22d3ee;
    --lime: #a3e635;
    --amber: #fbbf24;
}

/* ---------- hide default chrome ---------- */
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.stDeployButton { display: none; }

/* ---------- animated aurora background ---------- */
.stApp {
    color: #f6f5ff;
    font-family: 'Outfit', sans-serif;
    background: var(--bg);
    overflow-x: hidden;
}
.stApp::before, .stApp::after {
    content: "";
    position: fixed;
    z-index: 0;
    width: 60vmax; height: 60vmax;
    border-radius: 50%;
    filter: blur(90px);
    opacity: .38;
    pointer-events: none;
}
.stApp::before {
    top: -22vmax; left: -18vmax;
    background: radial-gradient(circle, #7c3aed, transparent 65%);
    animation: drift1 16s ease-in-out infinite alternate;
}
.stApp::after {
    bottom: -26vmax; right: -20vmax;
    background: radial-gradient(circle, #ff4fd8, #22d3ee 55%, transparent 70%);
    animation: drift2 20s ease-in-out infinite alternate;
}
@keyframes drift1 { to { transform: translate(14vmax, 10vmax) scale(1.15); } }
@keyframes drift2 { to { transform: translate(-12vmax, -8vmax) scale(1.1); } }

.block-container {
    position: relative; z-index: 1;
    max-width: 760px;
    padding-top: 1.4rem;
    padding-bottom: 4rem;
}

h1, h2, h3, h4 { font-family: 'Space Grotesk', sans-serif !important; color: #fff; }

/* ---------- marquee ---------- */
.marquee {
    overflow: hidden;
    margin: 0 -1rem 18px;
    padding: 9px 0;
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
    background: rgba(255,255,255,.04);
    backdrop-filter: blur(8px);
}
.marquee-track {
    display: inline-flex;
    white-space: nowrap;
    gap: 34px;
    animation: scroll 26s linear infinite;
    font-size: .78rem; font-weight: 700;
    letter-spacing: 3px; text-transform: uppercase;
    color: var(--muted);
}
.marquee-track b { color: var(--pink); }
@keyframes scroll { to { transform: translateX(-50%); } }

/* ---------- hero ---------- */
.hero {
    position: relative;
    overflow: hidden;
    margin-bottom: 26px;
    padding: 54px 22px 46px;
    border-radius: 32px;
    text-align: center;
    border: 1px solid rgba(255,255,255,.18);
    background:
        linear-gradient(135deg, rgba(139,92,246,.35), rgba(255,79,216,.22) 55%, rgba(34,211,238,.22)),
        rgba(14,12,30,.7);
    backdrop-filter: blur(16px);
    box-shadow: 0 24px 80px rgba(139,92,246,.30), inset 0 1px 0 rgba(255,255,255,.25);
}
.hero::before {
    content: "";
    position: absolute; inset: -2px;
    background: conic-gradient(from 0deg, transparent, rgba(255,79,216,.55), transparent 30%, rgba(34,211,238,.5), transparent 60%);
    animation: spin 9s linear infinite;
    opacity: .35;
    z-index: 0;
}
.hero::after {
    content: "";
    position: absolute; inset: 1px;
    border-radius: 31px;
    background: linear-gradient(160deg, rgba(20,16,44,.92), rgba(12,10,28,.9));
    z-index: 0;
}
.hero > * { position: relative; z-index: 1; }
@keyframes spin { to { transform: rotate(360deg); } }

.hero .eyebrow {
    display: inline-block;
    padding: 6px 14px;
    margin-bottom: 14px;
    border: 1px solid var(--border);
    border-radius: 999px;
    background: var(--glass);
    font-size: .7rem; font-weight: 800;
    letter-spacing: 3px; text-transform: uppercase;
    color: #dcd8ff;
}
.hero h1 {
    margin: 0;
    font-size: clamp(2.6rem, 11vw, 5rem);
    font-weight: 700;
    letter-spacing: 3px;
    line-height: 1.05;
    background: linear-gradient(90deg, #fff, #ffb3ef, #8be9ff, #fff);
    background-size: 250% 100%;
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 6s linear infinite;
    filter: drop-shadow(0 6px 28px rgba(255,79,216,.35));
}
@keyframes shine { to { background-position: -250% 0; } }
.hero p { margin: 14px 0 0; font-size: 1.15rem; color: #d9d6f7; }

.hero .orb {
    position: absolute; z-index: 1;
    border-radius: 50%;
    animation: float 5s ease-in-out infinite;
}
.hero .orb.a { width: 14px; height: 14px; left: 10%; top: 24%; background: var(--cyan); box-shadow: 0 0 22px var(--cyan); }
.hero .orb.b { width: 10px; height: 10px; right: 12%; top: 18%; background: var(--pink); box-shadow: 0 0 22px var(--pink); animation-delay: .9s; }
.hero .orb.c { width: 18px; height: 18px; right: 20%; bottom: 16%; background: var(--amber); box-shadow: 0 0 26px var(--amber); animation-delay: 1.7s; }
.hero .orb.d { width: 8px; height: 8px; left: 18%; bottom: 20%; background: var(--lime); box-shadow: 0 0 20px var(--lime); animation-delay: 2.4s; }
@keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-14px); } }

.chips { display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; margin-top: 22px; }
.chip {
    padding: 7px 14px; border-radius: 999px;
    border: 1px solid var(--border); background: var(--glass);
    font-size: .82rem; font-weight: 600; color: #e7e4ff;
}

/* ---------- section titles ---------- */
.sec-title {
    display: flex; align-items: center; gap: 12px;
    margin: 30px 0 6px;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.45rem; font-weight: 700; color: #fff;
}
.sec-title .num {
    display: grid; place-items: center;
    width: 34px; height: 34px; border-radius: 11px;
    font-size: .95rem; font-weight: 800;
    background: linear-gradient(135deg, var(--violet), var(--pink));
    box-shadow: 0 6px 20px rgba(255,79,216,.35);
}
.sec-sub { margin: 0 0 12px 46px; color: var(--muted); font-size: .92rem; }

/* ---------- widgets ---------- */
div[data-testid="stSlider"] { padding: 6px 4px 0; }
div[data-testid="stSlider"] label p { color: var(--muted) !important; font-weight: 600; }
div[data-testid="stSlider"] div[role="slider"] {
    background: linear-gradient(135deg, var(--pink), var(--violet)) !important;
    border: 3px solid #fff !important;
    box-shadow: 0 0 0 6px rgba(255,79,216,.22), 0 6px 18px rgba(255,79,216,.5) !important;
    height: 22px !important; width: 22px !important;
}
div[data-testid="stSliderThumbValue"] { color: #fff !important; font-weight: 800 !important; }

div[data-testid="stNumberInput"] input, div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,.06) !important;
    border-radius: 14px !important;
    color: #fff !important;
    font-weight: 600;
}
div[data-testid="stNumberInput"] > div > div, div[data-testid="stTextInput"] > div > div {
    border-radius: 14px !important;
    border: 1px solid var(--border) !important;
    background: rgba(255,255,255,.06) !important;
}
div[data-testid="stNumberInput"] > div > div:focus-within,
div[data-testid="stTextInput"] > div > div:focus-within {
    border-color: var(--pink) !important;
    box-shadow: 0 0 0 3px rgba(255,79,216,.25);
}
label[data-testid="stWidgetLabel"] p { color: var(--muted) !important; font-weight: 600; }

.stButton > button, .stDownloadButton > button {
    min-height: 50px;
    border: 1px solid rgba(255,255,255,.18);
    border-radius: 16px;
    color: #fff; font-weight: 800; font-size: 1rem;
    background: rgba(255,255,255,.07);
    transition: all .2s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    transform: translateY(-2px);
    border-color: rgba(255,255,255,.4);
    background: rgba(255,255,255,.13);
    color: #fff;
}
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
    min-height: 58px; font-size: 1.1rem;
    background: linear-gradient(100deg, #7c3aed, #ff4fd8, #fb923c);
    background-size: 200% 100%;
    box-shadow: 0 12px 36px rgba(255,79,216,.38);
    animation: btnflow 5s ease infinite;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-3px) scale(1.01);
    box-shadow: 0 18px 46px rgba(255,79,216,.55);
}
@keyframes btnflow { 0%,100% { background-position: 0 0; } 50% { background-position: 100% 0; } }

.stProgress > div > div > div > div { background: linear-gradient(90deg, var(--cyan), var(--violet), var(--pink)); }
.stProgress p { color: var(--muted) !important; }

div[data-testid="stMetric"] {
    padding: 14px; border: 1px solid var(--border);
    border-radius: 16px; background: var(--glass);
}
section[data-testid="stSidebar"] { background: rgba(10,9,22,.96); border-right: 1px solid var(--border); }

/* ---------- tier cards ---------- */
.tier {
    position: relative;
    min-height: 112px; padding: 16px 6px 12px;
    border: 1px solid var(--border); border-radius: 20px;
    text-align: center; color: var(--muted);
    background: var(--glass);
    transition: all .25s ease;
    opacity: .75;
}
.tier .pct { font-family: 'Space Grotesk', sans-serif; font-size: 2rem; font-weight: 700; color: #e6e3ff; }
.tier .off { font-size: .62rem; font-weight: 800; letter-spacing: 2px; margin-top: -2px; }
.tier .rng { margin-top: 6px; font-size: .72rem; line-height: 1.25; }
.tier .badge {
    margin-top: 8px; display: inline-block;
    padding: 3px 9px; border-radius: 999px;
    font-size: .58rem; font-weight: 800; letter-spacing: 1.5px;
    background: rgba(0,0,0,.3);
}
.tier.active { opacity: 1; transform: translateY(-6px) scale(1.04); color: #fff; border-color: rgba(255,255,255,.7); }
.tier.active .pct { color: #fff; }
.tier.active.t0 { background: linear-gradient(145deg, #f59e0b, #ff4fd8); box-shadow: 0 0 40px rgba(255,79,216,.55); }
.tier.active.t1 { background: linear-gradient(145deg, #7c3aed, #ec4899); box-shadow: 0 0 40px rgba(139,92,246,.55); }
.tier.active.t2 { background: linear-gradient(145deg, #0ea5e9, #22d3ee); box-shadow: 0 0 40px rgba(34,211,238,.5); }
.tier.active.t3 { background: linear-gradient(145deg, #475569, #64748b); box-shadow: 0 0 30px rgba(100,116,139,.4); }

/* ---------- price summary ---------- */
.summary {
    margin: 16px 0 8px; padding: 20px 22px;
    border: 1px solid var(--border); border-radius: 22px;
    background: var(--glass); backdrop-filter: blur(12px);
}
.summary .row { display: flex; justify-content: space-between; padding: 7px 0; color: var(--muted); font-weight: 500; }
.summary .row b { color: #fff; }
.summary .row.save b { color: var(--lime); }
.summary .total {
    display: flex; justify-content: space-between; align-items: baseline;
    margin-top: 10px; padding-top: 14px;
    border-top: 1px dashed rgba(255,255,255,.22);
}
.summary .total span { font-weight: 700; color: #fff; }
.summary .total strong {
    font-family: 'Space Grotesk', sans-serif; font-size: 2.2rem;
    background: linear-gradient(90deg, #fff, #ffb3ef);
    -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.unlock {
    margin: 14px 0 0; padding: 14px 18px; border-radius: 16px; text-align: center; font-weight: 700;
    color: #1d0f26;
    background: linear-gradient(100deg, #fde68a, #fdba74, #f9a8d4);
    box-shadow: 0 10px 30px rgba(249,168,212,.22);
}
.unlock.none { color: #cfcbf0; background: var(--glass); border: 1px dashed var(--border); box-shadow: none; font-weight: 500; }

.note { margin: 8px 2px 14px; text-align: center; font-size: .8rem; color: var(--muted); }

/* ---------- ticket ---------- */
.ticket {
    position: relative;
    max-width: 430px; margin: 16px auto;
    border-radius: 26px; overflow: hidden;
    background: linear-gradient(160deg, rgba(34,30,70,.98), rgba(14,12,32,.98));
    border: 1px solid rgba(255,255,255,.2);
    box-shadow: 0 26px 70px rgba(0,0,0,.5), 0 0 60px rgba(139,92,246,.25);
}
.ticket::before {
    content: ""; position: absolute; inset: 0; pointer-events: none; z-index: 2;
    background: linear-gradient(115deg, transparent 35%, rgba(255,255,255,.12) 50%, transparent 65%);
    background-size: 250% 100%;
    animation: holo 5s linear infinite;
}
@keyframes holo { from { background-position: 150% 0; } to { background-position: -150% 0; } }
.ticket-top {
    padding: 24px 20px 20px; text-align: center; color: #fff;
    background: linear-gradient(120deg, #7c3aed, #d946ef, #fb7185);
}
.ticket-top h3 { margin: 0; letter-spacing: 3px; font-size: 1.5rem; color: #fff; }
.ticket-top p { margin: 6px 0 0; font-size: .85rem; letter-spacing: 2px; text-transform: uppercase; opacity: .92; }
.ticket-tear {
    position: relative; height: 22px; margin: 0;
    background:
        radial-gradient(circle at 0 50%, var(--bg) 11px, transparent 12px) left / 51% 100% no-repeat,
        radial-gradient(circle at 100% 50%, var(--bg) 11px, transparent 12px) right / 51% 100% no-repeat;
}
.ticket-tear::after {
    content: ""; position: absolute; left: 22px; right: 22px; top: 50%;
    border-top: 2px dashed rgba(255,255,255,.22);
}
.ticket-body { padding: 6px 22px 24px; text-align: center; color: #e6e3ff; }
.ticket-qr {
    display: inline-block; margin: 6px 0 16px; padding: 12px;
    border-radius: 18px; background: #fff;
    box-shadow: 0 0 0 4px rgba(255,79,216,.35), 0 14px 36px rgba(255,79,216,.3);
}
.ticket-qr img { display: block; border-radius: 6px; }
.ticket-row { display: flex; justify-content: space-between; gap: 12px; padding: 11px 4px; border-bottom: 1px dashed rgba(255,255,255,.15); font-size: .95rem; }
.ticket-row:last-child { border-bottom: none; }
.ticket-row .lbl { color: var(--muted); }
.ticket-row .val { font-weight: 700; color: #fff; }

.pill { display: inline-block; padding: 4px 12px; border-radius: 999px; font-size: .78rem; font-weight: 800; letter-spacing: 1px; }
.pill.ok { background: rgba(163,230,53,.16); color: var(--lime); border: 1px solid rgba(163,230,53,.4); }
.pill.bad { background: rgba(251,113,133,.16); color: #fb7185; border: 1px solid rgba(251,113,133,.4); }

/* ---------- verdict ---------- */
.verdict {
    margin: 20px 0; padding: 46px 24px; border-radius: 26px;
    color: #fff; text-align: center; font-size: 1.7rem; font-weight: 800; line-height: 1.4;
    animation: pop .4s ease;
}
.verdict small { display: block; font-size: 1rem; font-weight: 600; opacity: .9; }
.verdict.ok { background: linear-gradient(130deg, #059669, #34d399); box-shadow: 0 0 60px rgba(52,211,153,.45); }
.verdict.bad { background: linear-gradient(130deg, #be123c, #fb7185); box-shadow: 0 0 60px rgba(251,113,133,.4); }
@keyframes pop { from { transform: scale(.92); opacity: 0; } to { transform: scale(1); opacity: 1; } }

.reco-link {
    display: block; margin-top: 14px; padding: 11px; text-align: center;
    border: 1px solid var(--border); border-radius: 14px;
    background: var(--glass); color: #fff !important; text-decoration: none !important; font-weight: 600;
}
.reco-link:hover { background: rgba(255,255,255,.12); }

@media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .hero { padding: 44px 14px 36px; border-radius: 24px; }
    .tier { min-height: 100px; padding: 12px 2px 10px; }
    .tier .pct { font-size: 1.5rem; }
    .tier .rng { font-size: .62rem; }
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ================= UI HELPERS =================

def html(markup: str):
    """Render HTML without Markdown treating indented lines as code blocks."""
    cleaned = textwrap.dedent(markup)
    cleaned = re.sub(r"\n\s*\n", "\n", cleaned).strip()
    cleaned = "\n".join(line.strip() for line in cleaned.splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


TIERS = [
    ("20", "CGPA above 9.5"),
    ("15", "CGPA above 9.0"),
    ("10", "CGPA above 8.5"),
    ("0", "CGPA 8.5 or below"),
]


def marquee():
    items = "".join(
        f"<span><b>✦</b> {t}</span>"
        for t in [FEST_NAME, "Live music", "Food street", "Student discounts", "Gate entry via QR", FEST_TAGLINE]
    )
    html(f'<div class="marquee"><div class="marquee-track">{items}{items}</div></div>')


def show_hero(title: str, subtitle: str, eyebrow: str = "Aurora Festival · 2026", chips=None):
    chip_html = ""
    if chips:
        chip_html = '<div class="chips">' + "".join(f'<span class="chip">{escape(c)}</span>' for c in chips) + "</div>"
    html(
        f"""
        <div class="hero">
            <span class="orb a"></span><span class="orb b"></span>
            <span class="orb c"></span><span class="orb d"></span>
            <div class="eyebrow">{escape(eyebrow)}</div>
            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
            {chip_html}
        </div>
        """
    )


def section(num: str, title: str, sub: str = ""):
    sub_html = f'<div class="sec-sub">{escape(sub)}</div>' if sub else ""
    html(f'<div class="sec-title"><span class="num">{num}</span>{escape(title)}</div>{sub_html}')


def tier_cards(cgpa: float):
    active_idx = 0 if cgpa > 9.5 else 1 if cgpa > 9.0 else 2 if cgpa > 8.5 else 3
    cols = st.columns(4)
    for i, (percent, label) in enumerate(TIERS):
        active = i == active_idx
        badge = '<div class="badge">YOUR TIER</div>' if active else ""
        cls = f"tier t{i} active" if active else f"tier t{i}"
        cols[i].markdown(
            f'<div class="{cls}"><div class="pct">{percent}%</div><div class="off">OFF</div>'
            f'<div class="rng">{label}</div>{badge}</div>',
            unsafe_allow_html=True,
        )


def ticket_card(code: str, discount: int, price_paid: float, cgpa: float, used: bool = False):
    qr_b64 = make_qr_b64(qr_url(code))
    status = '<span class="pill bad">CHECKED IN</span>' if used else '<span class="pill ok">VALID</span>'
    html(
        f"""
        <div class="ticket">
            <div class="ticket-top">
                <h3>🎟️ {escape(FEST_NAME)}</h3>
                <p>Festival pass</p>
            </div>
            <div class="ticket-tear"></div>
            <div class="ticket-body">
                <div class="ticket-qr">
                    <img src="data:image/png;base64,{qr_b64}" width="190" alt="Ticket QR code">
                </div>
                <div class="ticket-row"><span class="lbl">Status</span><span class="val">{status}</span></div>
                <div class="ticket-row"><span class="lbl">Ticket code</span><span class="val">{escape(code[:13])}…</span></div>
                <div class="ticket-row"><span class="lbl">CGPA</span><span class="val">{cgpa:.2f}</span></div>
                <div class="ticket-row"><span class="lbl">Discount</span><span class="val">{discount}% OFF</span></div>
                <div class="ticket-row"><span class="lbl">Reservation total</span><span class="val">₹ {price_paid:,.2f}</span></div>
            </div>
        </div>
        """
    )
    st.markdown('<div class="note">Save your QR and show it to the gate volunteer.</div>', unsafe_allow_html=True)


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

    ticket_card(ticket_code, discount, price_paid, cgpa, bool(used))
    download_qr_button(ticket_code)
    with st.expander("🔑 Your full ticket code (needed to recover this ticket)"):
        st.code(ticket_code, language=None)


# ================= PAGE ROUTING =================

params = st.query_params
page = params.get("page", "")


# ================= VOLUNTEER VERIFICATION =================

if page == "verify":
    code = str(params.get("code", "")).strip()

    if not st.session_state.get("volunteer_ok", False):
        show_hero("Gate Check", "Volunteer access only", "Aurora Festival · Staff")

        password = st.text_input("Volunteer access code", type="password")

        if st.button("🔐 Sign in", type="primary", use_container_width=True):
            if password == VOLUNTEER_PASSWORD:
                st.session_state.volunteer_ok = True
                st.session_state.pop("gate_result", None)
                st.rerun()
            else:
                st.error("That access code is incorrect.")

        st.stop()

    show_hero("Gate Check", "Scan a ticket QR or enter the ticket code", "Aurora Festival · Staff")

    if not code:
        st.info("No ticket code was included in the link. Enter one below.")
        code = st.text_input(
            "Ticket code",
            placeholder="Paste or type the full ticket code",
        ).strip()

    verdict = None

    if code:
        row = get_ticket(code)

        if row:
            ticket_code, t_cgpa, t_discount, t_price, t_used, _created_at = row
            status = (
                '<span class="pill ok">NOT USED</span>'
                if not t_used
                else '<span class="pill bad">ALREADY USED</span>'
            )

            html(
                f"""
                <div class="ticket">
                    <div class="ticket-top"><h3>🎫 Ticket details</h3></div>
                    <div class="ticket-tear"></div>
                    <div class="ticket-body">
                        <div class="ticket-row"><span class="lbl">Code</span><span class="val">{escape(ticket_code[:13])}…</span></div>
                        <div class="ticket-row"><span class="lbl">CGPA</span><span class="val">{t_cgpa:.2f}</span></div>
                        <div class="ticket-row"><span class="lbl">Discount</span><span class="val">{t_discount}% OFF</span></div>
                        <div class="ticket-row"><span class="lbl">Reservation total</span><span class="val">₹ {t_price:,.2f}</span></div>
                        <div class="ticket-row"><span class="lbl">Status</span><span class="val">{status}</span></div>
                    </div>
                </div>
                """
            )

            if not t_used:
                if st.button("✅ Check in and grant entry", type="primary", use_container_width=True):
                    with get_connection() as conn:
                        cursor = conn.execute(
                            "UPDATE tickets SET used = 1 WHERE ticket_code = ? AND used = 0",
                            (code,),
                        )
                        conn.commit()

                    st.session_state.gate_result = (code, "ok" if cursor.rowcount == 1 else "used")
                    st.session_state.celebrate = cursor.rowcount == 1
                    st.rerun()
            else:
                # Show VALID only for the check-in that just happened in this session.
                just_checked_in = st.session_state.get("gate_result") == (code, "ok")
                verdict = "ok" if just_checked_in else "used"
        else:
            st.error("❌ No ticket found with that code.")
            verdict = "none"

    if verdict == "ok":
        html('<div class="verdict ok">✅ VALID<small>Entry granted</small></div>')
        if st.session_state.pop("celebrate", False):
            st.balloons()
    elif verdict == "used":
        html('<div class="verdict bad">⛔ ALREADY USED<small>Deny entry</small></div>')
    elif verdict == "none":
        html('<div class="verdict bad">❌ INVALID<small>No such ticket</small></div>')

    st.stop()


# ================= TICKET RECOVERY =================

if page == "myticket":
    show_hero("My Ticket", "Retrieve your festival pass", "Aurora Festival · Ticket recovery")

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

marquee()
show_hero(
    FEST_NAME,
    FEST_TAGLINE,
    chips=["🎓 Up to 20% off for toppers", "📱 Instant QR pass", "⚡ 30-second reservation"],
)

# Sidebar stats
with st.sidebar:
    st.markdown("## ✨ Festival dashboard")
    with get_connection() as conn:
        sold = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        reserved_total = conn.execute("SELECT COALESCE(SUM(price_paid), 0) FROM tickets").fetchone()[0]
        checked_in = conn.execute("SELECT COUNT(*) FROM tickets WHERE used = 1").fetchone()[0]

    col1, col2 = st.columns(2)
    col1.metric("Reserved", sold)
    col2.metric("Checked in", checked_in)
    st.metric("Reserved total", f"₹ {reserved_total:,.0f}")
    st.divider()
    st.caption("🎓 Discounts are based on CGPA.")
    html(f'<a class="reco-link" href="{APP_URL}/?page=myticket" target="_self">🎫 Recover my ticket</a>')

# ---- Step 1: CGPA ----
section("1", "Unlock your student discount", "Slide to your CGPA and watch your tier light up.")

cgpa = st.slider("Your CGPA", min_value=0.0, max_value=10.0, value=8.0, step=0.01, format="%.2f")

tier_cards(cgpa)
st.progress(cgpa / 10, text=f"CGPA: {cgpa:.2f} / 10.00")

# ---- Step 2: Price ----
section("2", "Choose your ticket price", "Pick a quick amount or type your own.")

st.session_state.setdefault("price", 500.0)


def set_price(value: float):
    st.session_state.price = value


quick = [300.0, 500.0, 750.0, 1000.0]
q_cols = st.columns(len(quick))
for col, amount in zip(q_cols, quick):
    col.button(f"₹{amount:,.0f}", key=f"q{int(amount)}", on_click=set_price, args=(amount,), use_container_width=True)

price = st.number_input(
    "Ticket price (₹)",
    min_value=0.0,
    step=50.0,
    key="price",
    help="Your discount and reservation total update automatically.",
)

discount = calculate_discount(cgpa)
savings = price * discount / 100
final_price = round(price - savings, 2)

# ---- Step 3: Summary ----
section("3", "Your reservation")

if discount:
    html(f'<div class="unlock">🎉 You unlocked <b>{discount}% OFF</b> and you save <b>₹ {savings:,.2f}</b></div>')
else:
    html('<div class="unlock none">✨ Your discount starts when your CGPA is above 8.5.</div>')

html(
    f"""
    <div class="summary">
        <div class="row"><span>Ticket price</span><b>₹ {price:,.2f}</b></div>
        <div class="row save"><span>Discount ({discount}%)</span><b>− ₹ {savings:,.2f}</b></div>
        <div class="total"><span>Reservation total</span><strong>₹ {final_price:,.2f}</strong></div>
    </div>
    """
)

st.markdown(
    '<div class="note">This app creates a ticket reservation; it does not process a payment.</div>',
    unsafe_allow_html=True,
)

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
    section("🎉", "Your festival pass")
    show_ticket_from_database(current_code)
