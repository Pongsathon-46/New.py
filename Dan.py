import streamlit as st
import math
import pandas as pd
import plotly.graph_objects as go

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
    if r["Use"]:
        sn = r["a"] * r["m"] * r["D(cm)"]
    else:
        sn = 0

    total += sn
    SN_list.append(sn)
    cum_SN.append(total)

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
# SN TABLE (SHOW CONTRIBUTION)
# =========================
st.subheader("SN Contribution Table")

result_df = edited.copy()
result_df["SN Layer"] = SN_list
result_df["SN Cumulative"] = cum_SN

st.dataframe(result_df)

# =========================
# INTERACTIVE LAYER GRAPH
# =========================
st.subheader("Layer Section (Interactive)")

colors = ["#000000", "#3498DB", "#8E5A2B", "#F4D03F"]
text_colors = ["white", "black", "white", "black"]

fig = go.Figure()
y_base = 0

for i, r in edited.iterrows():

    fig.add_trace(go.Bar(
        x=[1],
        y=[r["D(cm)"]],
        base=y_base,
        marker_color=colors[i],
        text=f"D{i+1}<br>{r['Layer']}<br>{r['D(cm)']} cm",
        textposition="inside",
        textfont=dict(color=text_colors[i], size=14),
        hovertemplate=(
            f"<b>{r['Layer']}</b><br>"
            f"Thickness: {r['D(cm)']} cm<br>"
            f"SN: {round(SN_list[i],3)}<br>"
            f"Cumulative SN: {round(cum_SN[i],3)}"
            "<extra></extra>"
        ),
        width=0.5
    ))

    y_base += r["D(cm)"]

fig.update_layout(
    height=500,
    showlegend=False,
    yaxis=dict(title="Depth (cm)", autorange="reversed"),
    xaxis=dict(visible=False)
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# SN STACK GRAPH
# =========================
st.subheader("SN Stack Contribution")

fig2 = go.Figure()

for i, r in edited.iterrows():
    fig2.add_trace(go.Bar(
        name=r["Layer"],
        x=["SN"],
        y=[SN_list[i]],
        marker_color=colors[i],
        text=round(SN_list[i],3),
        textposition="inside"
    ))

fig2.update_layout(
    barmode='stack',
    height=400
)

st.plotly_chart(fig2, use_container_width=True)

# =========================
# SENSITIVITY
# =========================
st.subheader("Sensitivity (W18 vs SN)")

W_range = range(1000000,10000000,1000000)
SN_curve = [calc_SN_required(w, ZR, So, dPSI, MR) for w in W_range]

fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=list(W_range), y=SN_curve, mode='lines+markers'))

st.plotly_chart(fig3, use_container_width=True)
