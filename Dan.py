import streamlit as st
import math
import pandas as pd

st.set_page_config(page_title="AASHTO 1993 PRO", layout="wide")

# -----------------------------
# Helper Functions
# -----------------------------
def aashto_sn_eq(SN, ZR, So, delta_PSI, Mr):
    return (
        ZR * So
        + 9.36 * math.log10(SN + 1)
        - 0.20
        + math.log10(delta_PSI / (4.2 - 1.5))
        + (1094 / ((SN + 1) ** 5.19))
        + 2.32 * math.log10(Mr)
        - 8.07
    )

def solve_sn(W18, ZR, So, delta_PSI, Mr):
    SN = 2.0
    for _ in range(100):
        f = aashto_sn_eq(SN, ZR, So, delta_PSI, Mr) - math.log10(W18)
        df = (aashto_sn_eq(SN+0.001, ZR, So, delta_PSI, Mr) - aashto_sn_eq(SN, ZR, So, delta_PSI, Mr)) / 0.001
        
        if df == 0:
            break
        
        SN = SN - f/df
        
        if abs(f) < 1e-6:
            break
    return SN

def round_construct(x_cm):
    return math.ceil(x_cm/5)*5

# -----------------------------
# UI
# -----------------------------
st.title("AASHTO 1993 Pavement Design (PRO)")

tab1, tab2 = st.tabs(["Flexible Pavement", "Rigid Pavement"])

# =============================
# FLEXIBLE
# =============================
with tab1:
    st.header("Flexible Pavement")

    col1, col2 = st.columns(2)

    with col1:
        W18 = st.number_input("ESAL", value=1e6)
        So = st.number_input("So", value=0.45)
        delta_PSI = st.number_input("ΔPSI", value=1.7)
        Mr = st.number_input("Mr (psi)", value=8000.0)

    with col2:
        a1 = st.number_input("a1", value=0.44)
        a2 = st.number_input("a2", value=0.14)
        a3 = st.number_input("a3", value=0.11)
        m2 = st.number_input("m2", value=1.0)
        m3 = st.number_input("m3", value=1.0)

    scenarios = {
        "90%": -1.282,
        "95%": -1.645,
        "99%": -2.327
    }

    if st.button("Run Design"):
        results = []
        chart_data = []

        for key, ZR in scenarios.items():
            SN_req = solve_sn(W18, ZR, So, delta_PSI, Mr)

            # thickness (cm)
            D1 = SN_req / a1 * 2.54
            D2 = (SN_req*0.6) / (a2*m2) * 2.54
            D3 = (SN_req*0.4) / (a3*m3) * 2.54

            # minimum thickness
            D1 = max(D1, 7.5)
            D2 = max(D2, 10)
            D3 = max(D3, 15)

            # rounding
            D1 = round_construct(D1)
            D2 = round_construct(D2)
            D3 = round_construct(D3)

            SN_ach = a1*(D1/2.54) + a2*m2*(D2/2.54) + a3*m3*(D3/2.54)

            results.append([key, SN_req, SN_ach, D1, D2, D3])
            chart_data.append([D1, D2, D3])

        df = pd.DataFrame(results, columns=["Reliability","SN_required","SN_achieved","D1(cm)","D2(cm)","D3(cm)"])

        st.subheader("Summary Table")
        st.dataframe(df)

        # Chart
        st.subheader("Layer Thickness Visualization (95%)")
        chart_df = pd.DataFrame({
            "Thickness (cm)": chart_data[1]
        }, index=["Asphalt (D1)", "Base (D2)", "Subbase (D3)"])

        st.bar_chart(chart_df)

        # Export
        df.to_excel("flexible_design.xlsx", index=False)
        with open("flexible_design.xlsx","rb") as f:
            st.download_button("Download Excel", f)

# =============================
# RIGID
# =============================
with tab2:
    st.header("Rigid Pavement (Jointed Concrete)")

    W18 = st.number_input("ESAL ", value=1e6, key="r1")
    ZR = st.number_input("Zr ", value=-1.645, key="r2")
    So = st.number_input("So ", value=0.35, key="r3")
    delta_PSI = st.number_input("ΔPSI ", value=1.5, key="r4")
    Sc = st.number_input("Sc (psi)", value=650.0)

    if st.button("Design Rigid Pavement"):
        D = (
            (math.log10(W18) + ZR*So) /
            (1 + (1e7/(Sc**2)))
        )

        D_cm = round_construct(D*2.54)

        st.subheader("Result")
        st.success(f"Thickness ≈ {D_cm} cm")

        # Chart
        chart_df = pd.DataFrame({
            "Thickness (cm)": [D_cm]
        }, index=["Concrete Slab"])

        st.bar_chart(chart_df)

        df = pd.DataFrame([[D_cm]], columns=["Thickness(cm)"])
        df.to_excel("rigid.xlsx", index=False)

        with open("rigid.xlsx","rb") as f:
            st.download_button("Download Excel", f)
