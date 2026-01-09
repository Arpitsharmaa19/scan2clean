import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model

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
            # Citizen will join multiple groups if they have multiple assigned reports
            # For simplicity, we can have a general group or let them join specific ones via a message
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

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if self.role == 'worker' and 'lat' in data and 'lng' in data:
            lat = data['lat']
            lng = data['lng']
            
            # Update worker location in DB
            await self.update_worker_location(self.user.id, lat, lng)
            
            # Broadcast to anyone listening to this worker (citizens or admins)
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
        
        elif self.role == 'citizen' and data.get('action') == 'track_worker':
            worker_id = data.get('worker_id')
            if worker_id:
                # Add citizen to the worker's group
                await self.channel_layer.group_add(
                    f"worker_{worker_id}",
                    self.channel_name
                )

    # Receive message from group
    async def location_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'worker_id': event['worker_id'],
            'worker_name': event['worker_name'],
            'lat': event['lat'],
            'lng': event['lng']
        }))

    @database_sync_to_async
    def update_worker_location(self, user_id, lat, lng):
        User.objects.filter(id=user_id).update(
            latitude=lat,
            longitude=lng,
            last_location_update=timezone.now()
        )
