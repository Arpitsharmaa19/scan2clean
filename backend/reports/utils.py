import math
import os
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from notifications.models import Notification
from django.conf import settings
import json
import urllib.request

def send_realtime_notification(user, title, message, level='info'):
    # 1. Save to database
    Notification.objects.create(
        user=user,
        title=title,
        message=message
    )

    # 2. Send to WebSocket
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user.id}",
        {
            "type": "send_notification",
            "title": title,
            "message": message,
            "level": level
        }
    )

def get_optimized_route(worker_lat, worker_lng, report_locations):
    """
    report_locations: list of {'id': id, 'lat': lat, 'lng': lng}
    Returns optimized list of reports using OSRM (Free Open Source Routing Machine).
    """
    # OSRM expects Longitude, Latitude
    coords = [f"{worker_lng},{worker_lat}"]
    coords += [f"{r['lng']},{r['lat']}" for r in report_locations]
    
    coords_str = ";".join(coords)
    # Using OSRM Trip API which solves the TSP
    url = f"https://router.project-osrm.org/trip/v1/driving/{coords_str}?source=first&roundtrip=false"

    try:
        # Set a timeout for the request
        req = urllib.request.Request(url, headers={'User-Agent': 'Scan2Clean/1.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            
        if data.get('code') != 'Ok':
            return sort_by_distance(worker_lat, worker_lng, report_locations)

        # OSRM returns waypoints in the order they are visited in the 'waypoints' array
        waypoints = data.get('waypoints', [])
        
        optimized_reports = []
        for wp in waypoints:
            original_input_index = wp['waypoint_index']
            # original_input_index 0 is the worker's start position
            if original_input_index == 0:
                continue
            
            # report_locations[original_input_index - 1] is the corresponding report
            optimized_reports.append(report_locations[original_input_index - 1])
            
        return optimized_reports
        
    except Exception as e:
        print(f"OSRM Routing Error: {e}")
        return sort_by_distance(worker_lat, worker_lng, report_locations)

def sort_by_distance(lat, lng, locations):
    """Simple Nearest Neighbor algorithm"""
    unvisited = list(locations)
    current_lat, current_lng = lat, lng
    sorted_locs = []
    
    while unvisited:
        nearest = min(unvisited, key=lambda loc: calculate_dist(current_lat, current_lng, float(loc['lat']), float(loc['lng'])))
        sorted_locs.append(nearest)
        unvisited.remove(nearest)
        current_lat, current_lng = float(nearest['lat']), float(nearest['lng'])
        
    return sorted_locs

def calculate_dist(lat1, lon1, lat2, lon2):
    R = 6371 # km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2) * math.sin(dLat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dLon/2) * math.sin(dLon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def batch_reports_by_proximity(reports, threshold_km=0.2):
    """Group reports that are within threshold_km of each other"""
    batches = []
    visited = set()
    
    for i, r1 in enumerate(reports):
        if r1['id'] in visited: continue
        
        current_batch = [r1]
        visited.add(r1['id'])
        
        for j, r2 in enumerate(reports):
            if r2['id'] in visited: continue
            
            dist = calculate_dist(float(r1['lat']), float(r1['lng']), float(r2['lat']), float(r2['lng']))
            if dist <= threshold_km:
                current_batch.append(r2)
                visited.add(r2['id'])
        
        batches.append({
            'main_report': r1,
            'others': current_batch[1:],
            'count': len(current_batch)
        })
    return batches
