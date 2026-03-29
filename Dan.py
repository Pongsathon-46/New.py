import streamlit as st
import math
import pandas as pd

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="AASHTO 1993", layout="wide")

# =========================
# STYLE (UI เหมือนเว็บ)
# =========================
st.markdown("""
<style>
.metric-box {
    background-color: #161A23;
    padding: 15px;
    border-radius: 12px;
    text-align: center;
}
.layer-box {
    padding: 8px;
    border-radius: 6px;
    margin-bottom: 5px;
    color: white;
}
</style>
""", unsafe_allow_html=True)

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

# Flexible
def calc_SN(W18, ZR, So, dPSI, MR):
    SN = 3
    for _ in range(100):
        logW = ZR*So + 9.36*math.log10(SN+1)-0.20
        logW += (math.log10(dPSI/(4.2-1.5))) / (0.40+(1094/(SN+1)**5.19))
        logW += 2.32*math.log10(MR)-8.07
        SN += (math.log10(W18)-logW)
    return round(SN,3)

# Rigid (AASHTO Iteration)
def calc_rigid(W18, ZR, So, Sc, Cd, J, k):
    D = 8  # initial guess (inch)
    for _ in range(100):
        term1 = ZR*So
        term2 = 7.35*math.log10(D+1) - 0.06
        term3 = math.log10((Sc*Cd)/(215.63*J*(D**0.75)))
        term4 = 1.624*math.log10(D)
        logW = term1 + term2 + term3 + term4

        D = D + (math.log10(W18) - logW)

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
# FLEXIBLE
# =========================
if mode == "Flexible":

    Pi = st.sidebar.number_input("Pi", value=4.2)
    Pt = st.sidebar.number_input("Pt", value=2.5)
    CBR = st.sidebar.number_input("CBR", value=5.0)

    dPSI = Pi - Pt
    MR = MR_from_CBR(CBR)

    SN_req = calc_SN(W18, ZR, So, dPSI, MR)

    st.title("Flexible Pavement")

    # TABLE
    data = [
        ["AC",0.44,1.0,20.0,True],
        ["Base",0.14,1.1,20.0,True],
        ["Subbase",0.11,1.1,10.0,True],
    ]

    df = pd.DataFrame(data, columns=["Layer","a","m","D(cm)","Use"])
    edited = st.data_editor(df, use_container_width=True)

    SN_prov = sum([
        r["a"]*r["m"]*r["D(cm)"]
        for _,r in edited.iterrows() if r["Use"]
    ])

    total = edited["D(cm)"].sum()

    # METRICS
    c1,c2,c3,c4 = st.columns(4)

    c1.markdown(f"<div class='metric-box'>SN Req<br><b>{SN_req}</b></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'>SN Prov<br><b>{round(SN_prov,3)}</b></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-box'>Thickness<br><b>{round(total,1)} cm</b></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-box'>W18<br><b>{W18:,.0f}</b></div>", unsafe_allow_html=True)

    # LAYER DIAGRAM (UI สวย)
    st.subheader("Layer Section")

    colors = ["black","#3498DB","#8E5A2B"]

    y = 0
    for i,r in edited.iterrows():
        color = colors[i]
        st.markdown(
            f"<div class='layer-box' style='background:{color}'>"
            f"D{i+1} : {r['Layer']} = {r['D(cm)']} cm</div>",
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
    k = st.sidebar.number_input("k (pci)", value=100.0)

    D = calc_rigid(W18, ZR, So, Sc, Cd, J, k)

    c1,c2,c3 = st.columns(3)

    c1.markdown(f"<div class='metric-box'>Thickness<br><b>{D} inch</b></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-box'>Thickness<br><b>{round(D*2.54,2)} cm</b></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-box'>k-value<br><b>{k}</b></div>", unsafe_allow_html=True)

    st.info("Rigid design uses iterative AASHTO equation")
