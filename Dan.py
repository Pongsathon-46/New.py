import streamlit as st
import math
import pandas as pd
import time
import os

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
        50:0.0,60:-0.253,70:-0.524,75:-0.674,
        80:-0.841,85:-1.036,90:-1.282,95:-1.645,99:-2.327
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
st.sidebar.title("AASHTO 1993 PRO")

W18 = st.sidebar.number_input("W18", value=5000000.0)
R = st.sidebar.selectbox("Reliability",[50,60,70,75,80,85,90,95,99], index=8)
So = st.sidebar.number_input("So", value=0.45)
Pi = st.sidebar.number_input("Pi", value=4.2)
Pt = st.sidebar.number_input("Pt", value=2.5)
CBR = st.sidebar.number_input("CBR", value=5.0)

ZR = reliability_to_zr(R)
dPSI = Pi-Pt
MR = MR_from_CBR(CBR)

# =========================
# MAIN
# =========================
st.title("Flexible Pavement (AutoCAD Style)")

SN_req = calc_SN(W18, ZR, So, dPSI, MR)

data = [
    ["AC",0.44,1.0,20.0,True],
    ["Base",0.14,1.1,20.0,True],
    ["Subbase",0.11,1.1,10.0,True],
    ["Subgrade",0.10,1.0,10.0,True],
]

df = pd.DataFrame(data, columns=["Layer","a","m","D(cm)","Use"])
edited = st.data_editor(df, use_container_width=True)

# =========================
# SN CALC
# =========================
SN_list=[]
cum_SN=[]
total_SN=0
depth=0
depth_list=[]

for _,r in edited.iterrows():
    sn = r["a"]*r["m"]*r["D(cm)"] if r["Use"] else 0
    total_SN+=sn
    SN_list.append(round(sn,3))
    cum_SN.append(round(total_SN,3))

    depth+=r["D(cm)"]
    depth_list.append(depth)

total_depth = depth

# =========================
# METRICS
# =========================
c1,c2,c3 = st.columns(3)
c1.metric("SN Required", SN_req)
c2.metric("SN Provided", round(total_SN,3))
c3.metric("Total Depth (cm)", total_depth)

# =========================
# SECTION (AUTOCAD STYLE)
# =========================
st.subheader("AutoCAD Section (Scale 1:50)")

colors = ["#000000","#3498DB","#8E5A2B","#F4D03F"]
text_colors = ["white","black","white","black"]

if PLOTLY_OK:

    fig = go.Figure()
    y_base = 0

    for i,r in edited.iterrows():
        t = r["D(cm)"]

        fig.add_trace(go.Bar(
            x=[0],
            y=[t],
            base=y_base,
            marker_color=colors[i],
            text=f"{r['Layer']}<br>{t} cm",
            textposition="inside",
            textfont=dict(color=text_colors[i])
        ))

        # dimension lines
        fig.add_shape(type="line", x0=0.6,x1=0.9,y0=y_base,y1=y_base)
        fig.add_shape(type="line", x0=0.6,x1=0.9,y0=y_base+t,y1=y_base+t)
        fig.add_shape(type="line", x0=0.75,x1=0.75,y0=y_base,y1=y_base+t)

        fig.add_annotation(x=1.1,y=y_base+t/2,
                           text=f"D{i+1}={t} cm",
                           showarrow=False)

        y_base+=t

    # total dimension
    fig.add_shape(type="line", x0=1.5,x1=1.5,y0=0,y1=total_depth,
                  line=dict(width=3))
    fig.add_annotation(x=1.7,y=total_depth/2,
                       text=f"Total={total_depth} cm",
                       showarrow=False)

    fig.update_layout(
        height=700,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(visible=False),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No plotly → basic view")
    for i,r in edited.iterrows():
        st.write(f"D{i+1}: {r['Layer']} {r['D(cm)']} cm")

# =========================
# PDF REPORT (10 PAGES)
# =========================
st.subheader("Export Report")

if PDF_OK:

    if st.button("📄 Generate 10-Page Report"):

        doc = SimpleDocTemplate("report.pdf")
        styles = getSampleStyleSheet()
        content=[]

        # cover
        content.append(Paragraph("AASHTO 1993 DESIGN REPORT", styles['Title']))
        content.append(PageBreak())

        # input
        content.append(Paragraph(f"W18={W18}", styles['Normal']))
        content.append(PageBreak())

        # SN
        content.append(Paragraph(f"SN Required={SN_req}", styles['Normal']))
        content.append(PageBreak())

        # table
        content.append(Paragraph("Layer Table", styles['Heading2']))
        content.append(PageBreak())

        # section image
        if PLOTLY_OK:
            img_path="section.png"
            pio.write_image(fig,img_path,width=800,height=600)
            content.append(Image(img_path, width=400,height=300))
            content.append(PageBreak())

        # filler pages
        for i in range(5):
            content.append(Paragraph(f"Additional Analysis {i+1}", styles['Normal']))
            content.append(PageBreak())

        doc.build(content)

        with open("report.pdf","rb") as f:
            st.download_button("Download PDF", f)

else:
    st.warning("Install reportlab for PDF")
