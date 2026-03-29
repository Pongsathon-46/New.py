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
    table = {
        50:0.0,60:-0.253,70:-0.524,
        75:-0.674,80:-0.841,85:-1.036,
        90:-1.282,95:-1.645,99:-2.327
    }
    return table[R]

def MR_from_CBR(CBR):
    return 2555*(CBR**0.64)

# Flexible SN
def calc_SN_required(W18, ZR, So, dPSI, MR):
    SN = 3
    for _ in range(100):
        logW = ZR*So + 9.36*math.log10(SN+1)-0.20
        logW += (math.log10(dPSI/(4.2-1.5))) / (0.40+(1094/(SN+1)**5.19))
        logW += 2.32*math.log10(MR)-8.07
        SN += (math.log10(W18)-logW)
    return round(SN,3)

# Rigid Iterative
def calc_rigid(W18, ZR, So, Sc, Cd, J, k):
    D = 8  # initial guess (inch)
    for _ in range(100):
        term1 = ZR*So
        term2 = 7.35*math.log10(D+1) - 0.06
        term3 = math.log10((Sc*Cd)/(215.63*J*(D**0.75)))
        term4 = 1.624*math.log10(D)
        logW = term1 + term2 + term3 + term4
        D += (math.log10(W18) - logW)
    return round(D,2)

# =========================
# SIDEBAR
# =========================
st.sidebar.title("AASHTO 1993")

mode = st.sidebar.radio("Mode", ["Flexible","Rigid"])

W18 = st.sidebar.number_input("W18", value=5000000.0)
R = st.sidebar.selectbox("Reliability", [50,60,70,75,80,85,90,95,99], index=8)
So = st.sidebar.number_input("So", value=0.45)

ZR = reliability_to_zr(R)

# =========================
# FLEXIBLE MODE
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

    # SN calc
    SN_list = []
    cum_SN = []
    total = 0

    for _, r in edited.iterrows():
        sn = r["a"]*r["m"]*r["D(cm)"] if r["Use"] else 0
        total += sn
        SN_list.append(round(sn,3))
        cum_SN.append(round(total,3))

    SN_prov = round(total,3)

    c1,c2,c3 = st.columns(3)
    c1.metric("SN Required", SN_req)
    c2.metric("SN Provided", SN_prov)
    c3.metric("Status", "PASS" if SN_prov>=SN_req else "FAIL")

    # =========================
    # ANIMATION SN BUILD-UP
    # =========================
    st.subheader("🎬 SN Build-up Animation")

    if st.button("▶ Start Animation"):

        placeholder = st.empty()

        total_anim = 0

        for i, r in edited.iterrows():

            sn = SN_list[i]
            total_anim += sn

            if PLOTLY_OK:
                fig = go.Figure()

                fig.add_trace(go.Bar(
                    name=r["Layer"],
                    x=["SN"],
                    y=[total_anim],
                    text=f"{round(total_anim,3)}",
                    textposition="inside"
                ))

                fig.update_layout(
                    title=f"Layer {i+1}: {r['Layer']}",
                    yaxis_title="SN",
                    height=400
                )

                placeholder.plotly_chart(fig, use_container_width=True)

            else:
                placeholder.write(f"Layer {i+1}: {r['Layer']}")
                placeholder.progress(min(int(total_anim*10),100))

            time.sleep(0.8)

    # =========================
    # FINAL STACK GRAPH
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
# RIGID MODE
# =========================
else:

    st.title("Rigid Pavement")

    Sc = st.sidebar.number_input("Sc (psi)", value=650.0)
    Cd = st.sidebar.number_input("Cd", value=1.0)
    J = st.sidebar.number_input("J", value=3.2)
    k = st.sidebar.number_input("k (pci)", value=100.0)

    D = calc_rigid(W18, ZR, So, Sc, Cd, J, k)

    c1,c2,c3 = st.columns(3)
    c1.metric("Thickness (inch)", D)
    c2.metric("Thickness (cm)", round(D*2.54,2))
    c3.metric("k-value", k)

    st.info("Rigid design uses AASHTO 1993 iterative equation")
