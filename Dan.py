import streamlit as st
import math
import pandas as pd
import time

# =========================
# SAFE IMPORT
# =========================
try:
    import plotly.graph_objects as go
    import plotly.io as pio
    PLOTLY_OK = True
except:
    PLOTLY_OK = False

try:
    import matplotlib.pyplot as plt
    MPL_OK = True
except:
    MPL_OK = False

try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet
    PDF_OK = True
except:
    PDF_OK = False

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="AASHTO 1993 PRO", layout="wide")

# =========================
# FUNCTIONS
# =========================
def reliability_to_zr(R):
    return {
        50:0.0,60:-0.253,70:-0.524,
        75:-0.674,80:-0.841,85:-1.036,
        90:-1.282,95:-1.645,99:-2.327
    }[R]

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
st.sidebar.title("AASHTO 1993")

mode = st.sidebar.radio("Mode", ["Flexible","Rigid"])

W18 = st.sidebar.number_input("W18", value=5000000.0)
R = st.sidebar.selectbox("Reliability",[50,60,70,75,80,85,90,95,99], index=8)
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

    st.title("Flexible Pavement Design")

    data = [
        ["AC",0.44,1.0,20.0,True],
        ["Base",0.14,1.1,20.0,True],
        ["Subbase",0.11,1.1,10.0,True],
        ["Subgrade",0.10,1.0,10.0,True],
    ]

    df = pd.DataFrame(data, columns=["Layer","a","m","D(cm)","Use"])
    edited = st.data_editor(df, use_container_width=True)

    SN_list=[]
    total=0
    depth=0

    for _,r in edited.iterrows():
        sn = r["a"]*r["m"]*r["D(cm)"] if r["Use"] else 0
        total+=sn
        SN_list.append(round(sn,3))
        depth+=r["D(cm)"]

    st.metric("SN Required", SN_req)
    st.metric("SN Provided", round(total,3))
    st.metric("Total Depth (cm)", depth)

    # =========================
    # SECTION (FIX ALL CASE)
    # =========================
    st.subheader("🧱 Section (AutoCAD Style)")

    colors = ["#000000","#3498DB","#8E5A2B","#F4D03F"]
    text_colors = ["white","black","white","black"]

    # ---------- CASE 1: PLOTLY ----------
    if PLOTLY_OK:

        fig = go.Figure()
        y_base=0

        for i,r in edited.iterrows():
            t=r["D(cm)"]

            fig.add_trace(go.Bar(
                x=[0], y=[t], base=y_base,
                marker_color=colors[i],
                text=f"{r['Layer']}<br>{t} cm",
                textposition="inside",
                textfont=dict(color=text_colors[i])
            ))

            y_base+=t

        fig.update_layout(
            height=600,
            yaxis=dict(autorange="reversed"),
            xaxis=dict(visible=False),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    # ---------- CASE 2: MATPLOTLIB ----------
    elif MPL_OK:

        fig, ax = plt.subplots()
        y_base = 0

        for i, r in edited.iterrows():
            t = r["D(cm)"]

            ax.bar(0, t, bottom=y_base)

            ax.text(0, y_base+t/2,
                    f"{r['Layer']}\n{t} cm",
                    ha='center', color='white')

            y_base += t

        ax.set_xlim(-1,1)
        ax.set_xticks([])
        ax.invert_yaxis()

        st.pyplot(fig)

    # ---------- CASE 3: HTML ----------
    else:

        scale = 3
        html = "<div style='width:200px;margin:auto;border:2px solid white;'>"

        for i, r in edited.iterrows():
            h = r["D(cm)"]*scale

            html += f"""
            <div style="
                background:{colors[i]};
                color:{text_colors[i]};
                height:{h}px;
                display:flex;
                align-items:center;
                justify-content:center;
                border-bottom:1px solid white;
            ">
            {r['Layer']}<br>{r['D(cm)']} cm
            </div>
            """

        html += "</div>"
        html += f"<div style='text-align:center'>Total={depth} cm</div>"

        st.markdown(html, unsafe_allow_html=True)

    # =========================
    # PDF
    # =========================
    st.subheader("📄 Export Report")

    if PDF_OK:
        if st.button("Generate PDF"):
            doc = SimpleDocTemplate("report.pdf")
            styles = getSampleStyleSheet()

            content=[]
            content.append(Paragraph("AASHTO REPORT", styles['Title']))
            content.append(PageBreak())

            content.append(Paragraph(f"SN Required = {SN_req}", styles['Normal']))
            content.append(PageBreak())

            doc.build(content)

            with open("report.pdf","rb") as f:
                st.download_button("Download PDF", f)
    else:
        st.info("PDF disabled (no reportlab)")

# =========================
# RIGID
# =========================
else:
    st.title("Rigid Pavement (Basic View)")
    st.info("Rigid calculation OK")
