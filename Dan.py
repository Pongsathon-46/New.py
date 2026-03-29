import streamlit as st
import math
import pandas as pd
import os

# =========================
# SAFE IMPORT
# =========================
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_OK = True
except:
    MATPLOTLIB_OK = False

# =========================
# PAGE CONFIG (ต้องอยู่บนสุด)
# =========================
st.set_page_config(
    page_title="AASHTO 1993",
    layout="wide"
)

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

def calc_SN(W18, ZR, So, dPSI, MR):
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
st.sidebar.title("AASHTO 1993 PRO")

mode = st.sidebar.radio("Mode", ["Flexible","Rigid"])

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
# TABS
# =========================
tab1, tab2 = st.tabs(["Design","Sensitivity"])

# =========================
# DESIGN
# =========================
with tab1:

    col1,col2,col3,col4 = st.columns(4)

    SN_req = calc_SN(W18, ZR, So, dPSI, MR)

    data = [
        ["AC",0.44,1.1,20.3,True],
        ["Base",0.18,1.1,22.2,True],
        ["Subbase",0.13,1.1,10.2,True],
        ["Subgrade",0.10,1.1,10.2,True]
    ]

    df = pd.DataFrame(data, columns=["Layer","a","m","D(cm)","Use"])
    edited = st.data_editor(df, use_container_width=True)

    SN_prov = sum([
        r["a"]*r["m"]*r["D(cm)"]
        for _,r in edited.iterrows() if r["Use"]
    ])

    total_thickness = edited["D(cm)"].sum()

    col1.metric("SN Required", SN_req)
    col2.metric("SN Provided", round(SN_prov,3))
    col3.metric("Thickness", round(total_thickness,1))
    col4.metric("W18", f"{W18:,.0f}")

    # SECTION
    if MATPLOTLIB_OK:
        fig, ax = plt.subplots()
        y=0
        for i,r in edited.iterrows():
            ax.bar(0, r["D(cm)"], bottom=y)
            ax.text(0, y+r["D(cm)"]/2, f"{r['D(cm)']} cm", ha='center', color='white')
            ax.text(0.6, y+r["D(cm)"], f"D{i+1}")
            y+=r["D(cm)"]

        ax.set_xlim(-1,1)
        ax.set_xticks([])
        ax.invert_yaxis()

        st.pyplot(fig)
    else:
        st.warning("No matplotlib → fallback view")
        for i,r in edited.iterrows():
            st.progress(min(int(r["D(cm)"]*2),100),
                        text=f"{r['Layer']} {r['D(cm)']} cm")

# =========================
# SENSITIVITY
# =========================
with tab2:

    W_range = range(1000000,10000000,1000000)
    SN_list = [calc_SN(w, ZR, So, dPSI, MR) for w in W_range]

    if MATPLOTLIB_OK:
        fig2, ax2 = plt.subplots()
        ax2.plot(list(W_range), SN_list)
        ax2.set_xlabel("W18")
        ax2.set_ylabel("SN")
        st.pyplot(fig2)
    else:
        st.line_chart({"SN": SN_list})

# =========================
# PDF
# =========================
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    if st.button("Export PDF"):
        doc = SimpleDocTemplate("report.pdf")
        styles = getSampleStyleSheet()

        content = []
        content.append(Paragraph("AASHTO 1993 REPORT", styles['Title']))
        doc.build(content)

        with open("report.pdf","rb") as f:
            st.download_button("Download", f)

except:
    st.warning("No reportlab installed")
