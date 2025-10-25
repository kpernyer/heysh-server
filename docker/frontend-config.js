// Frontend configuration for hey.sh local development
// This script provides environment variables for the frontend

window.HEY_CONFIG = {
  VITE_SUPABASE_URL: "http://supabase.hey.local",
  VITE_SUPABASE_ANON_KEY: "local-development-key",
  VITE_API_URL: "http://api.hey.local",
  VITE_TEMPORAL_ADDRESS: "localhost:7233",
  VITE_TEMPORAL_NAMESPACE: "default",
  NODE_ENV: "development"
};

// Make environment variables available globally
Object.assign(process?.env || {}, window.HEY_CONFIG);
