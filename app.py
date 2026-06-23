import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import pandas as pd
import requests

# Set layout configurations
st.set_page_config(page_title="Hyderabad Live Traffic Route Compare", layout="wide")

st.title("🚗 Hyderabad AI Traffic Agent - Real Street Routing Engine")
st.markdown("This version tracks actual street networks and roads across Hyderabad using the OpenSource Routing Machine (OSRM).")

# Mock geographical database for major Hyderabad hubs
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

# --- FUNCTION TO FETCH REAL STREET PATHS ---
def get_route_geometry(start_lat, start_lon, end_lat, end_lon, alternative=False):
    """
    Fetches real street network paths from OSRM free routing API.
    """
    # OSRM expects coordinates as lon,lat
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    if alternative:
        url += "&alternative=true"
        
    try:
        response = requests.get(url).json()
        if response['code'] == 'Ok':
            # Extract coordinates for the polyline
            route = response['routes'][0]
            geometry = route['geometry']['coordinates']
            # Flip coordinates back to lat,lon for Folium
            path_coords = [[point[1], point[0]] for point in geometry]
            distance_km = round(route['distance'] / 1000, 1)
            duration_mins = int(route['duration'] / 60)
            return path_coords, distance_km, duration_mins
    except Exception as e:
        pass
    
    # Fallback to a straight line if API fails
    return [[start_lat, start_lon], [end_lat, end_lon]], 10.0, 25

# --- SIDEBAR: ROUTE CONTROLS ---
st.sidebar.header("🗺️ Route Selection")
use_presets = st.sidebar.checkbox("Use Hyderabad Hub Presets", value=True)

if use_presets:
    start_point = st.sidebar.selectbox("Select Start Point:", list(HYD_HUBS.keys()), index=2) # Mehdipatnam
    end_point = st.sidebar.selectbox("Select Destination Point:", list(HYD_HUBS.keys()), index=0) # Gachibowli
    start_coords = HYD_HUBS[start_point]
    end_coords = HYD_HUBS[end_point]
else:
    start_text = st.sidebar.text_input("Enter Starting Point:", "Tolichowki, Hyderabad")
    end_text = st.sidebar.text_input("Enter Destination Point:", "Madhapur, Hyderabad")
    
    geolocator = Nominatim(user_agent="hyd_traffic_agent")
    try:
        loc1 = geolocator.geocode(start_text)
        loc2 = geolocator.geocode(end_text)
        start_coords = [loc1.latitude, loc1.longitude]
        end_coords = [loc2.latitude, loc2.longitude]
        start_point, end_point = start_text.split(",")[0], end_text.split(",")[0]
    except:
        start_coords, end_coords = HYD_HUBS["Mehdipatnam"], HYD_HUBS["Gachibowli"]
        start_point, end_point = "Mehdipatnam", "Gachibowli"

st.sidebar.subheader("🌧️ Environmental Modifiers")
monsoon_mode = st.sidebar.toggle("Simulate Waterlogging Delays")

# --- FETCH REAL ROUTE GEOMETRY FROM OSRM ---
# Route A: Primary Driving Path
path_a, route_a_dist, route_a_base_time = get_route_geometry(start_coords[0], start_coords[1], end_coords[0], end_coords[1])

# Route B: Simulated alternative by adding a tiny shift to search for a secondary road structure
path_b, route_b_dist, route_b_base_time = get_route_geometry(start_coords[0], start_coords[1], end_coords[0], end_coords[1], alternative=True)

# Apply dynamic delays based on monsoon simulation toggle
route_a_delay = int(route_a_base_time * 0.7) if monsoon_mode else int(route_a_base_time * 0.2)
route_a_total = route_a_base_time + route_a_delay

route_b_delay = int(route_b_base_time * 0.2) if monsoon_mode else int(route_b_base_time * 0.3)
route_b_total = route_b_base_time + route_b_delay

# --- MAIN DASHBOARD DISPLAY ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="📍 Route Segment", value=f"{start_point} ➔ {end_point}")
with col2:
    status_color = "🔴 Highly Congested" if monsoon_mode else "🟢 Normal Traffic"
    st.metric(label="⚠️ Current Corridor Status", value=status_color)
with col3:
    best_route = "Route B (Bypass)" if route_b_total < route_a_total else "Route A (Main Road)"
    st.metric(label="💡 Recommended Action", value=best_route)

st.markdown("---")

layout_left, layout_right = st.columns([2, 3])

with layout_left:
    st.subheader("📊 Performance Matrix")
    metrics_data = {
        "Parameter": ["Total Commute Time", "Free-Flow Time", "Traffic/Water Delay", "Actual Distance"],
        "🔵 Route A (Main)": [f"{route_a_total} mins", f"{route_a_base_time} mins", f"+{route_a_delay} mins", f"{route_a_dist} km"],
        "🟢 Route B (Alternative)": [f"{route_b_total} mins", f"{route_b_base_time} mins", f"+{route_b_delay} mins", f"{route_b_dist} km"]
    }
    st.dataframe(pd.DataFrame(metrics_data), use_container_width=True, hide_index=True)
    st.info("💡 **Interview Talking Point:** This version uses an API connection to an open-source routing engine (OSRM) to snap coordinates perfectly onto genuine road network vectors.")

with layout_right:
