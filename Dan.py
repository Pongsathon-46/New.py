import streamlit as st
import math
import pandas as pd
import time

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
st.set_page_config(page_title="AASHTO 1993 PRO", layout="wide")

# =========================
# FUNCTIONS
# =========================
def reliability_to_zr(R):
    return {
        50:0.0,60:-0.253,70:-0.524,
        75:-0.674,80:-0.841,85:-1.036,
        90:-1.282,95:-1.645,99:-2.327
    }[R]

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

def calc_rigid(W18, ZR, So, Sc, Cd, J, k):
    D = 8
    for _ in range(100):
        logW = ZR*So
        logW += 7.35*math.log10(D+1) - 0.06
        logW += math.log10((Sc*Cd)/(215.63*J*(D**0.75)))
        logW += 1.624*math.log10(D)
        D += (math.log10(W18) - logW)
    return round(D,2)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("AASHTO 1993")

mode = st.sidebar.radio("Mode", ["Flexible","Rigid"])

W18 = st.sidebar.number_input("W18", value=5000000.0)
R = st.sidebar.selectbox("Reliability",[50,60,70,75,80,85,90,95,99], index=8)
So = st.sidebar.number_input("So", value=0.45)

ZR = reliability_to_zr(R)

# =========================
# FLEXIBLE
# =========================
if mode == "Flexible":

    Pi = st.sidebar.number_input("Pi", value=4.2)
    Pt = st.sidebar.number_input("Pt", value=2.5)
    CBR = st.sidebar.number_input("CBR", value=5.0)

    dPSI = Pi - Pt
    MR = MR_from_CBR(CBR)

    SN_req = calc_SN_required(W18, ZR, So, dPSI, MR)

    st.title("Flexible Pavement")

    # TABLE
    data = [
        ["AC",0.44,1.0,20.0,True],
        ["Base",0.14,1.1,20.0,True],
        ["Subbase",0.11,1.1,10.0,True],
        ["Subgrade",0.10,1.0,10.0,True],
    ]

    df = pd.DataFrame(data, columns=["Layer","a","m","D(cm)","Use"])
    edited = st.data_editor(df, use_container_width=True)

    # SN CALC
    SN_list = []
    cum_SN = []
    total = 0

    for _, r in edited.iterrows():
        sn = r["a"]*r["m"]*r["D(cm)"] if r["Use"] else 0
        total += sn
        SN_list.append(round(sn,3))
        cum_SN.append(round(total,3))

    SN_prov = round(total,3)

    # METRICS
    c1,c2,c3 = st.columns(3)
    c1.metric("SN Required", SN_req)
    c2.metric("SN Provided", SN_prov)
    c3.metric("Status", "PASS" if SN_prov>=SN_req else "FAIL")

    # =========================
    # ANIMATION
    # =========================
    st.subheader("🎬 SN Build-up Animation")

    if st.button("▶ Start Animation"):

        placeholder = st.empty()
        total_anim = 0

        for i, r in edited.iterrows():

            total_anim += SN_list[i]

            if PLOTLY_OK:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=["SN"],
                    y=[total_anim],
                    text=f"{round(total_anim,3)}",
                    textposition="inside"
                ))
                fig.update_layout(
                    title=f"Layer {i+1}: {r['Layer']}",
                    height=400
                )
                placeholder.plotly_chart(fig, use_container_width=True)
            else:
                placeholder.write(f"{r['Layer']} → SN = {total_anim}")

            time.sleep(0.8)

    # =========================
    # STACK GRAPH
    # =========================
    st.subheader("SN Stack")

    if PLOTLY_OK:
        fig2 = go.Figure()
        for i, r in edited.iterrows():
            fig2.add_trace(go.Bar(
                name=r["Layer"],
                x=["SN"],
                y=[SN_list[i]]
            ))
        fig2.update_layout(barmode='stack')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.bar_chart(pd.DataFrame({"SN":SN_list}))

    # =========================
    # SECTION VIEW (🔥 เพิ่มล่าสุด)
    # =========================
    st.subheader("🧱 Pavement Section (Top → Bottom)")

    colors = ["#000000", "#3498DB", "#8E5A2B", "#F4D03F"]
    text_colors = ["white", "black", "white", "black"]

    if PLOTLY_OK:
        fig3 = go.Figure()
        y_base = 0

        for i, r in edited.iterrows():
            t = r["D(cm)"]

            fig3.add_trace(go.Bar(
                x=[0],
                y=[t],
                base=y_base,
                marker_color=colors[i],
                width=0.6,
                text=f"D{i+1}<br>{r['Layer']}<br>{t} cm",
                textposition="inside",
                textfont=dict(color=text_colors[i]),
                hovertemplate=(
                    f"<b>{r['Layer']}</b><br>"
                    f"Thickness: {t} cm<br>"
                    f"SN: {SN_list[i]}<br>"
                    f"Cumulative SN: {cum_SN[i]}"
                    "<extra></extra>"
                )
            ))

            y_base += t

        fig3.update_layout(
            height=600,
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(title="Depth (cm)", autorange="reversed"),
            plot_bgcolor="#111111"
        )

        st.plotly_chart(fig3, use_container_width=True)

    else:
        for i, r in edited.iterrows():
            st.markdown(
                f"<div style='background:{colors[i]};color:{text_colors[i]};padding:15px;margin:5px'>{r['Layer']} {r['D(cm)']} cm</div>",
                unsafe_allow_html=True
            )

# =========================
# RIGID
# =========================
else:

    st.title("Rigid Pavement")

    Sc = st.sidebar.number_input("Sc (psi)", value=650.0)
    Cd = st.sidebar.number_input("Cd", value=1.0)
    J = st.sidebar.number_input("J", value=3.2)
    k = st.sidebar.number_input("k", value=100.0)

    D = calc_rigid(W18, ZR, So, Sc, Cd, J, k)

    c1,c2 = st.columns(2)
    c1.metric("Thickness (inch)", D)
    c2.metric("Thickness (cm)", round(D*2.54,2))
