import os
import django
import streamlit as st

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "agroexpert_main.settings")
django.setup()

from .reasoning import forward_chaining_db, can_plant_db

st.title("🌱 AgroExpert - Crop Recommendation System")

pH = st.number_input("Enter soil pH:", min_value=0.0, max_value=14.0, step=0.1)
rainfall = st.number_input("Enter annual rainfall (mm):", min_value=0.0)
month = st.text_input("Enter current month (name or number):")
soilType = st.text_input("Enter soil type:")

if st.button("Get Recommendations"):
    recommendations = forward_chaining_db(pH, rainfall, month, soilType)
    if recommendations:
        for r in recommendations:
            st.subheader(f"{r['crop']} (priority {r['priority']})")
            st.write(r['reason'])
    else:
        st.warning("No crops match the given conditions.")

if st.checkbox("Check specific crop"):
    crop_name = st.text_input("Enter crop name:")
    if crop_name:
        res = can_plant_db(crop_name, pH, rainfall, month, soilType)
        st.write(f"Can we plant {crop_name}? {'✅ Yes' if res['canPlant'] else '❌ No'}")
        st.write("Explanation:", res["explanation"])