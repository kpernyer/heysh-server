#!/usr/bin/env python3
"""
Simple configuration injector for the frontend.
This script serves the frontend with injected environment variables.
"""

import asyncio
import aiohttp
from aiohttp import web
import re

# Configuration for local development
CONFIG_JS = """
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

async def proxy_request(request):
    """Proxy request to the actual frontend and inject configuration."""
    frontend_url = "http://host.docker.internal:3000"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(frontend_url + str(request.rel_url)) as response:
            content = await response.text()
            
            # Inject configuration script into the HTML
            if response.content_type == 'text/html':
                # Find the closing </head> tag and inject our script
                config_script = f'<script>{CONFIG_JS}</script>'
                content = content.replace('</head>', f'{config_script}</head>')
            
            return web.Response(
                text=content,
                content_type=response.content_type,
                headers=response.headers
            )

app = web.Application()
app.router.add_route('*', '/{path:.*}', proxy_request)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=3001)
