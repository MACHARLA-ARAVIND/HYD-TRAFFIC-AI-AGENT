import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import pandas as pd

# Set layout configurations
st.set_page_config(page_title="Hyderabad Live Traffic Route Compare", layout="wide")

# Setup Title
st.title("🚗 Hyderabad AI Traffic Agent - Route Comparison Matrix")
st.markdown("Compare optimal corridors, bottleneck factors, and estimated time delays across the twin cities.")

# Mock geographical database for major Hyderabad hubs to guarantee quick local fallback
HYD_HUBS = {
    "Gachibowli": [17.4401, 78.3489],
    "HITEC City / Mindspace": [17.4435, 78.3773],
    "Mehdipatnam": [17.3950, 78.4312],
    "Secunderabad Station": [17.4347, 78.5016],
    "Begumpet Airport": [17.4485, 78.4682],
    "Charminar": [17.3616, 78.4747],
    "Jubilee Hills Checkpost": [17.4278, 78.4063],
    "Kukatpally": [17.4948, 78.3996]
}

# --- SIDEBAR: ROUTE CONTROLS ---
st.sidebar.header("🗺️ Route Selection")

# Fallback presets or manual input options
use_presets = st.sidebar.checkbox("Use Hyderabad Hub Presets", value=True)

if use_presets:
    start_point = st.sidebar.selectbox("Select Start Point:", list(HYD_HUBS.keys()), index=2) # Default Mehdipatnam
    end_point = st.sidebar.selectbox("Select Destination Point:", list(HYD_HUBS.keys()), index=0) # Default Gachibowli
    
    start_coords = HYD_HUBS[start_point]
    end_coords = HYD_HUBS[end_point]
else:
    # Manual location parsing fallback via geocoder
    start_text = st.sidebar.text_input("Enter Starting Point (e.g., Tolichowki, Hyderabad):", "Tolichowki, Hyderabad")
    end_text = st.sidebar.text_input("Enter Destination Point (e.g., Madhapur, Hyderabad):", "Madhapur, Hyderabad")
    
    geolocator = Nominatim(user_agent="hyd_traffic_agent")
    try:
        loc1 = geolocator.geocode(start_text)
        loc2 = geolocator.geocode(end_text)
        start_coords = [loc1.latitude, loc1.longitude] if loc1 else HYD_HUBS["Mehdipatnam"]
        end_coords = [loc2.latitude, loc2.longitude] if loc2 else HYD_HUBS["Gachibowli"]
        start_point, end_point = start_text.split(",")[0], end_text.split(",")[0]
    except Exception:
        st.sidebar.error("Geocoding failed. Using Mehdipatnam -> Gachibowli default.")
        start_coords, end_coords = HYD_HUBS["Mehdipatnam"], HYD_HUBS["Gachibowli"]
        start_point, end_point = "Mehdipatnam", "Gachibowli"

# Simulation parameters based on simulated time-of-day/season
st.sidebar.subheader("🌧️ Environmental Modifiers")
monsoon_mode = st.sidebar.toggle("Simulate Waterlogging Delays (Monsoon/Heavy Rain)")

# --- TRAFFIC DATA CALCULATION MODEL ---
# Generating realistic routing comparative models
base_distance = abs(start_coords[0] - end_coords[0]) * 111 + abs(start_coords[1] - end_coords[1]) * 111

# Route A - Main Arterial (e.g., via Main Flyovers / Khajaguda / Shaikpet Corridor)
route_a_dist = round(base_distance, 1)
route_a_base_time = int(route_a_dist * 2.5)
route_a_delay = int(route_a_base_time * 0.6) if monsoon_mode else int(route_a_base_time * 0.15)
route_a_total = route_a_base_time + route_a_delay

# Route B - Alternative Loop (e.g., ORR / Outer Bypass Corridor)
route_b_dist = round(base_distance * 1.3, 1) # Generally longer but faster moving
route_b_base_time = int(route_b_dist * 1.8)
route_b_delay = int(route_b_base_time * 0.1) # Less affected by minor junctions/waterlogging
route_b_total = route_b_base_time + route_b_delay

# --- MAIN PAGE DASHBOARD LAYOUT ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="📍 Route Segment", value=f"{start_point} ➔ {end_point}")
with col2:
    status_color = "🔴 Highly Congested" if monsoon_mode else "🟢 Normal / Moderate Rush"
    st.metric(label="⚠️ Current Corridor Status", value=status_color)
with col3:
    best_route = "Alternative Bypass" if route_b_total < route_a_total else "Main Arterial Corridor"
    st.metric(label="💡 Recommended Action", value=best_route)

st.markdown("---")

# Split screen layout: Metrics Table vs. Interactive Visual Map
layout_left, layout_right = st.columns([2, 3])

with layout_left:
    st.subheader("📊 Comparative Route Performance Metrics")
    
    metrics_data = {
        "Metric Parameter": ["Total Estimated Time", "Baseline Free-Flow Time", "Traffic/Waterlogging Delay", "Total Commute Distance", "Primary Bottleneck Risk"],
        "🔵 Route A (Main Arterial)": [f"{route_a_total} mins", f"{route_a_base_time} mins", f"+{route_a_delay} mins", f"{route_a_dist} km", "High (Waterlogging Junctions)"],
        "🟢 Route B (Alternative Bypass)": [f"{route_b_total} mins", f"{route_b_base_time} mins", f"+{route_b_delay} mins", f"{route_b_dist} km", "Low (Free Flow Loop)"]
    }
    df = pd.DataFrame(metrics_data)
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.info(
        "💡 **AI Traffic Agent Insight:** Alternative bypass tracks remain structurally optimal during high-intensity rush hours, "
        "even when geographic distance expands, due to uninhibited speeds along the Outer Radial links."
    )

with layout_right:
    st.subheader("🗺️ Live Vector Map Engine")
    
    # Initialize Folium base map centered dynamically between locations
    map_center = [(start_coords[0] + end_coords[0])/2, (start_coords[1] + end_coords[1])/2]
    m = folium.Map(location=map_center, zoom_start=13, tiles="OpenStreetMap")
    
    # Markers for Start and End coordinates
    folium.Marker(location=start_coords, popup=f"Start: {start_point}", icon=folium.Icon(color="blue", icon="play")).add_to(m)
    folium.Marker(location=end_coords, popup=f"End: {end_point}", icon=folium.Icon(color="red", icon="flag")).add_to(m)
    
    # Generate simple comparative paths (visual approximations)
    path_a = [start_coords, end_coords]
    # Creating a bent arc polyline path for Route B bypass
    midpoint_offset = [map_center[0] + 0.015, map_center[1] - 0.015]
    path_b = [start_coords, midpoint_offset, end_coords]
    
    # Plotting routes to interactive map layer
    folium.PolyLine(path_a, color="blue", weight=5, opacity=0.8, tooltip="Route A: Main Arterial").add_to(m)
    folium.PolyLine(path_b, color="green", weight=5, opacity=0.8, tooltip="Route B: Alternative Bypass").add_to(m)
    
    # Render map objects back directly into Streamlit ecosystem
    st_folium(m, width=700, height=450, returned_objects=[])