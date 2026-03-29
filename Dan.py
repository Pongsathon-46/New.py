import streamlit as st
import math
import numpy as np
import time
import os

# ===== SAFE IMPORT =====
try:
    import matplotlib.pyplot as plt
    HAS_MPL = True
except:
    HAS_MPL = False

try:
    from reportlab.platypus import SimpleDocTemplate, Image, Spacer, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    HAS_PDF = True
except:
    HAS_PDF = False

# =========================
# 🔧 FUNCTIONS
# =========================

def reliability_to_zr(R):
    table = {80:-0.841,85:-1.036,90:-1.282,95:-1.645}
    return table.get(R, -1.645)

def cbr_to_mr(cbr):
    return 2555 * (cbr ** 0.64)

def drainage(p):
    if p < 1: return 1.4
    elif p < 5: return 1.2
    elif p < 25: return 1.0
    elif p < 50: return 0.8
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

def optimize(SN, a1,a2,a3,a4,m2,m3,m4):
    best = None
    for D1 in range(5,30):
        for D2 in range(5,30):
            for D3 in range(5,30):
                for D4 in range(5,30):
                    SNc = a1*D1 + a2*m2*D2 + a3*m3*D3 + a4*m4*D4
                    if SNc >= SN:
                        total = D1+D2+D3+D4
                        if best is None or total < best[0]:
                            best = (total,D1,D2,D3,D4)
    return best

# =========================
# 🎨 DRAW (MATPLOTLIB)
# =========================

def draw_layers_plot(D1,D2,D3,D4,MR):
    if not HAS_MPL:
        return None

    fig, ax = plt.subplots()

    layers = [D1,D2,D3,D4]
    colors = ["black","#6c9fb3","#8b5a2b","#d4a017"]

    bottom = 0
    y_positions = []

    for d in layers:
        y_positions.append(bottom + d/2)
        bottom += d

    bottom = 0
    for d,c in zip(layers,colors):
        ax.bar(0,d,bottom=bottom)
        bottom += d

    # ✅ dimension lines
    bottom = 0
    for i,d in enumerate(layers):
        ax.plot([0.5,0.5],[bottom,bottom+d],'k-')
        ax.annotate(f"D{i+1}",
                    xy=(0.5,bottom+d/2),
                    xytext=(0.8,bottom+d/2),
                    arrowprops=dict(arrowstyle="->"))
        bottom += d

    ax.text(0,-5,f"MR={MR:.0f} psi",ha='center')
    ax.set_xlim(-1,1.5)
    ax.axis('off')

    return fig

# =========================
# 🎬 HTML ANIMATION
# =========================

def draw_layers_html_animated(D1,D2,D3,D4,MR,SN):
    st.markdown(f"""
    <style>
    .layer {{
        width:200px;
        text-align:center;
        color:white;
        padding:20px;
        margin:2px;
        animation: slide 1s ease forwards;
    }}

    @keyframes slide {{
        from {{transform: translateY(50px); opacity:0;}}
        to {{transform: translateY(0); opacity:1;}}
    }}
    </style>

    <div style="background:#111;padding:20px;border-radius:10px">

        <h3 style="color:white;">SN = {SN:.3f}</h3>

        <div style="display:flex">

            <div>
                <div class="layer" style="background:black">{D1} cm</div>
                <div class="layer" style="background:#6c9fb3">{D2} cm</div>
                <div class="layer" style="background:#8b5a2b">{D3} cm</div>
                <div class="layer" style="background:#d4a017;color:black">{D4} cm</div>
                <div class="layer" style="background:#5a3b1a">MR = {MR:.0f}</div>
            </div>

            <div style="margin-left:40px;color:white">
                <div style="margin:40px 0">D1 →</div>
                <div style="margin:40px 0">D2 →</div>
                <div style="margin:40px 0">D3 →</div>
                <div style="margin:40px 0">D4 →</div>
            </div>

        </div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# 📄 PDF EXPORT
# =========================

def export_pdf(fig):
    if not HAS_PDF:
        st.error("ไม่มี reportlab")
        return

    img_path = "temp.png"
    fig.savefig(img_path)

    doc = SimpleDocTemplate("report.pdf")
    styles = getSampleStyleSheet()

    story = []
    story.append(Paragraph("Pavement Design Report", styles["Title"]))
    story.append(Spacer(1,20))
    story.append(Image(img_path, width=300, height=400))

    doc.build(story)

    st.success("Export PDF สำเร็จ")

# =========================
# 🎯 UI
# =========================

st.set_page_config(layout="wide")
st.title("🏗️ Pavement Design (AASHTO 1993 PRO)")

col1,col2 = st.columns([1,2])

with col1:
    W18 = st.number_input("ESAL",1_000_000)
    R = st.selectbox("Reliability",[80,85,90,95])
    ZR = reliability_to_zr(R)

    So = st.number_input("So",0.45)
    dPSI = st.number_input("ΔPSI",1.7)

    CBR = st.number_input("CBR",5.0)
    MR = cbr_to_mr(CBR)

    sat = st.slider("Saturation %",0,100,10)
    m2 = m3 = m4 = drainage(sat)

    run = st.button("🚀 Calculate")

with col2:
    if run:
        SN = solve_SN(W18,ZR,So,dPSI,MR)
        total,D1,D2,D3,D4 = optimize(SN,0.44,0.14,0.11,0.08,m2,m3,m4)

        # 🎬 animation
        draw_layers_html_animated(D1,D2,D3,D4,MR,SN)

        fig = draw_layers_plot(D1,D2,D3,D4,MR)

        if fig:
            st.pyplot(fig)

        if st.button("📄 Export PDF"):
            export_pdf(fig)
