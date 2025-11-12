# frontend.py
import streamlit as st
import json
import requests
import os

st.set_page_config(page_title="Buckling Load Predictor", page_icon="🧩", layout="centered")
st.title("🧩 Buckling Load Predictor")

# -----------------------------
# Shape selection and geometry inputs
# -----------------------------
shape = st.selectbox(
    "Select Shape",
    ["Select", "Cylinder", "Hollow Cylinder", "Rectangular Bar",
     "Hollow Rectangular Bar", "Plate", "Plate with Hole"]
)

length = width = thickness = outer_diameter = inner_diameter = hole_diameter = 0.0

if shape == "Cylinder":
    length = st.number_input("Length (mm)", min_value=0.0)
    outer_diameter = st.number_input("Diameter (mm)", min_value=0.0)

elif shape == "Hollow Cylinder":
    length = st.number_input("Length (mm)", min_value=0.0)
    outer_diameter = st.number_input("Outer Diameter (mm)", min_value=0.0)
    inner_diameter = st.number_input("Inner Diameter (mm)", min_value=0.0)

elif shape == "Rectangular Bar":
    length = st.number_input("Length (mm)", min_value=0.0)
    width = st.number_input("Width (mm)", min_value=0.0)
    thickness = st.number_input("Thickness (mm)", min_value=0.0)

elif shape == "Hollow Rectangular Bar":
    length = st.number_input("Length (mm)", min_value=0.0)
    width = st.number_input("Outer Width (mm)", min_value=0.0)
    thickness = st.number_input("Thickness (mm)", min_value=0.0)

elif shape == "Plate":
    length = st.number_input("Length (mm)", min_value=0.0)
    width = st.number_input("Width (mm)", min_value=0.0)
    thickness = st.number_input("Thickness (mm)", min_value=0.0)

elif shape == "Plate with Hole":
    length = st.number_input("Length (mm)", min_value=0.0)
    width = st.number_input("Width (mm)", min_value=0.0)
    thickness = st.number_input("Thickness (mm)", min_value=0.0)
    hole_diameter = st.number_input("Hole Diameter (mm)", min_value=0.0)

# -----------------------------
# Material selection
# -----------------------------
material = st.selectbox(
    "Select Material",
    [
        "CF–PLA (15% Carbon Fiber Reinforced PLA)",
        "GF–PLA (25% Glass Fiber Reinforced PLA)",
        "Standard PLA",
        "Standard ABS"
    ]
)

fibre_type_map = {
    "CF–PLA (15% Carbon Fiber Reinforced PLA)": "Carbon",
    "GF–PLA (25% Glass Fiber Reinforced PLA)": "Glass",
    "Standard PLA": "None",
    "Standard ABS": "None"
}

fibre_type = fibre_type_map.get(material, "Unknown")

# -----------------------------
# Build JSON input payload
# -----------------------------
input_data = {
    "Shape": shape if shape != "Select" else "",
    "Material": material.split(' ')[0],  # e.g., "CF–PLA"
    "Fibre_Type": fibre_type,
    "Length_mm": length,
    "Width_mm": width,
    "Thickness_mm": thickness,
    "Outer_Diameter_mm": outer_diameter,
    "Inner_Diameter_mm": inner_diameter,
    "Hole_Diameter_mm": hole_diameter,
    "Youngs_Modulus_GPa": 0,  # backend infers from material
    "Poissons_Ratio": 0,
    "Strength_0_deg_MPa": 0,
    "Strength_90_deg_MPa": 0,
    "Area_mm2": 0,
    "I_min_mm4": 0,
    "I_max_mm4": 0,
    "Buckling_Load_norm": 0,
}

# -----------------------------
# Predict button
# -----------------------------
if shape != "Select" and length > 0:
    if st.button("Predict Buckling Load"):
        try:
            API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
            response = requests.post(f"{API_URL}/predict", json=input_data)
            result = response.json()

            load = result.get("predicted_buckling_load_kN", None)
            if load is not None:
                st.success(f"✅ Predicted Buckling Load: {load:.2f} kN")
            else:
                st.error("❌ Prediction failed. Check backend logs.")
        except requests.exceptions.ConnectionError:
            st.error("⚠️ Could not connect to FastAPI backend. Is it running?")
else:
    st.info("Please select a shape and enter required dimensions.")
