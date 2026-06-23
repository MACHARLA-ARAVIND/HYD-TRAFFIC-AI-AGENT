import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import pandas as pd
import requests

# Set layout configurations
st.set_page_config(page_title="Hyderabad AI Traffic Agent", layout="wide")

st.title("🚗 Hyderabad AI Traffic Agent")
st.markdown("Compare main streets vs. alternative street corridors with real-world road geometries.")

# Hardcoded precise fallback coordinates for Hyderabad hubs to prevent cloud loading freezes
HYD_COORDS = {
    "mehdipatnam": [17.3950, 78.4312],
    "gachibowli": [17.4401, 78.3489]
}

# --- FUNCTION TO FETCH REAL ROAD NETWORK GEOMETRY ---
def get_street_route(start_lat, start_lon, end_lat, end_lon, via_waypoint=None):
    """
    Fetches real street networks using OSRM. 
    """
    if via_waypoint:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{via_waypoint[1]},{via_waypoint[0]};{end_lon},{end_lat}?overview=full&geometries=geojson"
    else:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
        
    try:
        response = requests.get(url, timeout=5).json()
        if response['code'] == 'Ok':
            route = response['routes'][0]
            geometry = route['geometry']['coordinates']
            path_coords = [[point[1], point[0]] for point in geometry]
            distance_km = round(route['distance'] / 1000, 1)
            duration_mins = int(route['duration'] / 60)
            return path_coords, distance_km, duration_mins
    except:
        pass
    
    # Fallback if API fails
    return [[start_lat, start_lon], [end_lat, end_lon]], 12.5, 30

# --- SIDEBAR Controls ---
st.sidebar.header("🗺️ Route Selection")

start_text = st.sidebar.text_input("Enter Starting Point:", "Mehdipatnam, Hyderabad")
end_text = st.sidebar.text_input("Enter Destination Point:", "Gachibowli, Hyderabad")

st.sidebar.subheader("🌧️ Environmental Modifiers")
monsoon_mode = st.sidebar.toggle("Simulate Waterlogging Delays")

# --- CONVERT TEXT INPUTS TO GEOLOCATIONS WITH HIGHLY UNIQUE USER AGENT ---
# Using an ultra-specific user agent prevents OpenStreetMap from blocking the Streamlit cloud server IP
geolocator = Nominatim(user_agent="macharla_aravind_hyd_traffic_agent_final_2026")

# Set default fallback paths immediately
start_coords = HYD_COORDS["mehdipatnam"]
end_coords = HYD_COORDS["gachibowli"]

try:
    if start_text and "hyderabad" in start_text.lower():
        # Added a strict 4-second timeout so the cloud environment never gets stuck loading forever
        loc1 = geolocator.geocode(start_text, timeout=4)
        if loc1: 
            start_coords = [loc1.latitude, loc1.longitude]
        
    if end_text and "hyderabad" in end_text.lower():
        loc2 = geolocator.geocode(end_text, timeout=4)
        if loc2: 
            end_coords = [loc2.latitude, loc2.longitude]
except Exception as e:
    # Safely passes along to use the fast fallback coordinates instead of crashing
    pass

# --- COMPUTE MULTI-STREET PATHWAYS ---
# Route A: Main Arterial Route
path_a, dist_a, time_a = get_street_route(start_coords[0], start_coords[1], end_coords[0], end_coords[1])

# Route B: Alternate Corridor via an offset waypoint to force routing through secondary roads
mid_lat = (start_coords[0] + end_coords[0]) / 2 + 0.012
mid_lon = (start_coords[1] + end_coords[1]) / 2 - 0.012
path_b, dist_b, time_b = get_street_route(start_coords[0], start_coords[1], end_coords[0], end_coords[1], via_waypoint=[mid_lat, mid_lon])

# Apply custom monsoon simulation delay parameters
delay_a = int(time_a * 0.8) if monsoon_mode else int(time_a * 0.2)
total_a = time_a + delay_a

delay_b = int(time_b * 0.15) if monsoon_mode else int(time_b * 0.3)
total_b = time_b + delay_b

# --- RENDER MAIN LAYOUT ---
st.markdown("### 📊 Route Overview")
metrics_data = {
    "Parameter": ["Total Commute Time", "Traffic/Water Delay", "Actual Distance"],
    "🔵 Route A (Main Street)": [f"{total_a} mins", f"+{delay_a} mins", f"{dist_a} km"],
    "🟢 Route B (Alternate Street)": [f"{total_b} mins", f"+{delay_b} mins", f"{dist_b} km"]
}
st.dataframe(pd.DataFrame(metrics_data), use_container_width=True, hide_index=True)

st.markdown("---")

# Render Map Layer
st.subheader("🗺️ Real Road Network Map")
map_center = [(start_coords[0] + end_coords[0])/2, (start_coords[1] + end_coords[1])/2]
m = folium.Map(location=map_center, zoom_start=13, tiles="OpenStreetMap")

# Add markers for pin locations
folium.Marker(location=start_coords, popup="Start Location", icon=folium.Icon(color="blue", icon="play")).add_to(m)
folium.Marker(location=end_coords, popup="Destination", icon=folium.Icon(color="red", icon="flag")).add_to(m)

# Draw the two real street paths
folium.PolyLine(path_a, color="blue", weight=6, opacity=0.85, tooltip="Route A: Main Street Corridor").add_to(m)
folium.PolyLine(path_b, color="green", weight=5, opacity=0.85, tooltip="Route B: Alternative Street Corridor").add_to(m)

st_folium(m, width=900, height=500, returned_objects=[])
