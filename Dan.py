import streamlit as st
import math
import pandas as pd
import random

# -----------------------------
# OPTIONAL PDF (ไม่พังถ้าไม่มี)
# -----------------------------
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except:
    REPORTLAB_AVAILABLE = False

st.set_page_config(page_title="AASHTO 1993 Pavement Design", layout="wide")

# -----------------------------
# SOLVER
# -----------------------------
def aashto_sn_eq(SN, ZR, So, delta_PSI, Mr):
    SN = max(SN, 0.01)
    return (
        ZR * So
        + 9.36 * math.log10(SN + 1)
        - 0.20
        + math.log10(delta_PSI / (4.2 - 1.5))
        + (1094 / ((SN + 1) ** 5.19))
        + 2.32 * math.log10(Mr)
        - 8.07
    )

def f_SN(SN, W18, ZR, So, delta_PSI, Mr):
    return aashto_sn_eq(SN, ZR, So, delta_PSI, Mr) - math.log10(W18)

def solve_sn_debug(W18, ZR, So, delta_PSI, Mr):
    history = []

    # auto-fix
    W18 = max(W18, 1e5)
    Mr = max(Mr, 1000)
    delta_PSI = max(delta_PSI, 1.5)

    low, high = 0.1, 10

    for _ in range(20):
        if f_SN(low, W18, ZR, So, delta_PSI, Mr) * f_SN(high, W18, ZR, So, delta_PSI, Mr) <= 0:
            break
        high *= 2

    for i in range(50):
        mid = (low + high) / 2
        history.append({"iter": i, "SN": mid})
        if f_SN(low, W18, ZR, So, delta_PSI, Mr) * f_SN(mid, W18, ZR, So, delta_PSI, Mr) < 0:
            high = mid
        else:
            low = mid

    SN = (low + high) / 2

    for i in range(20):
        f = f_SN(SN, W18, ZR, So, delta_PSI, Mr)
        df = (f_SN(SN+0.001, W18, ZR, So, delta_PSI, Mr) - f)/0.001

        history.append({"iter": i+50, "SN": SN})

        if abs(df) < 1e-8:
            break

        SN_new = SN - f/df

        if SN_new <= 0:
            SN_new = SN/2

        if abs(SN_new - SN) < 1e-6:
            break

        SN = SN_new

    return SN, history

def round_construct(x):
    return math.ceil(x/5)*5

# -----------------------------
# PDF FUNCTION
# -----------------------------
def generate_pdf(SN_req, SN_ach, D1, D2, D3):
    if not REPORTLAB_AVAILABLE:
        return None

    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("AASHTO 1993 Pavement Design Report", styles['Title']))
    content.append(Paragraph(f"SN Required: {SN_req:.2f}", styles['Normal']))
    content.append(Paragraph(f"SN Achieved: {SN_ach:.2f}", styles['Normal']))
    content.append(Paragraph(f"Asphalt: {D1} cm", styles['Normal']))
    content.append(Paragraph(f"Base: {D2} cm", styles['Normal']))
    content.append(Paragraph(f"Subbase: {D3} cm", styles['Normal']))

    doc.build(content)
    return "report.pdf"

# -----------------------------
# UI
# -----------------------------
st.title("🚧 AASHTO 1993 Pavement Design")

tab1, tab2 = st.tabs(["Flexible", "Rigid"])

# ================= FLEXIBLE =================
with tab1:
    st.header("Flexible Pavement")

    col1, col2 = st.columns(2)

    with col1:
        AADT = st.number_input("AADT", value=10000)
        growth = st.number_input("Growth (%)", value=3.0)/100
        Mr = st.number_input("Mr", value=8000.0)
        delta_PSI = st.number_input("ΔPSI", value=1.7)
        So = st.number_input("So", value=0.45)

    with col2:
        a1 = st.number_input("a1", value=0.44)
        a2 = st.number_input("a2", value=0.14)
        a3 = st.number_input("a3", value=0.11)

    # Traffic
    W18 = sum([AADT*((1+growth)**y)*365*0.8*0.3 for y in range(20)])
    st.info(f"W18 ≈ {round(W18,0):,}")

    drainage = st.selectbox("Drainage", ["Poor","Fair","Good","Excellent"])
    m_dict = {"Poor":0.6,"Fair":0.8,"Good":1.0,"Excellent":1.2}
    m2 = m3 = m_dict[drainage]

    if st.button("Run Design"):

        ZR = -1.645
        SN_req, history = solve_sn_debug(W18, ZR, So, delta_PSI, Mr)

        if SN_req is None:
            st.error("❌ Solver failed")
            st.stop()

        D1 = round_construct(max(SN_req/a1*2.54, 7.5))
        D2 = round_construct(max(SN_req*0.6/(a2*m2)*2.54, 10))
        D3 = round_construct(max(SN_req*0.4/(a3*m3)*2.54, 15))

        SN_ach = a1*(D1/2.54)+a2*m2*(D2/2.54)+a3*m3*(D3/2.54)

        st.success(f"SN Required = {SN_req:.2f} | SN Achieved = {SN_ach:.2f}")

        st.bar_chart(pd.DataFrame({"Thickness":[D1,D2,D3]},
                                 index=["Asphalt","Base","Subbase"]))

        st.subheader("Convergence")
        st.line_chart(pd.DataFrame([h["SN"] for h in history]))

        with st.expander("Debug"):
            st.dataframe(pd.DataFrame(history))

        # Excel
        df = pd.DataFrame([[SN_req,SN_ach,D1,D2,D3]],
                          columns=["SN_req","SN_ach","D1","D2","D3"])
        df.to_excel("design.xlsx", index=False)

        with open("design.xlsx","rb") as f:
            st.download_button("Download Excel", f)

        # PDF (optional)
        if REPORTLAB_AVAILABLE:
            if st.button("Generate PDF"):
                file = generate_pdf(SN_req, SN_ach, D1, D2, D3)
                with open(file,"rb") as f:
                    st.download_button("Download PDF", f)
        else:
            st.warning("⚠️ PDF ไม่พร้อมใช้งาน (ยังไม่ได้ติดตั้ง reportlab)")

# ================= RIGID =================
with tab2:
    st.header("Rigid Pavement")

    W18 = st.number_input("ESAL", value=1e6, key="r1")
    ZR = st.number_input("Zr", value=-1.645)
    So = st.number_input("So", value=0.35)
    Sc = st.number_input("Sc", value=650.0)

    if st.button("Design Rigid"):
        D = (math.log10(W18)+ZR*So)/(1+(1e7/(Sc**2)))
        D = round_construct(D*2.54)

        st.success(f"Thickness = {D} cm")

        st.bar_chart(pd.DataFrame({"Thickness":[D]},index=["Concrete"]))
