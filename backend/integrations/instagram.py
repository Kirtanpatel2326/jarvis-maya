import os
from .base import BaseAdapter

class InstagramAdapter(BaseAdapter):
    """
    Instagram Graph API adapter. 
    Handles webhook-driven updates and autonomous marketing posting.
    """
    def __init__(self):
        # Graph API base URL
        super().__init__("Instagram", "https://graph.facebook.com/v19.0/")
        self.access_token = os.environ.get("IG_ACCESS_TOKEN")
        self.ig_account_id = os.environ.get("IG_ACCOUNT_ID")
        
        if not self.access_token or not self.ig_account_id:
            self.is_healthy = False
            
    async def health_check(self) -> bool:
        """Ping the Graph API to verify the token is still valid."""
        if not self.access_token:
            return False
        try:
            resp = await self.client.get(f"{self.ig_account_id}?access_token={self.access_token}")
            return resp.status_code == 200
        except Exception:
            return False

    async def fetch_recent_metrics(self):
        """Fetches recent insights for the connected IG account."""
        if not self.access_token:
            return {"error": "IG Token not configured"}
            
        endpoint = f"{self.ig_account_id}/insights?metric=impressions,reach,profile_views&period=day&access_token={self.access_token}"
        try:
            # Uses the base class's Tenacity retry logic
            resp = await self._safe_request("GET", endpoint)
            return resp.json()
        except Exception as e:
            return {"error": str(e)}
