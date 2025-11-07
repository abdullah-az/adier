#!/usr/bin/env python3
"""
Simple integration test to verify WebSocket progress endpoint registration.

This script checks that:
1. The progress router is properly imported
2. The WebSocket endpoint is registered
3. The Pydantic models are correctly defined

Usage:
    python test_integration.py
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test that all required modules can be imported."""
    try:
        from app.api.routes.progress import (
            ProgressMessage,
            ProgressSubscription,
            ProgressBroadcaster,
            publish_job_progress,
            router
        )
        print("✅ All progress route imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_pydantic_models():
    """Test Pydantic model validation."""
    try:
        from app.api.routes.progress import ProgressMessage
        from app.models.enums import ProcessingJobStatus
        
        # Test valid message creation
        message = ProgressMessage(
            job_id="test-job-123",
            status=ProcessingJobStatus.IN_PROGRESS,
            progress=75.5,
            message="Processing stage 2",
            timestamp="2023-01-01T00:00:00Z",
            metadata={"stage": "processing", "files_processed": 10}
        )
        
        # Validate the message
        message_dict = message.model_dump()
        
        assert message_dict["job_id"] == "test-job-123"
        assert message_dict["status"] == "in_progress"
        assert message_dict["progress"] == 75.5
        assert message_dict["message"] == "Processing stage 2"
        assert message_dict["timestamp"] == "2023-01-01T00:00:00Z"
        assert message_dict["metadata"]["stage"] == "processing"
        
        print("✅ ProgressMessage Pydantic model validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Pydantic model validation error: {e}")
        return False

def test_broadcaster():
    """Test ProgressBroadcaster functionality."""
    try:
        from app.api.routes.progress import ProgressBroadcaster, ProgressMessage
        from app.models.enums import ProcessingJobStatus
        
        # Create broadcaster
        broadcaster = ProgressBroadcaster()
        
        # Test initial state
        assert len(broadcaster._connections) == 0
        assert broadcaster._lock is not None
        
        print("✅ ProgressBroadcaster initialization successful")
        return True
        
    except Exception as e:
        print(f"❌ ProgressBroadcaster error: {e}")
        return False

def test_router_registration():
    """Test that the WebSocket router is properly configured."""
    try:
        from app.api.routes.progress import router
        
        # Check router properties
        assert router.prefix == "/progress"
        assert "progress" in router.tags
        
        # Check that WebSocket route is registered
        routes = [route for route in router.routes if hasattr(route, 'path')]
        websocket_routes = [route for route in routes if '/ws/' in route.path]
        
        assert len(websocket_routes) > 0, "No WebSocket routes found"
        
        print("✅ WebSocket router registration successful")
        return True
        
    except Exception as e:
        print(f"❌ Router registration error: {e}")
        return False

def test_job_lifecycle_integration():
    """Test that job lifecycle integration is properly set up."""
    try:
        # Check that the job_manager imports work
        from app.workers.job_manager import ProcessingJobLifecycle, _publish_progress_update
        
        # Verify the function exists
        assert callable(_publish_progress_update)
        
        print("✅ Job lifecycle integration setup successful")
        return True
        
    except Exception as e:
        print(f"❌ Job lifecycle integration error: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🧪 Running WebSocket Progress Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Pydantic Model Tests", test_pydantic_models),
        ("ProgressBroadcaster Tests", test_broadcaster),
        ("Router Registration Tests", test_router_registration),
        ("Job Lifecycle Integration Tests", test_job_lifecycle_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}:")
        print("-" * 40)
        
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} failed")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    exit(main())