import streamlit as st
import math
import pandas as pd

# =========================
# SAFE IMPORT
# =========================
try:
    import plotly.graph_objects as go
    PLOTLY_OK = True
except:
    PLOTLY_OK = False

try:
    import matplotlib.pyplot as plt
    MPL_OK = True
except:
    MPL_OK = False

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

# 🔥 RIGID ITERATIVE (เต็มสูตร)
def calc_rigid_full(W18, ZR, So, Sc, Cd, J, k):
    D = 8
    steps = []

    for i in range(20):
        term1 = ZR*So
        term2 = 7.35*math.log10(D+1) - 0.06
        term3 = math.log10((Sc*Cd)/(215.63*J*(D**0.75)))
        term4 = 1.624*math.log10(D)

        logW = term1 + term2 + term3 + term4
        error = math.log10(W18) - logW

        steps.append([i+1, round(D,3), round(logW,3), round(error,4)])

        D = D + error

    return round(D,2), steps

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

    st.title("Flexible Pavement")

    data = [
        ["AC",0.44,1.0,20.0,True],
        ["Base",0.14,1.1,20.0,True],
        ["Subbase",0.11,1.1,10.0,True],
        ["Subgrade",0.10,1.0,10.0,True],
    ]

    df = pd.DataFrame(data, columns=["Layer","a","m","D(cm)","Use"])
    edited = st.data_editor(df, use_container_width=True)

    total = 0
    depth = 0

    for _,r in edited.iterrows():
        if r["Use"]:
            total += r["a"]*r["m"]*r["D(cm)"]
        depth += r["D(cm)"]

    st.metric("SN Required", SN_req)
    st.metric("SN Provided", round(total,3))
    st.metric("Total Depth", depth)

    # =========================
    # SECTION (แสดงแน่นอน)
    # =========================
    st.subheader("🧱 Section View")

    colors = ["#000000","#3498DB","#8E5A2B","#F4D03F"]

    # ✅ Plotly
    if PLOTLY_OK:
        fig = go.Figure()
        y=0
        for i,r in edited.iterrows():
            fig.add_trace(go.Bar(
                x=[0],
                y=[r["D(cm)"]],
                base=y,
                marker_color=colors[i],
                text=f"{r['Layer']}<br>{r['D(cm)']} cm",
                textposition="inside"
            ))
            y+=r["D(cm)"]

        fig.update_layout(height=600,
                          yaxis=dict(autorange="reversed"),
                          xaxis=dict(visible=False))

        st.plotly_chart(fig, use_container_width=True)

    # ✅ Matplotlib
    elif MPL_OK:
        fig, ax = plt.subplots()
        y=0
        for i,r in edited.iterrows():
            ax.bar(0, r["D(cm)"], bottom=y)
            ax.text(0, y+r["D(cm)"]/2,
                    f"{r['Layer']}\n{r['D(cm)']} cm",
                    ha='center', color='white')
            y+=r["D(cm)"]

        ax.set_xticks([])
        ax.invert_yaxis()
        st.pyplot(fig)

    # ✅ HTML (สุดท้าย)
   else:

    html = ""

    for i, r in df_layer.iterrows():
        html += f"<div style='background:{colors[i]}; height:{r['D(cm)']*3}px; color:black; display:flex; align-items:center; justify-content:center; border-bottom:1px solid white;'>"
        html += f"{r['Layer']}<br>{r['D(cm)']} cm"
        html += "</div>"

    html = f"""
    <div style='width:200px;margin:auto;border:2px solid black;'>
    {html}
    </div>
    <div style='text-align:center;margin-top:10px;'>
    Total = {round(total_depth,1)} cm
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
# =========================
# RIGID (เพิ่ม Section View)
# =========================
else:

    st.title("Rigid Pavement (AASHTO 1993)")

    Sc = st.sidebar.number_input("Sc (psi)", value=650.0)
    Cd = st.sidebar.number_input("Cd", value=1.0)
    J = st.sidebar.number_input("J", value=3.2)
    k = st.sidebar.number_input("k (pci)", value=100.0)

    D, steps = calc_rigid_full(W18, ZR, So, Sc, Cd, J, k)

    st.metric("Thickness (inch)", D)
    st.metric("Thickness (cm)", round(D*2.54,2))

    # =========================
    # SECTION VIEW (🔥 เพิ่ม)
    # =========================
    st.subheader("🧱 Rigid Pavement Section")

    # layer data (สามารถแก้ได้)
    layers = [
        ["PCC Slab", round(D*2.54,2)],   # แปลงเป็น cm
        ["Subbase", 15],
        ["Subgrade", 20],
    ]

    df_layer = pd.DataFrame(layers, columns=["Layer","D(cm)"])

    colors = ["#BDC3C7", "#8E5A2B", "#F4D03F"]

    total_depth = df_layer["D(cm)"].sum()
    # ---------- Plotly (IMPROVED SECTION VIEW) ----------
    if PLOTLY_OK:

        fig = go.Figure()
        y = 0

        for i, r in df_layer.iterrows():

            y0 = y
            y1 = y + r["D(cm)"]

            # 🔹 วาด layer เป็น block จริง
            fig.add_shape(
                type="rect",
                x0=0, x1=1,
                y0=y0, y1=y1,
                fillcolor=colors[i],
                line=dict(color="black")
            )

            # 🔹 ข้อความกลาง layer
            fig.add_annotation(
                x=0.5,
                y=(y0 + y1)/2,
                text=f"{r['Layer']}<br>{r['D(cm)']} cm",
                showarrow=False,
                font=dict(color="black", size=14)
            )

            # 🔹 เส้น dimension บน
            fig.add_shape(
                type="line",
                x0=1.1, x1=1.2,
                y0=y0, y1=y0,
                line=dict(color="black")
            )

            # 🔹 เส้น dimension ล่าง
            fig.add_shape(
                type="line",
                x0=1.1, x1=1.2,
                y0=y1, y1=y1,
                line=dict(color="black")
            )

            # 🔹 เส้นแนวตั้ง (บอกความหนา)
            fig.add_shape(
                type="line",
                x0=1.15, x1=1.15,
                y0=y0, y1=y1,
                line=dict(color="black", dash="dot")
            )

            # 🔹 label ความหนา
            fig.add_annotation(
                x=1.3,
                y=(y0 + y1)/2,
                text=f"{r['D(cm)']} cm",
                showarrow=False
            )

            y = y1

        # 🔹 total depth
        fig.add_annotation(
            x=0.5,
            y=total_depth + 5,
            text=f"Total Depth = {round(total_depth,1)} cm",
            showarrow=False,
            font=dict(size=16)
        )

        fig.update_layout(
            height=650,
            yaxis=dict(autorange="reversed", title="Depth (cm)"),
            xaxis=dict(visible=False),
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)

    # ---------- Matplotlib ----------
    elif MPL_OK:

        fig, ax = plt.subplots()
        y = 0

        for i, r in df_layer.iterrows():
            ax.bar(0, r["D(cm)"], bottom=y)

            ax.text(0, y + r["D(cm)"]/2,
                    f"{r['Layer']}\n{r['D(cm)']} cm",
                    ha='center', color='black')

            y += r["D(cm)"]

        ax.set_xticks([])
        ax.invert_yaxis()

        st.pyplot(fig)

    # ---------- HTML ----------
    else:

        html = "<div style='width:200px;margin:auto;border:2px solid white;'>"

        for i, r in df_layer.iterrows():
            html += f"""
            <div style="
                background:{colors[i]};
                height:{r['D(cm)']*3}px;
                color:black;
                display:flex;
                align-items:center;
                justify-content:center;
                border-bottom:1px solid white;
            ">
            {r['Layer']}<br>{r['D(cm)']} cm
            </div>
            """

        html += "</div>"
        html += f"<div style='text-align:center'>Total = {round(total_depth,1)} cm</div>"

        st.markdown(html, unsafe_allow_html=True)

    # =========================
    # ITERATION TABLE
    # =========================
    st.subheader("📊 Iteration Table")

    df_steps = pd.DataFrame(steps,
        columns=["Step","D (inch)","logW","Error"])

    st.dataframe(df_steps, use_container_width=True)

    st.info("Iterative solution until convergence (AASHTO 1993)")
