import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class MediaAssetRepository:
    def __init__(self):
        # In a real implementation, this would connect to a database
        # For now, we'll use a simple in-memory storage for demonstration
        self._assets = {}
        self._transcriptions = {}
        self._clip_suggestions = {}

    async def get_by_id(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a media asset by its ID.
        """
        # In a real implementation, this would query the database
        asset = self._assets.get(asset_id)
        if asset:
            return asset
        # For demonstration, returning a mock asset if not found in memory
        return {
            'id': asset_id,
            'file_path': f'/workspace/storage/{asset_id}.mp4',
            'file_name': f'{asset_id}.mp4',
            'file_size': 1024000,  # 1MB mock size
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat(),
            'status': 'uploaded',
            'user_id': 'user_123'
        }

    async def update_transcription(self, asset_id: str, transcription_data: Dict[str, Any]) -> bool:
        """
        Update the transcription data for a media asset.
        """
        # Store transcription data
        self._transcriptions[asset_id] = {
            'asset_id': asset_id,
            'transcription': transcription_data,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Update the asset status
        if asset_id in self._assets:
            self._assets[asset_id]['transcription_status'] = 'completed'
            self._assets[asset_id]['updated_at'] = datetime.utcnow().isoformat()
        else:
            # If asset doesn't exist in memory, create a basic record
            self._assets[asset_id] = {
                'id': asset_id,
                'transcription_status': 'completed',
                'updated_at': datetime.utcnow().isoformat()
            }
        
        logger.info(f"Updated transcription for asset {asset_id}")
        return True

    async def update_clip_suggestions(self, asset_id: str, clip_suggestions: List[Dict[str, Any]]) -> bool:
        """
        Update the clip suggestions for a media asset.
        """
        # Store clip suggestions
        self._clip_suggestions[asset_id] = {
            'asset_id': asset_id,
            'clip_suggestions': clip_suggestions,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Update the asset status
        if asset_id in self._assets:
            self._assets[asset_id]['clip_generation_status'] = 'completed'
            self._assets[asset_id]['updated_at'] = datetime.utcnow().isoformat()
        else:
            # If asset doesn't exist in memory, create a basic record
            self._assets[asset_id] = {
                'id': asset_id,
                'clip_generation_status': 'completed',
                'updated_at': datetime.utcnow().isoformat()
            }
        
        logger.info(f"Updated clip suggestions for asset {asset_id}")
        return True

    async def create(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new media asset record.
        """
        asset_id = asset_data.get('id')
        if not asset_id:
            # Generate a simple ID for demonstration
            import uuid
            asset_id = str(uuid.uuid4())
            asset_data['id'] = asset_id
        
        self._assets[asset_id] = {
            **asset_data,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Created media asset {asset_id}")
        return self._assets[asset_id]

    async def update_status(self, asset_id: str, status: str) -> bool:
        """
        Update the status of a media asset.
        """
        if asset_id in self._assets:
            self._assets[asset_id]['status'] = status
            self._assets[asset_id]['updated_at'] = datetime.utcnow().isoformat()
            return True
        return False