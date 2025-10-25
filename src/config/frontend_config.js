/**
 * Hey.sh Frontend Configuration
 * Single source of truth for all environment-specific configuration.
 * 
 * Usage in frontend:
 * import { API_URL, FRONTEND_URL, config } from './config/frontend_config.js';
 */

// Environment detection
const ENVIRONMENT = process.env.NODE_ENV === 'production' ? 'production' : 'development';

// Base domains
const DEV_DOMAIN = 'hey.local';
const PROD_DOMAIN = 'hey.sh';

// Service names (consistent across environments)
const SERVICES = {
    frontend: 'www.hey',
    api: 'api',
    temporal: 'temporal',
    temporal_ui: 'temporal-ui',
    neo4j: 'neo4j',
    weaviate: 'weaviate',
    postgres: 'db',
    redis: 'redis',
    minio: 'minio',
    monitoring: 'monitoring',
    grafana: 'grafana',
    alertmanager: 'alertmanager',
    jaeger: 'jaeger',
    loki: 'loki',
};

// Ports (consistent across environments)
const PORTS = {
    api: 8002,
    temporal: 7233,
    temporal_ui: 8090,
    neo4j: 7474,
    weaviate: 8082,
    postgres: 5432,
    redis: 6379,
    minio: 9000,
    minio_console: 9001,
    monitoring: 9090,
    grafana: 3001,
    alertmanager: 9093,
    jaeger: 16686,
    loki: 3100,
    caddy_http: 80,
    caddy_https: 443,
};

// Configuration class
class Config {
    constructor() {
        this.environment = ENVIRONMENT;
        this.isDevelopment = this.environment === 'development';
        this.isProduction = this.environment === 'production';
        
        // Choose domain based on environment
        this.domain = this.isDevelopment ? DEV_DOMAIN : PROD_DOMAIN;
        
        // Choose protocol based on environment
        this.protocol = this.isDevelopment ? 'http' : 'https';
    }
    
    getHostname(service) {
        const serviceName = SERVICES[service];
        if (!serviceName) {
            throw new Error(`Unknown service: ${service}`);
        }
        
        // Special handling for frontend to use www.hey.local / www.hey.sh
        if (service === 'frontend') {
            return `www.${this.domain}`;
        }
        
        return `${serviceName}.${this.domain}`;
    }
    
    getUrl(service, path = '') {
        const hostname = this.getHostname(service);
        let url = `${this.protocol}://${hostname}`;
        if (path) {
            url += `/${path.replace(/^\//, '')}`;
        }
        return url;
    }
    
    getPort(service) {
        return PORTS[service] || 80;
    }
    
    getLocalUrl(service, path = '') {
        const port = this.getPort(service);
        let url = `http://localhost:${port}`;
        if (path) {
            url += `/${path.replace(/^\//, '')}`;
        }
        return url;
    }
}

// Global configuration instance
const config = new Config();

// Pre-built URLs (use these constants everywhere)
export const API_URL = config.getUrl('api');
export const FRONTEND_URL = config.getUrl('frontend');
export const TEMPORAL_URL = config.getUrl('temporal');
export const TEMPORAL_UI_URL = config.getUrl('temporal_ui');
export const NEO4J_URL = config.getUrl('neo4j');
export const WEAVIATE_URL = config.getUrl('weaviate');
export const POSTGRES_URL = config.getUrl('postgres');
export const REDIS_URL = config.getUrl('redis');
export const MINIO_URL = config.getUrl('minio');
export const MONITORING_URL = config.getUrl('monitoring');
export const GRAFANA_URL = config.getUrl('grafana');
export const ALERTMANAGER_URL = config.getUrl('alertmanager');
export const JAEGER_URL = config.getUrl('jaeger');
export const LOKI_URL = config.getUrl('loki');

// Local URLs for direct access
export const API_LOCAL_URL = config.getLocalUrl('api');
export const FRONTEND_LOCAL_URL = config.getLocalUrl('frontend');
export const TEMPORAL_LOCAL_URL = config.getLocalUrl('temporal');
export const TEMPORAL_UI_LOCAL_URL = config.getLocalUrl('temporal_ui');
export const NEO4J_LOCAL_URL = config.getLocalUrl('neo4j');
export const WEAVIATE_LOCAL_URL = config.getLocalUrl('weaviate');
export const POSTGRES_LOCAL_URL = config.getLocalUrl('postgres');
export const REDIS_LOCAL_URL = config.getLocalUrl('redis');
export const MINIO_LOCAL_URL = config.getLocalUrl('minio');
export const MONITORING_LOCAL_URL = config.getLocalUrl('monitoring');
export const GRAFANA_LOCAL_URL = config.getLocalUrl('grafana');
export const ALERTMANAGER_LOCAL_URL = config.getLocalUrl('alertmanager');
export const JAEGER_LOCAL_URL = config.getLocalUrl('jaeger');
export const LOKI_LOCAL_URL = config.getLocalUrl('loki');

// Environment info
export const ENVIRONMENT_INFO = {
    environment: config.environment,
    isDevelopment: config.isDevelopment,
    isProduction: config.isProduction,
    domain: config.domain,
    protocol: config.protocol,
};

// Export the config object for dynamic usage
export { config };

// Example usage:
/*
// ✅ CORRECT: Use the pre-built constants
import { API_URL, FRONTEND_URL } from './config/frontend_config.js';
fetch(`${API_URL}/health`);

// ✅ CORRECT: Use the config object for dynamic URLs
import { config } from './config/frontend_config.js';
const healthUrl = config.getUrl('api', '/health');

// ✅ CORRECT: Check environment
import { ENVIRONMENT_INFO } from './config/frontend_config.js';
if (ENVIRONMENT_INFO.isDevelopment) {
    console.log('Running in development mode');
}

// ❌ WRONG: Don't hardcode URLs
// const badUrl = 'http://localhost:8002';  // DON'T DO THIS

// ❌ WRONG: Don't construct URLs manually
// const badUrl = `http://api.hey.local`;  // DON'T DO THIS
*/
