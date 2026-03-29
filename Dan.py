import streamlit as st
import math
import numpy as np

# ===== Safe import =====
try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except:
    HAS_MPL = False

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Image
    from reportlab.lib.styles import getSampleStyleSheet
    HAS_PDF = True
except:
    HAS_PDF = False


# =========================
# FUNCTIONS
# =========================

def reliability_to_zr(R):
    table = {50:0,60:-0.253,70:-0.524,75:-0.674,80:-0.841,
             85:-1.036,90:-1.282,95:-1.645,98:-2.054,99:-2.327}
    return table.get(R, -1.645)


def cbr_to_mr(cbr):
    return 2555 * (cbr ** 0.64)


def drainage(percent):
    if percent < 1: return 1.4
    elif percent < 5: return 1.2
    elif percent < 25: return 1.0
    elif percent < 50: return 0.8
    else: return 0.6


def solve_SN(W18, ZR, So, dPSI, MR):
    def f(SN):
        return (ZR*So + 9.36*math.log10(SN+1)-0.20 +
                (math.log10(dPSI/(4.2-1.5))) /
                (0.40+(1094/(SN+1)**5.19)) +
                2.32*math.log10(MR)-8.07 -
                math.log10(W18))

    SN = 0.5
    while SN < 10:
        if abs(f(SN)) < 0.01:
            return SN
        SN += 0.01
    return None


def optimize(SN, a1,a2,a3,a4,m2,m3,m4,costs):
    best = None
    for D1 in range(5,30):
        for D2 in range(5,30):
            for D3 in range(5,30):
                for D4 in range(5,30):
                    SNc = a1*D1 + a2*m2*D2 + a3*m3*D3 + a4*m4*D4
                    if SNc >= SN:
                        cost = D1*costs[0]+D2*costs[1]+D3*costs[2]+D4*costs[3]
                        if best is None or cost < best[0]:
                            best = (cost,D1,D2,D3,D4)
    return best


# =========================
# DRAW (fallback safe)
# =========================

def draw_layers(D1,D2,D3,D4,MR):
    if not HAS_MPL:
        st.warning("⚠️ ไม่มี matplotlib → ไม่สามารถแสดงรูป layer")
        return None

    fig, ax = plt.subplots()

    layers = [D1,D2,D3,D4]
    colors = ["#111111","#5f8f9f","#8b5a2b","#d4a017"]

    bottom = 0
    for d,c in zip(layers,colors):
        ax.bar(0,d,bottom=bottom)
        ax.text(0,bottom+d/2,f"{d} cm",ha='center',color='white')
        bottom += d

    ax.text(0,-5,f"MR={MR:.0f} psi",ha='center')
    ax.axis('off')
    return fig


# =========================
# UI (เหมือนเว็บ)
# =========================

st.set_page_config(layout="wide")
st.title("🏗️ หน้าตัดโครงสร้างทาง (AASHTO 1993)")

col1,col2 = st.columns([1,2])

with col1:
    st.subheader("Input")

    W18 = st.number_input("ESAL", value=1_000_000)
    R = st.selectbox("Reliability (%)",[80,85,90,95,98])
    ZR = reliability_to_zr(R)

    So = st.number_input("So", value=0.45)
    dPSI = st.number_input("ΔPSI", value=1.7)

    CBR = st.number_input("CBR", value=5.0)
    MR = cbr_to_mr(CBR)

    sat = st.slider("Water saturation (%)",0,100,10)
    m2 = drainage(sat)
    m3 = drainage(sat)
    m4 = drainage(sat)

    st.write(f"m2={m2}, m3={m3}, m4={m4}")

    st.markdown("### Cost")
    c1 = st.number_input("AC",10.0)
    c2 = st.number_input("Base",6.0)
    c3 = st.number_input("Subbase",4.0)
    c4 = st.number_input("Subgrade",2.0)

    run = st.button("🚀 Calculate")


with col2:
    st.subheader("Result")

    if run:
        SN = solve_SN(W18,ZR,So,dPSI,MR)

        result = optimize(SN,0.44,0.14,0.11,0.08,m2,m3,m4,[c1,c2,c3,c4])

        cost,D1,D2,D3,D4 = result

        st.success(f"✅ SN={SN:.3f}")

        st.markdown(f"""
        ### Thickness
        - D1 = {D1} cm
        - D2 = {D2} cm
        - D3 = {D3} cm
        - D4 = {D4} cm
        """)

        fig = draw_layers(D1,D2,D3,D4,MR)
        if fig:
            st.pyplot(fig)

        # ===== PDF =====
        if st.button("📄 Export PDF"):
            if not HAS_PDF:
                st.error("❌ ไม่มี reportlab → export PDF ไม่ได้")
            else:
                doc = SimpleDocTemplate("report.pdf")
                styles = getSampleStyleSheet()

                story = []
                story.append(Paragraph(f"SN = {SN:.2f}", styles["Normal"]))
                story.append(Paragraph(f"D1={D1} cm D2={D2} cm D3={D3} cm D4={D4} cm", styles["Normal"]))

                doc.build(story)
                st.success("✅ Export PDF สำเร็จ")
