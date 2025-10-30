#!/usr/bin/env python3
"""
Demo script to test WebSocket progress functionality.

This script demonstrates the end-to-end progress WebSocket functionality by:
1. Creating a processing job
2. Connecting to the WebSocket progress endpoint
3. Simulating job progress updates
4. Displaying real-time progress messages

Usage:
    python demo_progress_ws.py
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone

import websockets

from backend.app.models.enums import ProcessingJobType
from backend.app.workers.job_manager import ProcessingJobLifecycle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def websocket_client(job_id: str):
    """WebSocket client that receives progress updates."""
    uri = f"ws://localhost:8000/progress/ws/{job_id}"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info(f"Connected to WebSocket for job {job_id}")
            
            # Send ping to test heartbeat
            await websocket.send(json.dumps({"type": "ping"}))
            
            # Listen for messages
            async for message in websocket:
                data = json.loads(message)
                
                if data.get("type") == "pong":
                    logger.info("🏓 Received pong response")
                elif data.get("type") == "heartbeat":
                    logger.info("💓 Received heartbeat")
                elif data.get("type") == "error":
                    logger.error(f"❌ Error: {data.get('error')}")
                else:
                    # Progress update
                    status = data.get("status", "unknown")
                    progress = data.get("progress")
                    msg = data.get("message", "")
                    timestamp = data.get("timestamp", "")
                    
                    logger.info(f"📊 Progress Update:")
                    logger.info(f"   Status: {status}")
                    if progress is not None:
                        logger.info(f"   Progress: {progress:.1f}%")
                    if msg:
                        logger.info(f"   Message: {msg}")
                    logger.info(f"   Time: {timestamp}")
                    logger.info("-" * 50)
                    
    except websockets.exceptions.ConnectionClosed:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


async def simulate_job_progress(job_id: str):
    """Simulate job progress by calling the job lifecycle methods."""
    logger.info(f"🚀 Starting job simulation for {job_id}")
    
    # Simulate job stages
    stages = [
        (0.0, "Initializing job"),
        (10.0, "Loading input data"),
        (25.0, "Processing stage 1"),
        (50.0, "Processing stage 2"),
        (75.0, "Processing stage 3"),
        (90.0, "Finalizing results"),
        (100.0, "Job completed successfully"),
    ]
    
    try:
        # Start the job
        ProcessingJobLifecycle.mark_started(job_id)
        logger.info("✅ Job started")
        
        # Simulate progress through stages
        for progress, message in stages:
            if progress == 0.0:
                continue  # Already marked as started
                
            logger.info(f"⏳ Updating progress: {progress:.1f}% - {message}")
            ProcessingJobLifecycle.mark_progress(
                job_id,
                progress=progress,
                message=message,
                metadata={"stage": f"stage_{int(progress)}"}
            )
            
            # Wait to simulate processing time
            await asyncio.sleep(2)
        
        # Mark as completed
        ProcessingJobLifecycle.mark_completed(
            job_id,
            result_payload={"output": "demo_result.txt", "size": 1024}
        )
        logger.info("🎉 Job completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Job simulation failed: {e}")
        ProcessingJobLifecycle.mark_failed(job_id, str(e))


async def main():
    """Main demo function."""
    logger.info("🎬 Starting WebSocket Progress Demo")
    logger.info("=" * 50)
    
    try:
        # Create a demo job
        logger.info("📝 Creating demo job...")
        job = ProcessingJobLifecycle.enqueue(
            job_type=ProcessingJobType.GENERATE_CLIP,
            payload={
                "demo": True,
                "input": "demo_video.mp4",
                "output_format": "mp4",
                "quality": "high"
            }
        )
        
        job_id = job.id
        logger.info(f"✅ Job created with ID: {job_id}")
        logger.info(f"   Type: {job.job_type}")
        logger.info(f"   Status: {job.status}")
        logger.info("=" * 50)
        
        # Start WebSocket client and job simulation concurrently
        logger.info("🔌 Connecting to WebSocket and starting job simulation...")
        
        # Run WebSocket client and job simulation in parallel
        websocket_task = asyncio.create_task(websocket_client(job_id))
        simulation_task = asyncio.create_task(simulate_job_progress(job_id))
        
        # Wait for both tasks to complete
        await asyncio.gather(websocket_task, simulation_task, return_exceptions=True)
        
        logger.info("🏁 Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        logger.exception("Full exception details:")
    
    logger.info("=" * 50)
    logger.info("👋 WebSocket Progress Demo Finished")


def run_demo():
    """Run the demo with proper error handling."""
    print("🎬 WebSocket Progress Demo")
    print("=" * 50)
    print("This demo will:")
    print("1. Create a processing job")
    print("2. Connect to the WebSocket progress endpoint")
    print("3. Simulate job progress updates")
    print("4. Display real-time progress messages")
    print("=" * 50)
    print()
    print("⚠️  Make sure the FastAPI server is running on localhost:8000")
    print("   You can start it with: uvicorn backend.app.main:app --reload")
    print()
    print("Press Ctrl+C to stop the demo")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Make sure the FastAPI server is running on localhost:8000")


if __name__ == "__main__":
    run_demo()