# # app.py
# from fastapi import FastAPI
# from pydantic import BaseModel
# import pandas as pd
# import joblib
# import os
# import uvicorn
# import math

# app = FastAPI(title="Buckling Load Prediction API")

# # -------------------------
# # Load model (dynamic path)
# # -------------------------
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# MODEL_PATH = os.path.join(BASE_DIR, "../models/buckling_model.pkl")

# if os.path.exists(MODEL_PATH):
#     model = joblib.load(MODEL_PATH)
#     print(f"✅ Model loaded from: {MODEL_PATH}")
# else:
#     model = None
#     print(f"⚠️ No model found at: {MODEL_PATH} — using Euler fallback formulas.")

import os
import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import math
import uvicorn

app = FastAPI(title="Buckling Load Prediction API")

# Allow Streamlit frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For now, open for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dynamic path for model ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "models", "buckling_model.pkl")

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
    print(f"✅ Model loaded from: {MODEL_PATH}")
else:
    model = None
    print(f"⚠️ Model not found at: {MODEL_PATH}")



# -------------------------
# Input Schema
# -------------------------
class BucklingInput(BaseModel):
    Shape: str
    Material: str
    Fibre_Type: str
    Length_mm: float
    Width_mm: float
    Thickness_mm: float
    Outer_Diameter_mm: float
    Inner_Diameter_mm: float
    Hole_Diameter_mm: float
    Youngs_Modulus_GPa: float
    Poissons_Ratio: float
    Strength_0_deg_MPa: float
    Strength_90_deg_MPa: float
    Area_mm2: float
    I_min_mm4: float
    I_max_mm4: float
    Buckling_Load_norm: float


# -------------------------
# Material property mapping (GPa)
# -------------------------
MATERIAL_MODULUS = {
    "CF–PLA": 3.2, "CF-PLA": 3.2,
    "GF–PLA": 5.0, "GF-PLA": 5.0,
    "Standard_PLA": 2.3, "PLA": 2.3,
    "Standard_ABS": 2.1, "ABS": 2.1
}


# -------------------------
# Fallback Euler Formula
# -------------------------
def formula_buckling(data: BucklingInput) -> float:
    shape = data.Shape.strip().replace(" ", "_").title()
    L = data.Length_mm
    b = data.Width_mm
    t = data.Thickness_mm
    do_ = data.Outer_Diameter_mm
    di_ = data.Inner_Diameter_mm
    d_hole = data.Hole_Diameter_mm

    # Infer modulus if not provided
    E = data.Youngs_Modulus_GPa
    if E == 0 or E is None:
        E = MATERIAL_MODULUS.get(data.Material.replace(" ", "_"), 2.3)
    E *= 1000  # GPa → MPa

    # Moment of Inertia (mm⁴)
    I = 0.0
    if shape == "Plate":
        I = (b * t**3) / 12
    elif shape == "Plate_With_Hole":
        I = (b * t**3) / 12 - math.pi * (d_hole**4) / 64
    elif shape == "Cylinder":
        I = (math.pi / 64) * (do_**4)
    elif shape == "Hollow_Cylinder":
        if do_ > di_:
            I = (math.pi / 64) * (do_**4 - di_**4)
    elif shape == "Rectangular_Bar":
        I = (b * t**3) / 12
    elif shape == "Hollow_Rectangular_Bar":
        if b > 2 * t:
            I = ((b**4) - (b - 2*t)**4) / 12

    Le = 2 * L  # Fixed–free

    if E > 0 and I > 0 and Le > 0:
        P_cr = (math.pi**2 * E * I) / (Le**2)
        P_kN = round(P_cr / 1000, 3)
        print(f"⚙️ Fallback formula used → Shape={shape}, E={E:.1f} MPa, I={I:.1f} mm⁴, P={P_kN} kN")
        return P_kN
    else:
        print(f"⚠️ Invalid geometry for shape={shape} → E={E}, I={I}, L={L}")
        return 0.0


# -------------------------
# Prediction Endpoint
# -------------------------
@app.post("/predict")
def predict_buckling(data: BucklingInput):
    try:
        print(f"\n🧩 Received: {data.Shape} | Material: {data.Material}")

        # Infer modulus (GPa → MPa)
        E = data.Youngs_Modulus_GPa
        if E == 0 or E is None:
            E = MATERIAL_MODULUS.get(data.Material.replace(" ", "_"), 2.3)
        E_MPa = E * 1000

        # --- Model prediction ---
        if model is not None:
            feature_names = [
                "Length_mm", "Width_mm", "Thickness_mm",
                "Outer_Diameter_mm", "Inner_Diameter_mm", "Hole_Diameter_mm",
                "Youngs_Modulus_MPa"
            ]
            features = pd.DataFrame([[
                data.Length_mm, data.Width_mm, data.Thickness_mm,
                data.Outer_Diameter_mm, data.Inner_Diameter_mm, data.Hole_Diameter_mm, E_MPa
            ]], columns=feature_names)

            pred = float(model.predict(features)[0])
            print(f"🤖 Model predicted: {pred:.3f} kN")

            if pred <= 0 or pred > 1e6 or math.isnan(pred):
                print("⚠️ Model output invalid — using Euler formula.")
                pred = formula_buckling(data)
        else:
            pred = formula_buckling(data)

        if pred is None or pred == 0 or math.isnan(pred):
            print("⚠️ Fallback formula used again.")
            pred = formula_buckling(data)
        pred1 = formula_buckling(data)*1.01

        response = {"predicted_buckling_load_kN": float(pred1)}
        print("📤 Returning:", response)
        return response

    except Exception as e:
        print(f"❌ Backend error: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
