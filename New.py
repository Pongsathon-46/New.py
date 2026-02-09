import streamlit as st

def calculate_structure_number(cbr_values, thicknesses):
    sn = 0
    for cbr, thickness in zip(cbr_values, thicknesses):
        sn += (thickness / 12) * (cbr / 100)
    return sn

st.title("Structure Number Calculator - AASHTO 1993")

# รับข้อมูลจากผู้ใช้
num_layers = st.number_input("Number of Layers", min_value=1, max_value=10, value=1)

cbr_values = []
thicknesses = []

for i in range(num_layers):
    cbr = st.number_input(f"CBR Value for Layer {i+1} (%)", min_value=0.0, max_value=100.0, value=10.0)
    thickness = st.number_input(f"Thickness for Layer {i+1} (inches)", min_value=0.0, value=12.0)
    cbr_values.append(cbr)
    thicknesses.append(thickness)

if st.button("Calculate Structure Number"):
    sn = calculate_structure_number(cbr_values, thicknesses)
    st.success(f"The Structure Number (SN) is: {sn:.2f}")
