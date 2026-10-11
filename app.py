
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="MARSCOPE",
    page_icon="🔴",
    layout="wide"
)

st.title("🔴 MARSCOPE")
st.subheader("Interplanetary Survival Guide: Martian Map")

st.write(
    "Explore potential exploration sites on Mars "
    "and compare their scientific value."
)

targets = pd.DataFrame([
    {
        "Target": "Target A",
        "Latitude": 18.4,
        "Longitude": 77.6,
        "Science Value": 8
    },
    {
        "Target": "Target B",
        "Latitude": 18.6,
        "Longitude": 77.9,
        "Science Value": 5
    },
    {
        "Target": "Target C",
        "Latitude": 18.3,
        "Longitude": 77.7,
        "Science Value": 9
    }
])

st.subheader("Exploration Targets")
st.dataframe(targets, use_container_width=True)

minimum_value = st.slider(
    "Minimum science value",
    min_value=1,
    max_value=10,
    value=7
)

filtered_targets = targets[
    targets["Science Value"] >= minimum_value
]

st.subheader("Selected Targets")
st.dataframe(filtered_targets, use_container_width=True)

st.caption(
    "Prototype demonstration — all target data is fictional."
)
