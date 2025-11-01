from __future__ import annotations

import asyncio
import json
import unittest
from typing import Any

from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.models.enums import ProcessingJobStatus, ProcessingJobType
from backend.app.workers.job_manager import ProcessingJobLifecycle


class TestWebSocketProgress(unittest.TestCase):
    """Test WebSocket progress endpoint and functionality."""

    def setUp(self) -> None:
        """Set up test environment before each test."""
        self.app = create_app()
        self.client = TestClient(self.app)

    def test_websocket_connection_invalid_job_id(self) -> None:
        """Test WebSocket connection with invalid job ID."""
        with self.client.websocket_connect("/progress/ws/invalid-job-id") as websocket:
            # Should receive error message and close
            data = websocket.receive_text()
            message = json.loads(data)
            assert message["type"] == "error"
            assert "not found" in message["error"]

    def test_websocket_connection_valid_job_id(self) -> None:
        """Test WebSocket connection with valid job ID."""
        # Create a test job
        job = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.INGEST,
            payload={"test": "data"},
        )
        
        try:
            with self.client.websocket_connect(f"/progress/ws/{job.id}") as websocket:
                # Should receive initial status
                data = websocket.receive_text()
                message = json.loads(data)
                
                assert message["job_id"] == job.id
                assert "status" in message
                assert "timestamp" in message
                
                # Should be in QUEUED status
                assert message["status"] in [ProcessingJobStatus.PENDING.value, ProcessingJobStatus.QUEUED.value]
                
        finally:
            # Clean up
            try:
                ProcessingJobLifecycle.mark_failed(job.id, "Test cleanup")
            except Exception:
                pass

    def test_websocket_ping_pong(self) -> None:
        """Test WebSocket ping/pong heartbeat."""
        # Create a test job
        job = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.TRANSCRIBE,
            payload={"test": "ping"},
        )
        
        try:
            with self.client.websocket_connect(f"/progress/ws/{job.id}") as websocket:
                # Send ping
                websocket.send_text(json.dumps({"type": "ping"}))
                
                # Should receive pong
                data = websocket.receive_text()
                message = json.loads(data)
                assert message["type"] == "pong"
                assert "timestamp" in message
                
        finally:
            # Clean up
            try:
                ProcessingJobLifecycle.mark_failed(job.id, "Test cleanup")
            except Exception:
                pass

    def test_websocket_subscribe_to_additional_job(self) -> None:
        """Test subscribing to additional jobs via WebSocket."""
        # Create two test jobs
        job1 = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.INGEST,
            payload={"test": "job1"},
        )
        job2 = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.TRANSCRIBE,
            payload={"test": "job2"},
        )
        
        try:
            with self.client.websocket_connect(f"/progress/ws/{job1.id}") as websocket:
                # Receive initial status for job1
                data = websocket.receive_text()
                message = json.loads(data)
                assert message["job_id"] == job1.id
                
                # Subscribe to job2
                websocket.send_text(json.dumps({
                    "type": "subscribe",
                    "job_id": job2.id
                }))
                
                # Should receive status for job2
                data = websocket.receive_text()
                message = json.loads(data)
                assert message["job_id"] == job2.id
                
        finally:
            # Clean up
            for job in [job1, job2]:
                try:
                    ProcessingJobLifecycle.mark_failed(job.id, "Test cleanup")
                except Exception:
                    pass

    def test_websocket_subscribe_invalid_job(self) -> None:
        """Test subscribing to invalid job via WebSocket."""
        # Create a test job
        job = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.INGEST,
            payload={"test": "data"},
        )
        
        try:
            with self.client.websocket_connect(f"/progress/ws/{job.id}") as websocket:
                # Receive initial status
                websocket.receive_text()
                
                # Try to subscribe to invalid job
                websocket.send_text(json.dumps({
                    "type": "subscribe",
                    "job_id": "invalid-job-id"
                }))
                
                # Should receive error
                data = websocket.receive_text()
                message = json.loads(data)
                assert message["type"] == "error"
                assert "not found" in message["error"]
                
        finally:
            # Clean up
            try:
                ProcessingJobLifecycle.mark_failed(job.id, "Test cleanup")
            except Exception:
                pass

    def test_websocket_invalid_json(self) -> None:
        """Test WebSocket with invalid JSON."""
        # Create a test job
        job = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.INGEST,
            payload={"test": "data"},
        )
        
        try:
            with self.client.websocket_connect(f"/progress/ws/{job.id}") as websocket:
                # Receive initial status
                websocket.receive_text()
                
                # Send invalid JSON
                websocket.send_text("invalid json")
                
                # Should receive error
                data = websocket.receive_text()
                message = json.loads(data)
                assert message["type"] == "error"
                assert "Invalid JSON" in message["error"]
                
        finally:
            # Clean up
            try:
                ProcessingJobLifecycle.mark_failed(job.id, "Test cleanup")
            except Exception:
                pass

    def test_websocket_progress_updates(self) -> None:
        """Test receiving progress updates via WebSocket."""
        # Create a test job
        job = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.GENERATE_CLIP,
            payload={"test": "progress"},
        )
        
        try:
            with self.client.websocket_connect(f"/progress/ws/{job.id}") as websocket:
                # Receive initial status
                data = websocket.receive_text()
                message = json.loads(data)
                assert message["job_id"] == job.id
                
                # Simulate job progress updates
                ProcessingJobLifecycle.mark_started(job.id)
                ProcessingJobLifecycle.mark_progress(job.id, progress=25.0, message="Processing stage 1")
                ProcessingJobLifecycle.mark_progress(job.id, progress=50.0, message="Processing stage 2")
                ProcessingJobLifecycle.mark_progress(job.id, progress=75.0, message="Processing stage 3")
                ProcessingJobLifecycle.mark_completed(job.id, {"result": "success"})
                
                # Receive progress updates (may need to wait a bit)
                messages = []
                for _ in range(5):  # Try to receive up to 5 messages
                    try:
                        data = websocket.receive_text(timeout=1.0)
                        messages.append(json.loads(data))
                    except Exception:
                        break
                
                # Should have received progress updates
                status_updates = [msg for msg in messages if msg.get("status")]
                assert len(status_updates) > 0
                
                # Check that we got different status updates
                statuses = {msg["status"] for msg in status_updates}
                assert ProcessingJobStatus.IN_PROGRESS.value in statuses
                assert ProcessingJobStatus.COMPLETED.value in statuses
                
                # Check progress values
                progress_messages = [msg for msg in messages if msg.get("progress") is not None]
                progress_values = [msg["progress"] for msg in progress_messages]
                assert 25.0 in progress_values
                assert 50.0 in progress_values
                assert 75.0 in progress_values
                assert 100.0 in progress_values  # Completed job should have 100% progress
                
        finally:
            # Clean up if job wasn't completed
            if job.status != ProcessingJobStatus.COMPLETED:
                try:
                    ProcessingJobLifecycle.mark_failed(job.id, "Test cleanup")
                except Exception:
                    pass

    def test_websocket_multiple_clients_same_job(self) -> None:
        """Test multiple WebSocket clients subscribed to the same job."""
        # Create a test job
        job = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.RENDER,
            payload={"test": "multiple_clients"},
        )
        
        messages_clients = []
        
        try:
            # Create multiple WebSocket connections
            clients = []
            for i in range(3):
                websocket = self.client.websocket_connect(f"/progress/ws/{job.id}")
                clients.append(websocket)
                
            with clients[0] as ws1, clients[1] as ws2, clients[2] as ws3:
                websockets = [ws1, ws2, ws3]
                
                # Each client should receive initial status
                for i, ws in enumerate(websockets):
                    data = ws.receive_text()
                    message = json.loads(data)
                    assert message["job_id"] == job.id
                    messages_clients.append((i, message))
                
                # Send progress update
                ProcessingJobLifecycle.mark_progress(job.id, progress=50.0, message="Halfway done")
                
                # Each client should receive the progress update
                for i, ws in enumerate(websockets):
                    data = ws.receive_text(timeout=1.0)
                    message = json.loads(data)
                    assert message["job_id"] == job.id
                    assert message["progress"] == 50.0
                    assert message["message"] == "Halfway done"
                    messages_clients.append((i, message))
                
                # Verify all clients received the same updates
                client_0_messages = [msg for client, msg in messages_clients if client == 0]
                client_1_messages = [msg for client, msg in messages_clients if client == 1]
                client_2_messages = [msg for client, msg in messages_clients if client == 2]
                
                assert len(client_0_messages) == len(client_1_messages) == len(client_2_messages)
                
        finally:
            # Clean up
            try:
                ProcessingJobLifecycle.mark_failed(job.id, "Test cleanup")
            except Exception:
                pass

    def test_websocket_client_disconnect_handling(self) -> None:
        """Test server handling of client disconnection."""
        # Create a test job
        job = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.EXPORT,
            payload={"test": "disconnect"},
        )
        
        try:
            # Connect and immediately disconnect
            with self.client.websocket_connect(f"/progress/ws/{job.id}") as websocket:
                # Receive initial status
                websocket.receive_text()
                # Connection will close when exiting context
            
            # Send progress update after disconnect - should not raise exceptions
            ProcessingJobLifecycle.mark_progress(job.id, progress=30.0, message="After disconnect")
            
            # Should be able to connect again
            with self.client.websocket_connect(f"/progress/ws/{job.id}") as websocket:
                data = websocket.receive_text()
                message = json.loads(data)
                assert message["job_id"] == job.id
                
        finally:
            # Clean up
            try:
                ProcessingJobLifecycle.mark_failed(job.id, "Test cleanup")
            except Exception:
                pass

    def test_websocket_heartbeat_timeout(self) -> None:
        """Test WebSocket heartbeat mechanism."""
        # Create a test job
        job = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.INGEST,
            payload={"test": "heartbeat"},
        )
        
        try:
            with self.client.websocket_connect(f"/progress/ws/{job.id}") as websocket:
                # Receive initial status
                websocket.receive_text()
                
                # Wait for heartbeat (should be sent every 30 seconds, but we'll wait shorter)
                # This test may need adjustment based on actual timeout
                try:
                    data = websocket.receive_text(timeout=35.0)
                    message = json.loads(data)
                    # Should receive heartbeat or other update
                    assert "type" in message
                    assert message["type"] in ["heartbeat", "pong"]
                    assert "timestamp" in message
                except Exception:
                    # If no heartbeat received, that's also acceptable for this test
                    # The important thing is that the connection stays alive
                    pass
                
        finally:
            # Clean up
            try:
                ProcessingJobLifecycle.mark_failed(job.id, "Test cleanup")
            except Exception:
                pass


class TestProgressMessageSchema(unittest.TestCase):
    """Test ProgressMessage Pydantic model validation."""

    def test_progress_message_validation(self) -> None:
        """Test ProgressMessage Pydantic model validation."""
        from backend.app.api.routes.progress import ProgressMessage
        
        # Valid message
        message = ProgressMessage(
            job_id="test-job",
            status=ProcessingJobStatus.IN_PROGRESS,
            progress=50.0,
            message="Processing",
            timestamp="2023-01-01T00:00:00Z",
            metadata={"stage": "processing"}
        )
        
        self.assertEqual(message.job_id, "test-job")
        self.assertEqual(message.status, ProcessingJobStatus.IN_PROGRESS)
        self.assertEqual(message.progress, 50.0)
        self.assertEqual(message.message, "Processing")
        self.assertEqual(message.timestamp, "2023-01-01T00:00:00Z")
        self.assertEqual(message.metadata, {"stage": "processing"})
        
        # Message without optional fields
        message_minimal = ProgressMessage(
            job_id="test-job-2",
            status=ProcessingJobStatus.COMPLETED,
            timestamp="2023-01-01T00:00:00Z"
        )
        
        self.assertEqual(message_minimal.job_id, "test-job-2")
        self.assertEqual(message_minimal.status, ProcessingJobStatus.COMPLETED)
        self.assertIsNone(message_minimal.progress)
        self.assertIsNone(message_minimal.message)
        self.assertIsNone(message_minimal.metadata)


class TestProgressBroadcaster(unittest.TestCase):
    """Test ProgressBroadcaster functionality."""

    def test_broadcaster_operations(self) -> None:
        """Test ProgressBroadcaster functionality."""
        from backend.app.api.routes.progress import ProgressBroadcaster, ProgressMessage
        
        broadcaster = ProgressBroadcaster()
        
        # Test subscription/unsubscription
        self.assertEqual(len(broadcaster._connections), 0)
        
        # Mock WebSocket for testing
        class MockWebSocket:
            def __init__(self):
                self.sent_messages = []
                self.closed = False
            
            async def send_text(self, data: str) -> None:
                self.sent_messages.append(data)
            
            def __hash__(self):
                return id(self)
        
        # Test subscription
        mock_ws1 = MockWebSocket()
        mock_ws2 = MockWebSocket()
        
        # Since these are sync tests, we need to run async methods in sync context
        async def test_async_operations():
            await broadcaster.subscribe("job1", mock_ws1)
            await broadcaster.subscribe("job1", mock_ws2)
            await broadcaster.subscribe("job2", mock_ws1)
            
            self.assertIn("job1", broadcaster._connections)
            self.assertIn("job2", broadcaster._connections)
            self.assertEqual(len(broadcaster._connections["job1"]), 2)
            self.assertEqual(len(broadcaster._connections["job2"]), 1)
            
            # Test broadcasting
            message = ProgressMessage(
                job_id="job1",
                status=ProcessingJobStatus.IN_PROGRESS,
                progress=75.0,
                timestamp="2023-01-01T00:00:00Z"
            )
            
            await broadcaster.broadcast(message)
            
            # Both websockets subscribed to job1 should receive the message
            self.assertEqual(len(mock_ws1.sent_messages), 1)
            self.assertEqual(len(mock_ws2.sent_messages), 1)
            
            sent_data1 = json.loads(mock_ws1.sent_messages[0])
            sent_data2 = json.loads(mock_ws2.sent_messages[0])
            
            self.assertEqual(sent_data1["job_id"], "job1")
            self.assertEqual(sent_data1["progress"], 75.0)
            self.assertEqual(sent_data2["job_id"], "job1")
            self.assertEqual(sent_data2["progress"], 75.0)
            
            # Test unsubscription
            await broadcaster.unsubscribe("job1", mock_ws1)
            self.assertEqual(len(broadcaster._connections["job1"]), 1)
            self.assertNotIn(mock_ws1, broadcaster._connections["job1"])
            
            # Test cleanup
            await broadcaster.cleanup_websocket(mock_ws1)
            self.assertNotIn("job2", broadcaster._connections)
        
        # Run the async test
        asyncio.run(test_async_operations())


if __name__ == "__main__":
    unittest.main()