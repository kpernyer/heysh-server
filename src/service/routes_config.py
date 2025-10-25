"""Configuration endpoint for frontend environment variables."""

from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter(prefix="/api/v1/config", tags=["config"])


@router.get("/frontend")
async def get_frontend_config():
    """Get frontend configuration including Supabase settings."""
    return {
        "supabase": {
            "url": "http://supabase.hey.local",  # Use local MinIO as Supabase alternative
            "anon_key": "local-development-key",  # Placeholder for local development
        },
        "api": {
            "url": "http://api.hey.local",
        },
        "environment": "development",
    }


@router.get("/frontend.js")
async def get_frontend_config_js():
    """Get frontend configuration as JavaScript."""
    config_js = """
// Frontend configuration for hey.sh local development
window.HEY_CONFIG = {
  VITE_SUPABASE_URL: "http://supabase.hey.local",
  VITE_SUPABASE_ANON_KEY: "local-development-key",
  VITE_API_URL: "http://api.hey.local",
  VITE_TEMPORAL_ADDRESS: "localhost:7233",
  VITE_TEMPORAL_NAMESPACE: "default",
  NODE_ENV: "development"
};

// Make environment variables available globally
if (typeof process !== 'undefined' && process.env) {
  Object.assign(process.env, window.HEY_CONFIG);
}

// Also set them on window for direct access
Object.assign(window, window.HEY_CONFIG);
"""
    return Response(content=config_js, media_type="application/javascript")
