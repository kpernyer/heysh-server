# Extensions Index

Staged guides for extending the hey.sh backend.

## Available Extensions

### Extension 1: Advanced Workflows
**Status**: ⏳ Planned
**File**: `extension-01-advanced-workflows.md`

Learn to create complex multi-step workflows with:
- Parallel activity execution
- Child workflows
- Continue-as-new pattern
- Signals and queries
- Workflow versioning

### Extension 2: Vector Search Optimization
**Status**: ⏳ Planned
**File**: `extension-02-vector-search.md`

Advanced Weaviate usage:
- Custom vector models
- Hybrid search (vector + keyword)
- Multi-vector indexing
- Performance tuning
- Batch operations

### Extension 3: Knowledge Graph Advanced Queries
**Status**: ⏳ Planned
**File**: `extension-03-neo4j-advanced.md`

Neo4j advanced patterns:
- Graph algorithms (PageRank, Community Detection)
- Path finding
- Recommendation engines
- Graph embeddings
- Performance optimization

### Extension 4: Authentication & Authorization
**Status**: ⏳ Planned
**File**: `extension-04-auth.md`

Security implementation:
- JWT authentication
- Role-based access control (RBAC)
- Domain-level permissions
- API key management
- OAuth integration

### Extension 5: Monitoring & Observability
**Status**: ⏳ Planned
**File**: `extension-05-monitoring.md`

Production monitoring:
- Structured logging with structlog
- OpenTelemetry integration
- Prometheus metrics
- Grafana dashboards
- Alert configuration

### Extension 6: Database Migrations
**Status**: ⏳ Planned
**File**: `extension-06-migrations.md`

Schema evolution:
- Alembic for SQL migrations
- Neo4j schema migrations
- Weaviate schema updates
- Zero-downtime migrations
- Rollback strategies

### Extension 7: Background Jobs & Scheduling
**Status**: ⏳ Planned
**File**: `extension-07-scheduling.md`

Scheduled workflows:
- Cron workflows
- Periodic processing
- Cleanup jobs
- Report generation
- Data synchronization

### Extension 8: Advanced Testing Strategies
**Status**: ⏳ Planned
**File**: `extension-08-testing.md`

Comprehensive testing:
- Temporal workflow testing
- Integration tests
- Contract testing
- Load testing
- Chaos engineering

### Extension 9: Multi-Tenancy
**Status**: ⏳ Planned
**File**: `extension-09-multi-tenancy.md`

Tenant isolation:
- Domain isolation strategies
- Database partitioning
- Resource quotas
- Tenant-specific configurations
- Billing integration

### Extension 10: Production Deployment
**Status**: ⏳ Planned
**File**: `extension-10-production.md`

Production best practices:
- GKE deployment
- CI/CD pipelines
- Secrets management
- Backup & disaster recovery
- Performance tuning
- Cost optimization

## How to Use Extensions

Each extension builds on the basics and previous extensions. Follow in order for best results:

1. Complete [basics.md](basics.md) first
2. Choose extensions based on your needs
3. Extensions are independent after prerequisites
4. Refer back to basics for core concepts

## Contributing Extensions

Want to add an extension? Follow this template:

```markdown
# Extension N: Title

**Prerequisites**: Extension X, Extension Y

## Overview

Brief description...

## Implementation

Step-by-step guide...

## Example

Working code example...

## Testing

How to test this extension...

## Next Steps

Related extensions...
```
