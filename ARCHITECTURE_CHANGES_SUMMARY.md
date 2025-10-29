# Architecture Changes Summary: Domain → Topic Migration

**Date:** 2025-01-28
**Migration ID:** 001
**Status:** Ready for Deployment

## Overview

This document summarizes the complete architectural changes from "Domain" to "Topic" terminology across the Hey.sh backend system.

## Rationale

The terminology change from "Domain" to "Topic" better reflects:
1. **User-centric language:** Topics are more intuitive than domains for knowledge organization
2. **Clearer semantics:** Avoids confusion with "domain" in web/DNS context
3. **HITL workflow clarity:** Separates topic management from workflow implementation details
4. **Role definitions:** Owner, Contributor, Controller, Member roles are topic-specific

## Changes Summary

### 1. Database Schema (migrations/)

**Tables Renamed:**
- `domains` → `topics`
- `domain_members` → `topic_members`

**Columns Renamed:**
- `documents.domain_id` → `documents.topic_id`
- `workflows.domain_id` → `workflows.topic_id`
- `domain_members.domain_id` → `topic_members.topic_id`
- `membership_requests.domain_id` → `membership_requests.topic_id`

**Constraints & Indexes:**
- All foreign key constraints updated
- All indexes renamed for consistency
- Data relationships preserved

**Files:**
- `migrations/001_rename_domain_to_topic_up.sql` - Forward migration
- `migrations/001_rename_domain_to_topic_down.sql` - Rollback migration
- `migrations/README.md` - Detailed migration documentation

### 2. API Endpoints (src/service/)

**Endpoint Changes:**

| Old Endpoint | New Endpoint | Status |
|-------------|-------------|--------|
| `POST /api/v1/domains` | `POST /api/v1/topics` | ✅ Updated |
| `GET /api/v1/domains` | `GET /api/v1/topics` | ✅ Updated |
| `GET /api/v1/domains/search` | `GET /api/v1/topics/search` | ✅ Updated |
| `GET /api/v1/domains/{id}` | `GET /api/v1/topics/{id}` | ✅ Updated |

**All workflow endpoints updated to use `topic_id`:**
- `POST /api/v1/documents` - Document upload
- `POST /api/v1/questions` - Question answering
- `POST /api/v1/reviews` - Quality reviews
- `GET /api/v1/workflows/{id}/status` - Workflow status

**Files Modified:**
- `src/service/routes_data.py` - Topic CRUD operations
- `src/service/routes_workflows.py` - Workflow orchestration

### 3. Data Models (src/app/)

**Core Models (src/app/models/domain.py):**
- `Domain` → `Topic`
- `DomainStatus` → `TopicStatus`
- `DomainRole` → `TopicRole` (now: OWNER, CONTRIBUTOR, CONTROLLER, MEMBER)
- `DomainMember` → `TopicMember`
- `BootstrapInput` - Updated to use topic fields
- `BootstrapResult` - Updated to use topic fields

**Request Schemas (src/app/schemas/requests.py):**
- `UploadDocumentRequest.topic_id`
- `AskQuestionRequest.topic_id`
- `SubmitReviewRequest.topic_id`
- `WorkflowDataRequest.topic_id`
- `DocumentDataRequest.topic_id`
- `CreateTopicRequest` - New model

**Response Schemas:**
- `WorkflowResponse` - No changes (workflow-agnostic)
- Topic-specific responses return `topic_id` fields

### 4. Role Semantics

**New TopicRole Enum:**
```python
class TopicRole(Enum):
    OWNER = "owner"           # Full control, bootstrap approvals
    CONTRIBUTOR = "contributor"  # Add/edit content
    CONTROLLER = "controller"    # Review and approve changes
    MEMBER = "member"           # Read-only access
```

These roles have specific meanings in HITL (Human-in-the-Loop) workflows but are not exposed in the public API.

### 5. Internal Implementation (Not Changed)

**Activity Layer (src/activity/):**
- Activity functions still reference "domain" internally
- This is acceptable as activities are internal implementation
- Future refactoring can update these for consistency

**Workflow Layer (src/workflow/):**
- Workflows reference "domain" in internal naming
- No breaking changes as workflows are internal
- Can be updated in future iterations

**Workers (src/worker/):**
- Workers maintain current implementation
- Accept topic data through API layer

## Backward Compatibility

**⚠️ BREAKING CHANGES - NO BACKWARD COMPATIBILITY**

- All API clients must update to use new endpoints
- All requests must use `topic_id` instead of `domain_id`
- Database migration is one-way (rollback available via migration script)
- Frontend must be updated simultaneously with backend deployment

## Deployment Strategy

### Recommended Approach: Blue-Green Deployment

1. **Preparation Phase**
   - Create full database backup
   - Test migration in staging environment
   - Update and test frontend code
   - Prepare rollback plan

2. **Deployment Phase**
   - Enable maintenance mode
   - Stop all backend services
   - Run database migration
   - Deploy updated backend code
   - Deploy updated frontend code
   - Verify all systems

3. **Verification Phase**
   - Run automated verification
   - Test critical workflows
   - Monitor error logs
   - Verify user functionality

4. **Rollback Plan** (if needed)
   - Run rollback migration
   - Restore from backup
   - Deploy previous code versions

### Timeline

- **Dev Environment:** 10 minutes
- **Staging Environment:** 30 minutes
- **Production Environment:** 60 minutes (with full verification)

## Testing Checklist

### Pre-Deployment Testing

- [ ] Migration runs successfully in dev
- [ ] Migration runs successfully in staging
- [ ] Frontend tests pass with new API
- [ ] All verification queries pass
- [ ] Data integrity confirmed
- [ ] Performance benchmarks acceptable

### Post-Deployment Testing

- [ ] Health check returns healthy
- [ ] Create topic endpoint works
- [ ] Search topics endpoint works
- [ ] Upload document workflow works
- [ ] Ask question workflow works
- [ ] Get workflow status works
- [ ] Frontend can display topics
- [ ] No errors in backend logs
- [ ] No errors in frontend logs

## Documentation Updates

**Created:**
- `API_MIGRATION_GUIDE.md` - Frontend migration guide
- `MIGRATION_QUICKSTART.md` - Quick start for running migrations
- `migrations/README.md` - Detailed migration documentation
- `ARCHITECTURE_CHANGES_SUMMARY.md` - This document

**Updated:**
- API endpoint documentation (inline)
- Request/response schemas
- Database models

**To Be Updated (by respective teams):**
- API reference documentation
- User-facing documentation
- Database ER diagrams
- Architecture diagrams

## Risk Assessment

### Low Risk
- ✅ Data loss: Transactions ensure atomicity
- ✅ Service interruption: Planned maintenance window
- ✅ Rollback capability: Full rollback migration available

### Medium Risk
- ⚠️ Frontend/backend sync: Requires coordinated deployment
- ⚠️ Migration duration: Depends on data volume

### Mitigation Strategies
- Full database backups before migration
- Staging environment testing
- Rollback scripts ready
- Monitoring and alerting enabled
- Coordinated deployment timeline

## Success Metrics

Migration is successful when:

1. **Database:**
   - All tables renamed correctly
   - All data preserved
   - Foreign keys intact
   - No orphaned records

2. **Backend:**
   - API starts without errors
   - All endpoints respond correctly
   - Workflows execute successfully
   - No schema-related errors

3. **Frontend:**
   - Can authenticate
   - Can list topics
   - Can create topics
   - Can search topics
   - Can upload documents
   - Can ask questions

4. **System:**
   - No error spikes in logs
   - Response times normal
   - Database queries optimized
   - No failed workflows

## Files Modified

### Backend Files (Total: 7)
1. `src/app/models/domain.py` - Core models
2. `src/app/schemas/requests.py` - Request schemas
3. `src/app/schemas/responses.py` - No changes needed
4. `src/service/routes_data.py` - Data management routes
5. `src/service/routes_workflows.py` - Workflow routes
6. `migrations/001_rename_domain_to_topic_up.sql` - Migration
7. `migrations/001_rename_domain_to_topic_down.sql` - Rollback

### Documentation Files (Total: 4)
1. `API_MIGRATION_GUIDE.md`
2. `MIGRATION_QUICKSTART.md`
3. `migrations/README.md`
4. `ARCHITECTURE_CHANGES_SUMMARY.md`

### Scripts (Total: 2)
1. `scripts/run_migration.py` - Migration runner
2. `scripts/verify_migration.sh` - Verification script

## Next Steps

### Immediate (Pre-Deployment)
1. Review all changes
2. Test in development environment
3. Test in staging environment
4. Update frontend code
5. Schedule deployment window

### Deployment Day
1. Create database backup
2. Stop all services
3. Run migration
4. Deploy backend
5. Deploy frontend
6. Verify and monitor

### Post-Deployment
1. Monitor system health
2. Gather user feedback
3. Update activity layer (optional future work)
4. Update workflow layer (optional future work)
5. Archive this migration documentation

## Questions & Support

For questions or issues:

1. **Migration Questions:** See `MIGRATION_QUICKSTART.md`
2. **API Changes:** See `API_MIGRATION_GUIDE.md`
3. **Technical Issues:** Check migration logs and verification output
4. **Emergency Rollback:** Run `python scripts/run_migration.py --down`

## Approval Checklist

Before proceeding with production deployment:

- [ ] Technical review completed
- [ ] Database migration tested in staging
- [ ] Frontend changes tested
- [ ] Performance impact assessed
- [ ] Rollback plan verified
- [ ] Deployment schedule confirmed
- [ ] Team notified
- [ ] Monitoring configured
- [ ] Backup created
- [ ] Final approval obtained

---

**Prepared by:** Backend Team
**Review Date:** [To be filled]
**Approved by:** [To be filled]
**Deployment Date:** [To be filled]
