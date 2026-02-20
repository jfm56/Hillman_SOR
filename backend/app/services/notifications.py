from fastapi import WebSocket
from typing import Dict, List, Optional
import json
import asyncio
from datetime import datetime


class ConnectionManager:
    """Manages WebSocket connections for real-time notifications."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        """Remove a disconnected user."""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal(self, user_id: str, message: dict):
        """Send a message to a specific user."""
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception:
                self.disconnect(user_id)
    
    async def broadcast(self, message: dict, exclude_user: Optional[str] = None):
        """Broadcast a message to all connected users."""
        disconnected = []
        for user_id, connection in self.active_connections.items():
            if user_id != exclude_user:
                try:
                    await connection.send_json(message)
                except Exception:
                    disconnected.append(user_id)
        
        for user_id in disconnected:
            self.disconnect(user_id)
    
    @property
    def connected_count(self) -> int:
        return len(self.active_connections)


# Global connection manager
manager = ConnectionManager()


async def notify_project_created(project_id: str, project_name: str, created_by_name: str, exclude_user_id: Optional[str] = None):
    """Notify all users about a new project."""
    await manager.broadcast({
        "type": "project_created",
        "data": {
            "project_id": project_id,
            "project_name": project_name,
            "created_by": created_by_name,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }, exclude_user=exclude_user_id)


async def notify_report_created(report_id: str, report_title: str, project_name: str, created_by_name: str, exclude_user_id: Optional[str] = None):
    """Notify all users about a new report."""
    await manager.broadcast({
        "type": "report_created",
        "data": {
            "report_id": report_id,
            "report_title": report_title,
            "project_name": project_name,
            "created_by": created_by_name,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }, exclude_user=exclude_user_id)


async def notify_report_status_changed(report_id: str, report_title: str, new_status: str, changed_by_name: str, exclude_user_id: Optional[str] = None):
    """Notify all users about a report status change."""
    await manager.broadcast({
        "type": "report_status_changed",
        "data": {
            "report_id": report_id,
            "report_title": report_title,
            "new_status": new_status,
            "changed_by": changed_by_name,
            "timestamp": datetime.utcnow().isoformat(),
        }
    }, exclude_user=exclude_user_id)
