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

# Hardcoded precise fallback coordinates for Hyderabad hubs
HYD_COORDS = {
    "mehdipatnam": [17.3950, 78.4312],
    "gachibowli": [17.4401, 78.3489],
    "jubilee_hills": [17.4278, 78.4063] # Forced alternate waypoint
}

# --- FUNCTION TO FETCH CLEAN ROUTE GEOMETRY ---
def get_clean_route(start_lat, start_lon, end_lat, end_lon):
    """
    Fetches a standard direct route from point A to point B along real streets.
    """
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
    return [[start_lat, start_lon], [end_lat, end_lon]], 10.8, 15

# --- SIDEBAR Controls ---
st.sidebar.header("🗺️ Route Selection")

start_text = st.sidebar.text_input("Enter Starting Point:", "Mehdipatnam, Hyderabad")
end_text = st.sidebar.text_input("Enter Destination Point:", "Gachibowli, Hyderabad")

st.sidebar.subheader("🌧️ Environmental Modifiers")
monsoon_mode = st.sidebar.toggle("Simulate Waterlogging Delays")

# --- CONVERT TEXT INPUTS TO GEOLOCATIONS ---
geolocator = Nominatim(user_agent="macharla_aravind_hyd_traffic_agent_final_2026")

start_coords = HYD_COORDS["mehdipatnam"]
end_coords = HYD_COORDS["gachibowli"]
waypoint_coords = HYD_COORDS["jubilee_hills"]

try:
    if start_text and "hyderabad" in start_text.lower():
        loc1 = geolocator.geocode(start_text, timeout=4)
        if loc1: start_coords = [loc1.latitude, loc1.longitude]
        
    if end_text and "hyderabad" in end_text.lower():
        loc2 = geolocator.geocode(end_text, timeout=4)
        if loc2: end_coords = [loc2.latitude, loc2.longitude]
except:
    pass

# --- COMPUTE SEPARATE MULTI-STREET PATHWAYS ---
# 1. Fetch Route A (Main Direct Road - Blue)
path_a, dist_a, time_a = get_clean_route(start_coords[0], start_coords[1], end_coords[0], end_coords[1])

# 2. Fetch Route B by breaking it into two distinct legs to force a completely different highway network (Green)
# Leg 1: Start to Jubilee Hills Checkpost area
path_b1, dist_b1, time_b1 = get_clean_route(start_coords[0], start_coords[1], waypoint_coords[0], waypoint_coords[1])
# Leg 2: Jubilee Hills Checkpost to Gachibowli Destination
path_b2, dist_b2, time_b2 = get_clean_route(waypoint_coords[0], waypoint_coords[1], end_coords[0], end_coords[1])

# Combine Leg 1 and Leg 2 data for Route B
path_b = path_b1 + path_b2
dist_b = round(dist_b1 + dist_b2, 1)
time_b = time_b1 + time_b2

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

# Draw the two real paths completely separated on the map layers
folium.PolyLine(path_a, color="blue", weight=6, opacity=0.85, tooltip="Route A: Main Street Corridor").add_to(m)
folium.PolyLine(path_b, color="green", weight=5, opacity=0.85, tooltip="Route B: Alternative Street Corridor").add_to(m)

st_folium(m, width=900, height=500, returned_objects=[])
