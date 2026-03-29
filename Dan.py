import streamlit as st
import math

st.set_page_config(page_title="AASHTO 1993 Pavement Design", layout="wide")

# =========================
# 🔧 FUNCTIONS
# =========================

def reliability_to_zr(R):
    table = {
        50: 0.0, 60: -0.253, 70: -0.524,
        75: -0.674, 80: -0.841, 85: -1.036,
        90: -1.282, 95: -1.645, 99: -2.327
    }
    return table.get(R, -1.282)

def MR_from_CBR(CBR):
    return 2555 * (CBR ** 0.64)

# Flexible Pavement Equation (AASHTO 1993)
def calc_SN_required(W18, ZR, So, dPSI, MR):
    SN = 3.0
    for _ in range(100):
        term1 = ZR * So
        term2 = 9.36 * math.log10(SN + 1) - 0.20
        term3 = (math.log10(dPSI / (4.2 - 1.5))) / (0.40 + (1094 / (SN + 1) ** 5.19))
        term4 = 2.32 * math.log10(MR) - 8.07

        logW18 = term1 + term2 + term3 + term4
        W18_calc = 10 ** logW18

        SN = SN + (math.log10(W18) - logW18)

    return round(SN, 3)

def calc_SN_provided(layers):
    SN = 0
    for layer in layers:
        if layer["use"]:
            SN += layer["a"] * layer["D"] * layer["m"]
    return round(SN, 3)

# =========================
# 🧭 SIDEBAR INPUT
# =========================

st.sidebar.title("AASHTO 1993")

mode = st.sidebar.radio("เลือกประเภท", ["Flexible", "Rigid"])

W18 = st.sidebar.number_input("W18 (ESAL)", value=5_000_000.0, format="%.0f")
R = st.sidebar.selectbox("Reliability (%)", [50,60,70,75,80,85,90,95,99], index=8)
So = st.sidebar.number_input("So", value=0.45)

Pi = st.sidebar.number_input("Initial Serviceability (Pi)", value=4.2)
Pt = st.sidebar.number_input("Terminal Serviceability (Pt)", value=2.5)

CBR = st.sidebar.number_input("CBR (%)", value=5.0)

ZR = reliability_to_zr(R)
dPSI = Pi - Pt
MR = MR_from_CBR(CBR)

st.sidebar.write(f"ZR = {ZR}")
st.sidebar.write(f"ΔPSI = {round(dPSI,2)}")
st.sidebar.write(f"MR = {round(MR,0)} psi")

# =========================
# 🟢 FLEXIBLE
# =========================

if mode == "Flexible":

    st.title("Flexible Pavement (AASHTO 1993)")

    SN_required = calc_SN_required(W18, ZR, So, dPSI, MR)

    layers = [
        {"name": "AC", "a": 0.44, "m": 1.0, "D": 20.0, "use": True},
        {"name": "Base", "a": 0.14, "m": 1.1, "D": 20.0, "use": True},
        {"name": "Subbase", "a": 0.11, "m": 1.1, "D": 10.0, "use": True},
    ]

    SN_provided = calc_SN_provided(layers)

    col1, col2, col3 = st.columns(3)

    col1.metric("SN Required", SN_required)
    col2.metric("SN Provided", SN_provided)

    if SN_provided >= SN_required:
        col3.success("ผ่าน")
    else:
        col3.error("ไม่ผ่าน")

    st.subheader("Layer Details")

    total_thickness = 0

    for i, layer in enumerate(layers):
        cols = st.columns(5)

        layer["D"] = cols[0].number_input(f"{layer['name']} Thickness (cm)", value=layer["D"], key=i)
        layer["a"] = cols[1].number_input("a", value=layer["a"], key=f"a{i}")
        layer["m"] = cols[2].number_input("m", value=layer["m"], key=f"m{i}")
        layer["use"] = cols[3].checkbox("ใช้", value=True, key=f"use{i}")

        SN_layer = layer["a"] * layer["D"] * layer["m"] if layer["use"] else 0
        cols[4].write(f"SN = {round(SN_layer,3)}")

        total_thickness += layer["D"]

    st.write(f"Total Thickness = {round(total_thickness,1)} cm")

# =========================
# 🔵 RIGID
# =========================

else:

    st.title("Rigid Pavement (AASHTO 1993)")

    Ec = st.number_input("Ec (psi)", value=4_000_000.0)
    k = st.number_input("k (pci)", value=100.0)
    J = st.number_input("J", value=3.2)
    Cd = st.number_input("Cd", value=1.0)
    Sc = st.number_input("Sc (Modulus of Rupture)", value=650.0)

    # simple estimation
    D = (math.log10(W18) + ZR*So) * 2

    st.metric("Slab Thickness (inch)", round(D,2))
    st.metric("Slab Thickness (cm)", round(D*2.54,2))

    st.info("Rigid equation เป็น iterative ในมาตรฐานจริง")
