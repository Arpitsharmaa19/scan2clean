import math
import os
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from notifications.models import Notification
from django.conf import settings
import googlemaps

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
    Returns optimized list of reports using Google Maps Directions API.
    """
    gmaps_key = os.getenv('GOOGLE_MAPS_API_KEY')
    if not gmaps_key:
        # Fallback: Simple distance-based sorting (Nearest Neighbor)
        return sort_by_distance(worker_lat, worker_lng, report_locations)

    gmaps = googlemaps.Client(key=gmaps_key)
    
    # Format origin and waypoints
    origin = (worker_lat, worker_lng)
    destinations = [(r['lat'], r['lng']) for r in report_locations]
    
    # Since worker needs to return or stop at the last point, 
    # we take the first point as origin and others as waypoints
    # For simplicity, we'll just use waypoints optimization
    
    try:
        # Directions API supports up to 25 waypoints
        result = gmaps.directions(
            origin=origin,
            destination=destinations[-1],
            waypoints=destinations[:-1],
            optimize_waypoints=True
        )
        
        if not result:
            return sort_by_distance(worker_lat, worker_lng, report_locations)
            
        waypoint_order = result[0]['waypoint_order']
        # waypoint_order gives the indices of waypoints list (destinations[:-1])
        optimized = []
        # Add the optimized waypoints
        for idx in waypoint_order:
            optimized.append(report_locations[idx])
        # Add the final destination (destinations[-1])
        optimized.append(report_locations[-1])
        
        return optimized
    except Exception as e:
        print(f"Routing Error: {e}")
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
