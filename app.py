import streamlit as st
import json
import os
import pandas as pd

from settings import DATA_PATH  # ✅ FIX PATH
print("DEBUG PATH:", DATA_PATH)


# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="Market Allocation", layout="centered")

# -----------------------------
# STATE
# -----------------------------
if "capital" not in st.session_state:
    st.session_state.capital = 10000

# -----------------------------
# LOAD MODEL (UNICO PATH)
# -----------------------------
@st.cache_data(ttl=2)
def load_model():

    # ✅ FIX ROBUSTO (file o cartella)
    if DATA_PATH.endswith(".json"):
        path = DATA_PATH
    else:
        path = os.path.join(DATA_PATH, "dashboard_data.json")

    if not os.path.exists(path):
        st.error(f"Model file not found: {path}")
        return {}

    with open(path, "r") as f:
        return json.load(f)


report = load_model()



DEBUG = False

if DEBUG:
    st.write("DEBUG DATA_PATH:", DATA_PATH)

    if DATA_PATH.endswith(".json"):
        debug_path = DATA_PATH
    else:
        debug_path = os.path.join(DATA_PATH, "dashboard_data.json")

    st.write("DEBUG FILE PATH:", debug_path)

    if os.path.exists(debug_path):
        with open(debug_path) as f:
            debug_json = json.load(f)
        st.write("DEBUG EXPOSURE:", debug_json.get("exposure"))
    else:
        st.write("DEBUG: file NON esiste")




signals = report.get("signals", [])
playbook = report.get("playbook", "No signal available")
confidence = report.get("confidence", 0)
exposure = report.get("exposure", 0)
dispersion = report.get("dispersion", 0)

# -----------------------------
# COLORI REGIME
# -----------------------------
if "Defensive" in playbook:
    bg = "#ff4d4f20"
    color = "#ff4d4f"
    suggested_profile = "Conservative"
elif "Reduce" in playbook:
    bg = "#f5c54220"
    color = "#f5c542"
    suggested_profile = "Balanced"
else:
    bg = "#00c46a20"
    color = "#00c46a"
    suggested_profile = "Active"

# -----------------------------
# HEADER
# -----------------------------
st.title("Market Allocation")

st.markdown(
    f"""
    <div style="padding:12px;border-radius:10px;
    background-color:{bg};color:{color};
    font-weight:600;font-size:18px;">
    {playbook}
    </div>
    """,
    unsafe_allow_html=True
)

st.caption("Model-driven portfolio positioning")


# -----------------------------
# CAPITAL
# -----------------------------
st.subheader("Capital")

col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    if st.button("−"):
        st.session_state.capital = max(1000, st.session_state.capital - 1000)

with col3:
    if st.button("+"):
        st.session_state.capital += 1000

with col2:
    capital = st.number_input(
        "Capital (€)",
        min_value=1000,
        value=st.session_state.capital,
        step=1000,
        label_visibility="collapsed"
    )
    st.session_state.capital = capital

# -----------------------------
# SUMMARY
# -----------------------------
base_invest = capital * exposure

st.divider()


c1, c2, c3 = st.columns(3)

c1.metric("Exposure", f"{exposure*100:.1f}%")
c2.metric("Investable", f"{base_invest:,.0f} €")
c3.metric("Dispersion", f"{dispersion:.2f}")



# -----------------------------
# PROFILE
# -----------------------------
profiles = {
    "Conservative": 0.7,
    "Balanced": 1.0,
    "Active": 1.3,
}

profile_names = list(profiles.keys())

display_names = [
    f"{p} ⭐" if p == suggested_profile else p
    for p in profile_names
]

default_index = profile_names.index(suggested_profile)

selected_display = st.radio("Profile", display_names, index=default_index)

selected = selected_display.replace(" ⭐", "")
mult = profiles[selected]

# -----------------------------
# RESULT
# -----------------------------
invest = base_invest * mult
cash = capital - invest

st.subheader("Your allocation")

c1, c2 = st.columns(2)
c1.metric("Cash", f"{cash:,.0f} €")
c2.metric("Invested", f"{invest:,.0f} €")

# -----------------------------
# GRAPH
# -----------------------------
data = []

for s in signals:
    weight = s.get("weight", 0)

    if weight == 0:
        continue

    value = invest * weight

    data.append({
        "Asset": s.get("asset", "").upper(),
        "€": abs(value)
    })

if data:
    df = pd.DataFrame(data).sort_values("€", ascending=False)
    st.bar_chart(df.set_index("Asset"), height=200)

# -----------------------------
# MARKET CONTEXT
# -----------------------------
st.divider()

st.markdown(f"""
### Market context

- Confidence: **{confidence:.2f}**  
- Exposure: **{exposure:.2f}**
- Dispersion: **{dispersion:.2f}**

👉 Signals quality reflected in playbook  
""")

# -----------------------------
# BREAKDOWN
# -----------------------------
with st.expander("Asset breakdown", expanded=True):

    if not data:
        st.write("No active positions")
    else:
        max_val = max(d["€"] for d in data)

        for d in data:
            asset = d["Asset"]
            value = d["€"]

            signal = next(
                (s.get("signal", "LONG") for s in signals if s.get("asset", "").upper() == asset),
                "LONG"
            )

            colA, colB = st.columns([2, 1])

            if signal == "SHORT":
                badge = "<span style='color:#ff4d4f'>SHORT</span>"
                val = f"-{value:,.0f} €"
            else:
                badge = "<span style='color:#00c46a'>LONG</span>"
                val = f"+{value:,.0f} €"

            colA.markdown(f"**{asset}** — {badge}", unsafe_allow_html=True)
            colB.markdown(f"## {val}")

            st.progress(value / max_val)
            st.write("")