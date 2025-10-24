"""
Application constants and text strings.
All text strings and constants should be defined here.
"""


class Constants:
    """Application constants and text strings."""

    # API Endpoints
    API_BASE_URL = "https://api.hey.sh"
    GRAPHQL_ENDPOINT = "/graphql"
    HEALTH_CHECK_ENDPOINT = "/health"

    # Workflow Status
    WORKFLOW_STATUS_PENDING = "pending"
    WORKFLOW_STATUS_RUNNING = "running"
    WORKFLOW_STATUS_COMPLETED = "completed"
    WORKFLOW_STATUS_FAILED = "failed"
    WORKFLOW_STATUS_CANCELLED = "cancelled"

    # Error Messages
    ERROR_INVALID_WORKFLOW = "Invalid workflow definition"
    ERROR_MISSING_REQUIRED_FIELD = "Missing required field: {field}"
    ERROR_VALIDATION_FAILED = "Validation failed: {details}"
    ERROR_PORT_CONFLICT = "Port conflict detected: {ports}"
    ERROR_HOSTNAME_INVALID = "Invalid hostname format: {hostname}"

    # UI Messages
    SUCCESS_WORKFLOW_SAVED = "Workflow saved successfully"
    SUCCESS_DOCUMENT_UPLOADED = "Document uploaded successfully"
    INFO_PROCESSING_WORKFLOW = "Processing workflow..."
    INFO_SERVICE_STARTING = "Starting {service} service..."
    INFO_SERVICE_STOPPED = "Stopped {service} service"

    # Development Messages
    DEV_SERVICE_READY = "Development service ready at {url}"
    DEV_ALL_SERVICES_READY = "All development services ready"
    DEV_ACCESS_POINTS = "Access points:"
    DEV_FRONTEND = "Frontend: {url}"
    DEV_API = "API: {url}"
    DEV_TEMPORAL = "Temporal: {url}"

    # Health Check Messages
    HEALTH_CHECK_SUCCESS = "Health check passed"
    HEALTH_CHECK_FAILED = "Health check failed"
    HEALTH_CHECK_SERVICE_DOWN = "Service {service} is down"

    # Configuration Messages
    CONFIG_LOADED = "Configuration loaded for environment: {env}"
    CONFIG_VALIDATION_FAILED = "Configuration validation failed: {errors}"
    CONFIG_ENVIRONMENT_SET = "Environment set to: {env}"

    # Docker Messages
    DOCKER_SERVICES_STARTING = "Starting Docker services..."
    DOCKER_SERVICES_STOPPED = "Docker services stopped"
    DOCKER_SERVICES_RESTARTED = "Docker services restarted"
    DOCKER_CLEANUP_COMPLETE = "Docker cleanup completed"

    # Caddy Messages
    CADDY_STARTING = "Starting Caddy reverse proxy..."
    CADDY_STOPPED = "Caddy reverse proxy stopped"
    CADDY_RELOADED = "Caddy configuration reloaded"
    CADDY_VALIDATION_PASSED = "Caddy configuration is valid"
    CADDY_VALIDATION_FAILED = "Caddy configuration validation failed"

    # Database Messages
    DATABASE_CONNECTED = "Database connected successfully"
    DATABASE_DISCONNECTED = "Database disconnected"
    DATABASE_MIGRATION_COMPLETE = "Database migration completed"
    DATABASE_ROLLBACK_COMPLETE = "Database rollback completed"

    # Temporal Messages
    TEMPORAL_SERVER_STARTING = "Starting Temporal server..."
    TEMPORAL_SERVER_STARTED = "Temporal server started"
    TEMPORAL_WORKFLOW_STARTED = "Workflow {workflow_id} started"
    TEMPORAL_WORKFLOW_COMPLETED = "Workflow {workflow_id} completed"
    TEMPORAL_WORKFLOW_FAILED = "Workflow {workflow_id} failed"

    # Monitoring Messages
    MONITORING_STACK_STARTING = "Starting monitoring stack..."
    MONITORING_STACK_READY = "Monitoring stack ready"
    METRICS_COLLECTION_STARTED = "Metrics collection started"
    ALERTING_CONFIGURED = "Alerting configured"

    # Security Messages
    SECURITY_SCAN_STARTED = "Security scan started"
    SECURITY_SCAN_COMPLETED = "Security scan completed"
    SECURITY_VULNERABILITIES_FOUND = "Security vulnerabilities found: {count}"
    SECURITY_SCAN_CLEAN = "Security scan clean - no vulnerabilities found"

    # Testing Messages
    TESTS_STARTING = "Starting tests..."
    TESTS_COMPLETED = "Tests completed"
    TESTS_FAILED = "Tests failed: {failures}"
    TEST_COVERAGE = "Test coverage: {coverage}%"

    # Linting Messages
    LINTING_STARTED = "Running code quality checks..."
    LINTING_COMPLETED = "Code quality checks completed"
    LINTING_FAILED = "Code quality checks failed: {issues}"
    LINTING_CLEAN = "Code quality checks passed"

    # Deployment Messages
    DEPLOYMENT_STARTING = "Starting deployment..."
    DEPLOYMENT_COMPLETED = "Deployment completed successfully"
    DEPLOYMENT_FAILED = "Deployment failed: {error}"
    DEPLOYMENT_ROLLBACK = "Deployment rollback initiated"

    # Documentation Messages
    DOCS_GENERATING = "Generating documentation..."
    DOCS_GENERATED = "Documentation generated successfully"
    DOCS_VALIDATION_FAILED = "Documentation validation failed"
    DOCS_UPDATED = "Documentation updated"
