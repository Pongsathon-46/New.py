import streamlit as st
import math
import pandas as pd

# =========================
# SAFE IMPORT
# =========================
try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except:
    PLOTLY_OK = False

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="AASHTO 1993", layout="wide")

# =========================
# FUNCTIONS
# =========================
def reliability_to_zr(R):
    table = {
        50:0.0,60:-0.253,70:-0.524,
        75:-0.674,80:-0.841,85:-1.036,
        90:-1.282,95:-1.645,99:-2.327
    }
    return table[R]

def MR_from_CBR(CBR):
    return 2555*(CBR**0.64)

def calc_SN_required(W18, ZR, So, dPSI, MR):
    SN = 3
    for _ in range(100):
        logW = ZR*So + 9.36*math.log10(SN+1)-0.20
        logW += (math.log10(dPSI/(4.2-1.5))) / (0.40+(1094/(SN+1)**5.19))
        logW += 2.32*math.log10(MR)-8.07
        SN += (math.log10(W18)-logW)
    return round(SN,3)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("AASHTO 1993")

W18 = st.sidebar.number_input("W18", value=5000000.0)
R = st.sidebar.selectbox("Reliability", [50,60,70,75,80,85,90,95,99], index=8)
So = st.sidebar.number_input("So", value=0.45)
Pi = st.sidebar.number_input("Pi", value=4.2)
Pt = st.sidebar.number_input("Pt", value=2.5)
CBR = st.sidebar.number_input("CBR", value=5.0)

ZR = reliability_to_zr(R)
dPSI = Pi - Pt
MR = MR_from_CBR(CBR)

# =========================
# CALC
# =========================
SN_req = calc_SN_required(W18, ZR, So, dPSI, MR)

st.title("Flexible Pavement Design")

# =========================
# TABLE INPUT
# =========================
data = [
    ["AC",0.44,1.0,20.0,True],
    ["Base",0.14,1.1,20.0,True],
    ["Subbase",0.11,1.1,10.0,True],
    ["Subgrade",0.10,1.0,10.0,True],
]

df = pd.DataFrame(data, columns=["Layer","a","m","D(cm)","Use"])
edited = st.data_editor(df, use_container_width=True)

# =========================
# SN CALCULATION
# =========================
SN_list = []
cum_SN = []
total = 0

for _, r in edited.iterrows():
    sn = r["a"] * r["m"] * r["D(cm)"] if r["Use"] else 0
    total += sn
    SN_list.append(round(sn,3))
    cum_SN.append(round(total,3))

SN_prov = round(total,3)

# =========================
# METRICS
# =========================
c1,c2,c3 = st.columns(3)

c1.metric("SN Required", SN_req)
c2.metric("SN Provided", SN_prov)

if SN_prov >= SN_req:
    c3.success("PASS")
else:
    c3.error("FAIL")

# =========================
# TABLE
# =========================
st.subheader("SN Contribution")

result_df = edited.copy()
result_df["SN Layer"] = SN_list
result_df["SN Cumulative"] = cum_SN

st.dataframe(result_df)

# =========================
# GRAPH (SAFE)
# =========================
st.subheader("SN Stack Graph")

if PLOTLY_OK:
    fig = go.Figure()

    for i, r in edited.iterrows():
        fig.add_trace(go.Bar(
            name=r["Layer"],
            x=["SN"],
            y=[SN_list[i]],
            text=SN_list[i],
            textposition="inside"
        ))

    fig.update_layout(barmode='stack')
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No plotly → fallback chart")
    st.bar_chart(pd.DataFrame({
        "Layer": edited["Layer"],
        "SN": SN_list
    }).set_index("Layer"))

# =========================
# SENSITIVITY
# =========================
st.subheader("Sensitivity")

W_range = range(1000000,10000000,1000000)
SN_curve = [calc_SN_required(w, ZR, So, dPSI, MR) for w in W_range]

if PLOTLY_OK:
    fig2 = go.Figure()
    fig2.add_scatter(x=list(W_range), y=SN_curve, mode='lines+markers')
    st.plotly_chart(fig2, use_container_width=True)
else:
    st.line_chart(SN_curve)
