import json
import math
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import F
from reports.models import WasteReport

User = get_user_model()

class LocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.role = self.scope['url_route']['kwargs']['role']
        
        # Room group name
        if self.role == 'worker':
            self.room_group_name = f"worker_{self.user.id}"
        else:
            self.room_group_name = f"citizen_{self.user.id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if self.role == 'worker' and 'lat' in data and 'lng' in data:
            lat = data['lat']
            lng = data['lng']
            
            await self.update_worker_location(self.user.id, lat, lng)
            
            # Broadcast location update to anyone tracking this worker
            await self.channel_layer.group_send(
                f"worker_{self.user.id}",
                {
                    'type': 'location_update',
                    'worker_id': self.user.id,
                    'worker_name': self.user.username,
                    'lat': lat,
                    'lng': lng
                }
            )

            # Check for proximity to assigned reports
            await self.check_proximity(lat, lng)
        
        elif self.role == 'citizen' and data.get('action') == 'track_worker':
            worker_id = data.get('worker_id')
            if worker_id:
                await self.channel_layer.group_add(
                    f"worker_{worker_id}",
                    self.channel_name
                )

    async def location_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'worker_id': event['worker_id'],
            'worker_name': event['worker_name'],
            'lat': event['lat'],
            'lng': event['lng']
        }))

    async def check_proximity(self, worker_lat, worker_lng):
        reports = await self.get_assigned_reports()
        for report in reports:
            if report['lat'] and report['lng']:
                dist = self.calculate_distance(worker_lat, worker_lng, float(report['lat']), float(report['lng']))
                if dist < 0.1: # 100 meters
                    # Send real-time notification to the specific citizen
                    await self.channel_layer.group_send(
                        f"user_{report['citizen_id']}",
                        {
                            "type": "send_notification",
                            "title": "Worker Arriving! 🚛",
                            "message": f"Your assigned worker {self.user.username} is arriving at the location for Waste Report #{report['id']}.",
                            "level": "info"
                        }
                    )

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        R = 6371 # Earth radius in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @database_sync_to_async
    def get_assigned_reports(self):
        return list(WasteReport.objects.filter(
            assigned_worker=self.user,
            status='assigned'
        ).values('id', 'citizen_id', 'latitude', 'longitude').annotate(lat=F('latitude'), lng=F('longitude')))

    @database_sync_to_async
    def update_worker_location(self, user_id, lat, lng):
        User.objects.filter(id=user_id).update(
            latitude=lat,
            longitude=lng,
            last_location_update=timezone.now()
        )

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return

        self.user_group = f"user_{self.user.id}"
        
        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )

    async def send_notification(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'title': event.get('title', 'New Notification'),
            'message': event['message'],
            'level': event.get('level', 'info')
        }))
