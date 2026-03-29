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
        D += error

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

    auto_mode = st.toggle("🧠 Auto Design Thickness", value=True)

    df = pd.DataFrame([
        ["AC",0.44,1.0,0.0,True],
        ["Base",0.14,1.1,0.0,True],
        ["Subbase",0.11,1.1,0.0,True],
        ["Subgrade",0.10,1.0,0.0,True],
    ], columns=["Layer","a","m","D(cm)","Use"])

    edited = st.data_editor(df, use_container_width=True)

    # =========================
    # AUTO DESIGN
    # =========================
    if auto_mode:
        remaining_SN = SN_req

        for i, r in edited.iterrows():
            if r["Use"]:
                a = r["a"]
                m = r["m"]

                # แจก SN แบบลดหลั่น
                if r["Layer"] == "AC":
                    SN_layer = min(remaining_SN * 0.4, remaining_SN)
                elif r["Layer"] == "Base":
                    SN_layer = min(remaining_SN * 0.35, remaining_SN)
                elif r["Layer"] == "Subbase":
                    SN_layer = remaining_SN
                else:
                    SN_layer = 0

                if a*m > 0:
                    D = SN_layer / (a*m)
                else:
                    D = 0

                edited.at[i, "D(cm)"] = round(D,1)

                remaining_SN -= SN_layer

    # =========================
    # CALC RESULT
    # =========================
    total = sum(r["a"]*r["m"]*r["D(cm)"] for _,r in edited.iterrows() if r["Use"])
    depth = edited["D(cm)"].sum()

    st.metric("SN Required", SN_req)
    st.metric("SN Provided", round(total,3))
    st.metric("Total Depth", depth)

    st.dataframe(edited, use_container_width=True)

    st.subheader("🧱 Section View")

    colors = ["#000000","#3498DB","#8E5A2B","#F4D03F"]

    if PLOTLY_OK:
        fig = go.Figure()
        y=0
        for i,r in edited.iterrows():
            fig.add_trace(go.Bar(
                x=[0],
                y=[r["D(cm)"]],
                base=y,
                marker_color=colors[i % len(colors)],
                text=f"{r['Layer']}<br>{r['D(cm)']} cm",
                textposition="inside"
            ))
            y+=r["D(cm)"]

        fig.update_layout(height=600,
                          yaxis=dict(autorange="reversed"),
                          xaxis=dict(visible=False))
        st.plotly_chart(fig, use_container_width=True)

    else:
        html = "<div style='width:220px;margin:auto;border:2px solid black;'>"

        for i, r in edited.iterrows():
            h = r["D(cm)"] * 3
            display_h = max(h, 40)

            font_size = max(9, min(14, int(h/3)))

            label = f"{r['Layer']}<br>{r['D(cm)']} cm"

            html += f"""
<div style="
    background:{colors[i % len(colors)]};
    height:{display_h}px;
    color:white;
    display:flex;
    align-items:center;
    justify-content:center;
    border-bottom:1px solid white;
    font-size:{font_size}px;
    line-height:1.2;
    text-align:center;">
{label}
</div>
"""

        html += "</div>"
        html += f"<div style='text-align:center'>Total = {round(depth,1)} cm</div>"

        st.markdown(html, unsafe_allow_html=True)
# =========================
# RIGID
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

    st.subheader("🧱 Rigid Pavement Section")

    df_layer = pd.DataFrame([
        ["PCC Slab", round(D*2.54,2)],
        ["Subbase", 15],
        ["Subgrade", 20],
    ], columns=["Layer","D(cm)"])

    colors = ["#BDC3C7", "#8E5A2B", "#F4D03F"]
    total_depth = df_layer["D(cm)"].sum()

    if PLOTLY_OK:
        fig = go.Figure()
        y=0
        for i,r in df_layer.iterrows():
            fig.add_shape(type="rect", x0=0, x1=1, y0=y, y1=y+r["D(cm)"],
                          fillcolor=colors[i], line=dict(color="black"))

            fig.add_annotation(x=0.5, y=y+r["D(cm)"]/2,
                               text=f"{r['Layer']}<br>{r['D(cm)']} cm",
                               showarrow=False)
            y+=r["D(cm)"]

        fig.update_layout(height=650,
                          yaxis=dict(autorange="reversed"),
                          xaxis=dict(visible=False))
        st.plotly_chart(fig, use_container_width=True)

    else:
        html = "<div style='width:220px;margin:auto;border:2px solid black;'>"

        for i, r in df_layer.iterrows():
            h = r["D(cm)"] * 3
            display_h = max(h, 40)

            font_size = max(9, min(14, int(h/3)))

            label = f"{r['Layer']}<br>{r['D(cm)']} cm"

            html += f"""
<div style="
    background:{colors[i]};
    height:{display_h}px;
    display:flex;
    align-items:center;
    justify-content:center;
    border-bottom:1px solid white;
    font-size:{font_size}px;
    line-height:1.2;">
{label}
</div>
"""

        html += "</div>"
        html += f"<div style='text-align:center'>Total = {round(total_depth,1)} cm</div>"

        st.markdown(html, unsafe_allow_html=True)

    st.subheader("📊 Iteration Table")
    st.dataframe(pd.DataFrame(steps,
        columns=["Step","D (inch)","logW","Error"]),
        use_container_width=True)
