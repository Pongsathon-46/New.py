import streamlit as st
import math
import numpy as np
import matplotlib.pyplot as plt

# =========================
# 🔧 ENGINEERING FUNCTIONS
# =========================

def reliability_to_zr(R):
    table = {
        50: 0.0, 60: -0.253, 70: -0.524, 75: -0.674,
        80: -0.841, 85: -1.036, 90: -1.282,
        95: -1.645, 98: -2.054, 99: -2.327
    }
    return table.get(R, -1.645)


def cbr_to_mr(cbr):
    # nonlinear (AASHTO recommended approximation)
    return 2555 * (cbr ** 0.64)


def drainage_coefficient(percent_time_saturated):
    if percent_time_saturated < 1:
        return 1.4
    elif percent_time_saturated < 5:
        return 1.2
    elif percent_time_saturated < 25:
        return 1.0
    elif percent_time_saturated < 50:
        return 0.8
    else:
        return 0.6


def traffic_to_esal(adt, growth, years, lane_factor=0.8, truck_factor=1.5):
    total = 0
    for i in range(years):
        adt_year = adt * ((1 + growth) ** i)
        total += adt_year * 365
    return total * lane_factor * truck_factor


# =========================
# 🛣️ FLEXIBLE DESIGN
# =========================

def solve_SN(W18, ZR, So, delta_PSI, MR):
    def f(SN):
        return (
            ZR * So
            + 9.36 * math.log10(SN + 1)
            - 0.20
            + (math.log10(delta_PSI / (4.2 - 1.5)))
            / (0.40 + (1094 / (SN + 1) ** 5.19))
            + 2.32 * math.log10(MR)
            - 8.07
            - math.log10(W18)
        )

    SN = 0.5
    while SN < 10:
        if abs(f(SN)) < 0.01:
            return SN
        SN += 0.01
    return None


# =========================
# 💰 COST OPTIMIZATION (4 layers)
# =========================

def optimize_layers_cost(SN, a1, a2, a3, a4, m2, m3, m4, costs):
    best = None

    for D1 in np.arange(5, 30, 1):
        for D2 in np.arange(5, 30, 1):
            for D3 in np.arange(5, 30, 1):
                for D4 in np.arange(5, 30, 1):

                    SN_calc = (
                        a1*D1 +
                        a2*m2*D2 +
                        a3*m3*D3 +
                        a4*m4*D4
                    )

                    if SN_calc >= SN:
                        cost = (
                            D1*costs[0] +
                            D2*costs[1] +
                            D3*costs[2] +
                            D4*costs[3]
                        )

                        if best is None or cost < best[0]:
                            best = (cost, D1, D2, D3, D4)

    return best


# =========================
# 🎨 DRAW LAYERS (เหมือนรูป)
# =========================

def draw_layers(D1, D2, D3, D4, MR):
    fig, ax = plt.subplots()

    layers = [D1, D2, D3, D4]
    colors = ["black", "#6c9fb3", "#8b5a2b", "#d4a017"]

    bottom = 0
    for d, c in zip(layers, colors):
        ax.bar(0, d, bottom=bottom)
        ax.text(0, bottom + d/2, f"{d:.1f} cm",
                ha='center', color='white', fontsize=12)
        bottom += d

    ax.text(0, -5, f"MR = {MR:.0f} psi", ha='center')
    ax.set_xlim(-1, 1)
    ax.axis('off')

    return fig


# =========================
# 📊 SENSITIVITY GRAPH
# =========================

def sensitivity_plot(W18, ZR, So, delta_PSI):
    CBRs = np.linspace(2, 15, 20)
    SNs = []

    for cbr in CBRs:
        MR = cbr_to_mr(cbr)
        SN = solve_SN(W18, ZR, So, delta_PSI, MR)
        SNs.append(SN)

    fig, ax = plt.subplots()
    ax.plot(CBRs, SNs)
    ax.set_xlabel("CBR (%)")
    ax.set_ylabel("Required SN")

    return fig


# =========================
# 🎯 UI
# =========================

st.title("🚧 AASHTO 1993 Pavement Design (Advanced)")

# Sidebar
st.sidebar.header("Traffic")

adt = st.sidebar.number_input("ADT", value=5000)
growth = st.sidebar.number_input("Growth rate", value=0.05)
years = st.sidebar.number_input("Years", value=20)

W18 = traffic_to_esal(adt, growth, years)
st.sidebar.write(f"ESAL = {W18:,.0f}")

R = st.sidebar.selectbox("Reliability (%)", [50,60,70,75,80,85,90,95,98,99])
ZR = reliability_to_zr(R)

So = st.sidebar.number_input("So", value=0.45)
delta_PSI = st.sidebar.number_input("ΔPSI", value=1.7)

CBR = st.sidebar.number_input("CBR (%)", value=5.0)
MR = cbr_to_mr(CBR)

# Drainage
sat = st.sidebar.slider("Time Saturated (%)", 0, 100, 10)
m2 = drainage_coefficient(sat)
m3 = drainage_coefficient(sat)
m4 = drainage_coefficient(sat)

st.sidebar.write(f"m2 = {m2}, m3 = {m3}, m4 = {m4}")

# Layer properties
st.header("Layer Properties")

a1 = st.number_input("a1 (AC)", value=0.44)
a2 = st.number_input("a2 (Base)", value=0.14)
a3 = st.number_input("a3 (Subbase)", value=0.11)
a4 = st.number_input("a4 (Selected Subgrade)", value=0.08)

st.subheader("Cost (per cm)")
c1 = st.number_input("AC cost", value=10.0)
c2 = st.number_input("Base cost", value=6.0)
c3 = st.number_input("Subbase cost", value=4.0)
c4 = st.number_input("Subgrade cost", value=2.0)

if st.button("Calculate"):
    SN = solve_SN(W18, ZR, So, delta_PSI, MR)

    result = optimize_layers_cost(
        SN, a1, a2, a3, a4,
        m2, m3, m4,
        [c1, c2, c3, c4]
    )

    cost, D1, D2, D3, D4 = result

    st.success(f"SN Required = {SN:.3f}")
    st.write(f"Total Cost = {cost:.2f}")

    st.write("### Thickness (cm)")
    st.write(f"D1 = {D1}")
    st.write(f"D2 = {D2}")
    st.write(f"D3 = {D3}")
    st.write(f"D4 = {D4}")

    st.pyplot(draw_layers(D1, D2, D3, D4, MR))
    st.pyplot(sensitivity_plot(W18, ZR, So, delta_PSI))
