import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import pandas as pd
import requests

# 1. Set up layout configurationsimport streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim
import pandas as pd
import requests

# Set layout configurations
st.set_page_config(page_title="Hyderabad AI Traffic Agent", layout="wide")

st.title("🚗 Hyderabad AI Traffic Agent")
st.markdown("Compare main streets vs. alternative street corridors with real-world road geometries.")

# Global fallback coordinates for Hyderabad hubs
HYD_COORDS = {
    "mehdipatnam": [17.3950, 78.4312],
    "gachibowli": [17.4401, 78.3489]
}

# --- FUNCTION TO FETCH REAL ROAD NETWORK GEOMETRY ---
def get_street_route(start_lat, start_lon, end_lat, end_lon, via_waypoint=None):
    """
    Fetches real street networks using OSRM. 
    If a via_waypoint is provided, it forces the route through an alternative street corridor.
    """
    if via_waypoint:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{via_waypoint[1]},{via_waypoint[0]};{end_lon},{end_lat}?overview=full&geometries=geojson"
    else:
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
        
    try:
        response = requests.get(url).json()
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

# --- SIDEBAR Controls (Always Unlocked) ---
st.sidebar.header("🗺️ Route Selection")

# Text inputs are wide open by default
start_text = st.sidebar.text_input("Enter Starting Point:", "Mehdipatnam, Hyderabad")
end_text = st.sidebar.text_input("Enter Destination Point:", "Gachibowli, Hyderabad")

st.sidebar.subheader("🌧️ Environmental Modifiers")
monsoon_mode = st.sidebar.toggle("Simulate Waterlogging Delays")

# --- CONVERT TEXT INPUTS TO GEOLOCATIONS ---
geolocator = Nominatim(user_agent="hyd_traffic_agent_v2")

# Set defaults
start_coords = HYD_COORDS["mehdipatnam"]
end_coords = HYD_COORDS["gachibowli"]

try:
    if start_text and "hyderabad" in start_text.lower():
        loc1 = geolocator.geocode(start_text)
        if loc1: start_coords = [loc1.latitude, loc1.longitude]
        
    if end_text and "hyderabad" in end_text.lower():
        loc2 = geolocator.geocode(end_text)
        if loc2: end_coords = [loc2.latitude, loc2.longitude]
except:
    st.sidebar.warning("Using fallback system coordinates for calculations.")

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
st.set_page_config(page_title="Hyderabad Live Traffic Route Compare", layout="wide")

st.title("🚗 Hyderabad AI Traffic Agent - Real Street Routing Engine")
st.markdown("This application tracks actual street networks and roads across Hyderabad using the OpenSource Routing Machine (OSRM).")

# 2. Hardcoded fallback coordinates for prominent Hyderabad hubs
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

# 3. Helper Function to fetch street-by-street path geometries
def get_route_geometry(start_lat, start_lon, end_lat, end_lon, alternative=False):
    """
    Fetches real street network paths from OSRM free routing API.
    """
    # OSRM expects coordinates in lon,lat format
    url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"
    if alternative:
        url += "&alternative=true"
        
    try:
        response = requests.get(url).json()
        if response['code'] == 'Ok':
            # Extract routing calculations and street nodes
            route = response['routes'][0]
            geometry = route['geometry']['coordinates']
            # Convert back to lat,lon order for Folium plotting
            path_coords = [[point[1], point[0]] for point in geometry]
            distance_km = round(route['distance'] / 1000, 1)
            duration_mins = int(route['duration'] / 60)
            return path_coords, distance_km, duration_mins
    except Exception as e:
        pass
    
    # Simple direct line fallback if network error occurs
    return [[start_lat, start_lon], [end_lat, end_lon]], 10.0, 25

# 4. Sidebar Controls for user inputs
st.sidebar.header("🗺️ Route Selection")
use_presets = st.sidebar.checkbox("Use Hyderabad Hub Presets", value=True)

if use_presets:
    start_point = st.sidebar.selectbox("Select Start Point:", list(HYD_HUBS.keys()), index=2) # Default Mehdipatnam
    end_point = st.sidebar.selectbox("Select Destination Point:", list(HYD_HUBS.keys()), index=0) # Default Gachibowli
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

# 5. Execute OSRM Routing Engine requests
path_a, route_a_dist, route_a_base_time = get_route_geometry(start_coords[0], start_coords[1], end_coords[0], end_coords[1])
path_b, route_b_dist, route_b_base_time = get_route_geometry(start_coords[0], start_coords[1], end_coords[0], end_coords[1], alternative=True)

# 6. Apply realistic traffic weights based on monsoon status
route_a_delay = int(route_a_base_time * 0.7) if monsoon_mode else int(route_a_base_time * 0.2)
route_a_total = route_a_base_time + route_a_delay

route_b_delay = int(route_b_base_time * 0.2) if monsoon_mode else int(route_b_base_time * 0.3)
route_b_total = route_b_base_time + route_b_delay

# 7. Render Top Panel Metrics Row
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

# 8. Split Grid Layout: Data Performance Metrics vs. Live Vector Map Engine
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
    st.subheader("🗺️ Real Road Network Map")
    map_center = [(start_coords[0] + end_coords[0])/2, (start_coords[1] + end_coords[1])/2]
    m = folium.Map(location=map_center, zoom_start=13, tiles="OpenStreetMap")
    
    # Place markers for route pins
    folium.Marker(location=start_coords, popup=f"Start: {start_point}", icon=folium.Icon(color="blue", icon="play")).add_to(m)
    folium.Marker(location=end_coords, popup=f"End: {end_point}", icon=folium.Icon(color="red", icon="flag")).add_to(m)
    
    # Map out overlapping layout paths on actual open street coordinates
    folium.PolyLine(path_a, color="blue", weight=5, opacity=0.8, tooltip="Route A (Main Street)").add_to(m)
    folium.PolyLine(path_b, color="green", weight=4, opacity=0.8, tooltip="Route B (Alternative Street)").add_to(m)
    
    # Render map back cleanly to dashboard grid
    st_folium(m, width=700, height=450, returned_objects=[])
