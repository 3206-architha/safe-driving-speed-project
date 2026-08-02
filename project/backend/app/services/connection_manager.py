"""
Tracks active WebSocket connections. Kept simple (in-memory) — fine for
a single-instance deployment. If you later scale to multiple backend
instances behind a load balancer, replace this with a Redis pub/sub
backed manager so connections on different instances can still be
addressed (noted here so future-you doesn't get surprised).
"""
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)


manager = ConnectionManager()
