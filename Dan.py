import streamlit as st
import math

st.set_page_config(page_title="AASHTO 1993 Pavement Design", layout="wide")

st.title("AASHTO 1993 Pavement Design")

# เลือกประเภท
pavement_type = st.sidebar.selectbox(
    "เลือกประเภทผิวทาง",
    ["Flexible Pavement", "Rigid Pavement"]
)

# -----------------------------
# Flexible Pavement
# -----------------------------
if pavement_type == "Flexible Pavement":
    st.header("Flexible Pavement Design (SN)")

    W18 = st.number_input("ESAL (W18)", value=1e6)
    ZR = st.number_input("Zr (Reliability Factor)", value=-1.645)
    So = st.number_input("Standard Deviation (So)", value=0.45)
    delta_PSI = st.number_input("ΔPSI", value=1.7)
    Mr = st.number_input("Subgrade Resilient Modulus (psi)", value=8000.0)

    if st.button("คำนวณ SN"):

        # สมการ AASHTO 1993 (ประมาณ)
        SN = (math.log10(W18) - ZR * So + 0.20 + math.log10(delta_PSI)) / (
            0.40 + (1094 / ((SN if 'SN' in locals() else 5.0) + 1) ** 5.19)
        )

        st.success(f"Structural Number (SN) ≈ {round(SN, 3)}")

# -----------------------------
# Rigid Pavement
# -----------------------------
elif pavement_type == "Rigid Pavement":
    st.header("Rigid Pavement Design (Thickness)")

    W18 = st.number_input("ESAL (W18)", value=1e6)
    ZR = st.number_input("Zr", value=-1.645)
    So = st.number_input("So", value=0.35)
    delta_PSI = st.number_input("ΔPSI", value=1.5)
    Sc = st.number_input("Modulus of Rupture Sc (psi)", value=650.0)
    Ec = st.number_input("Elastic Modulus Ec (psi)", value=4e6)
    k = st.number_input("k-value (pci)", value=100.0)

    if st.button("คำนวณ Thickness"):

        # สูตรประมาณ (simplified)
        D = (
            (math.log10(W18) + ZR * So) /
            (0.75 + (1.624e7 / (Sc ** 2)))
        )

        st.success(f"Thickness D ≈ {round(D, 2)} inches")

# Footer
st.markdown("---")
st.caption("Based on AASHTO 1993 Pavement Design Guide")
