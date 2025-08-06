# core/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Nos unimos a un grupo de canal llamado "dashboard"
        await self.channel_layer.group_add(
            "dashboard",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Salimos del grupo del canal
        await self.channel_layer.group_discard(
            "dashboard",
            self.channel_name
        )

    # Este método se llama cuando el grupo "dashboard" recibe un mensaje
    async def dashboard_update(self, event):
        # Enviamos el mensaje (que contiene los nuevos datos) al cliente WebSocket
        print("Enviando datos al WebSocket:", event["data"])
        await self.send(text_data=json.dumps(event["data"]))