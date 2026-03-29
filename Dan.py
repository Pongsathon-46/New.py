import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="AASHTO 1993 PRO", layout="wide")

st.title("AASHTO 1993 Pavement Design (Professional)")

# -----------------------------
# Sidebar Inputs
# -----------------------------
st.sidebar.header("Input Parameters")

W18 = st.sidebar.number_input("ESAL (W18)", value=1e6, format="%.0f")
ZR = st.sidebar.number_input("Zr", value=-1.645)
So = st.sidebar.number_input("So", value=0.45)
delta_PSI = st.sidebar.number_input("ΔPSI", value=1.7)
Mr = st.sidebar.number_input("Mr (psi)", value=8000.0)

st.sidebar.markdown("---")
st.sidebar.header("Layer Coefficients")

a1 = st.sidebar.number_input("a1 (Asphalt)", value=0.44)
a2 = st.sidebar.number_input("a2 (Base)", value=0.14)
a3 = st.sidebar.number_input("a3 (Subbase)", value=0.11)

m2 = st.sidebar.number_input("m2 (Drainage Base)", value=1.0)
m3 = st.sidebar.number_input("m3 (Drainage Subbase)", value=1.0)

# -----------------------------
# AASHTO Equation Function
# -----------------------------
def aashto_sn(SN):
    return (
        ZR * So
        + 9.36 * math.log10(SN + 1)
        - 0.20
        + math.log10(delta_PSI / (4.2 - 1.5))
        + (1094 / ((SN + 1) ** 5.19))
        + 2.32 * math.log10(Mr)
        - 8.07
    )

# -----------------------------
# Iterative Solve SN
# -----------------------------
def solve_sn():
    SN = 1.0
    for _ in range(100):
        f = aashto_sn(SN) - math.log10(W18)
        df = (aashto_sn(SN + 0.001) - aashto_sn(SN)) / 0.001
        SN = SN - f / df
        if abs(f) < 1e-5:
            break
    return SN

if st.button("Calculate SN"):
    SN = solve_sn()
    st.success(f"SN = {round(SN,3)}")

    st.subheader("Layer Thickness Design")

    # Assume practical layer thickness
    D1 = SN / a1
    SN2 = SN - a1 * D1

    D2 = max(SN2 / (a2 * m2), 0)
    SN3 = SN2 - a2 * m2 * D2

    D3 = max(SN3 / (a3 * m3), 0)

    df = pd.DataFrame({
        "Layer": ["Asphalt", "Base", "Subbase"],
        "Thickness (in)": [D1, D2, D3]
    })

    st.dataframe(df)

    # -----------------------------
    # Graph
    # -----------------------------
    st.subheader("SN vs Thickness")

    SN_values = []
    thickness = []

    for d in range(1, 20):
        sn_temp = a1*d
        SN_values.append(sn_temp)
        thickness.append(d)

    import matplotlib.pyplot as plt

    plt.figure()
    plt.plot(thickness, SN_values)
    plt.xlabel("Thickness (in)")
    plt.ylabel("SN")
    plt.title("Asphalt Contribution to SN")

    st.pyplot(plt)

    # -----------------------------
    # Export Excel
    # -----------------------------
    excel_file = "pavement_design.xlsx"
    df.to_excel(excel_file, index=False)

    with open(excel_file, "rb") as f:
        st.download_button("Download Excel", f, file_name=excel_file)
