# hey.sh - Project Plan

## Project Overview

**hey.sh** is a domain-based collaborative knowledge platform where users can:
- Create and manage knowledge domains
- Upload and organize documents
- Build searchable knowledge bases
- Collaborate with domain members
- Ask questions and get AI-powered answers from domain knowledge

## Current State (As of Now)

### ✅ Implemented Features
- **Authentication System**: Email/password signup and login with Supabase
- **Domain Management**: Create, view, and manage domains
- **User Roles**: Super admin, domain admin, and member roles
- **Domain Features**:
  - Overview dashboard
  - Member management
  - Document upload and storage
  - Knowledge base management
  - Domain settings
- **Pages**: Landing page, Dashboard, Admin panel, Inbox, Interests
- **Mock Data Generation**: Tool for testing

### 🏗️ Current Architecture
- Frontend: React + TypeScript + Tailwind CSS
- Backend: Lovable Cloud (Supabase)
- Database Tables: profiles, domains, domain_members, user_roles, documents
- Authentication: Supabase Auth with RLS policies

---

## Strategic Vision

### Pricing & Monetization Philosophy
**Hybrid Microtransaction Model**: Users start free, pay small amounts as they scale.

This model allows us to:
1. **Learn user intent quickly** - See who's serious vs. tire-kickers
2. **Segment users by behavior** - Identify Owners, Contributors, Controllers
3. **Generate revenue early** - Validate willingness to pay
4. **Keep barrier to entry low** - Free tier allows experimentation

### Target User Personas

We want to identify three key personas based on usage patterns:

1. **Domain Owners** (Entrepreneurs/Organizers)
   - Create multiple domains
   - Invite members
   - Pay for domain creation after 1st free domain
   - High-value users with organizational needs

2. **Contributors** (Knowledge Workers)
   - Upload documents to grow knowledge bases
   - Pay per document after free tier (5 docs)
   - Want to share expertise
   - Quality contributors are valuable

3. **Controllers** (Managers/QA)
   - Ask questions to test knowledge base
   - Review and approve contributions
   - Can rollback bad contributions
   - Pay for questions and reviews
   - Gatekeepers of quality

---

## Phase 1: Pricing Foundation & User Segmentation (Week 1-2)

### Goals
- Make pricing transparent upfront
- Track all user actions
- Implement free tier limits
- Add simple payment flow

### 1.1 Add Pricing Visibility

**Landing Page Updates:**
- Hero section: Add "Start free, pay as you grow" messaging
- Create `/pricing-faq` page (lightweight, not full pricing page)
- Add "Free to start" badge on signup page

**Key Messages:**
- First domain: FREE
- First 5 documents: FREE
- First 10 questions: FREE
- Then pay-as-you-go microtransactions

### 1.2 Database Schema: Usage Tracking Tables

```sql
-- Track every user action
CREATE TABLE public.user_actions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  action_type text NOT NULL, -- 'domain_created', 'document_uploaded', 'question_asked', 'review_submitted', etc.
  domain_id uuid REFERENCES public.domains(id) ON DELETE SET NULL,
  metadata jsonb, -- Flexible storage for action-specific data
  created_at timestamptz DEFAULT now() NOT NULL
);

-- Track user credit balance and free tier status
CREATE TABLE public.user_credits (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL UNIQUE,
  balance numeric DEFAULT 0 NOT NULL, -- Can go negative for "owed" amounts
  free_tier_status jsonb DEFAULT '{
    "domains_created": 0,
    "documents_uploaded": 0,
    "questions_asked": 0,
    "reviews_submitted": 0
  }'::jsonb,
  created_at timestamptz DEFAULT now() NOT NULL,
  updated_at timestamptz DEFAULT now() NOT NULL
);

-- Track all financial transactions
CREATE TABLE public.transactions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
  amount numeric NOT NULL, -- Positive for credits added, negative for charges
  transaction_type text NOT NULL, -- 'credit_purchase', 'domain_charge', 'document_charge', 'question_charge', 'penalty', 'refund'
  description text,
  metadata jsonb, -- Store Stripe payment ID, action reference, etc.
  created_at timestamptz DEFAULT now() NOT NULL
);

-- Enable RLS on all tables
ALTER TABLE public.user_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_credits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can view their own actions"
  ON public.user_actions FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own credits"
  ON public.user_credits FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view their own transactions"
  ON public.transactions FOR SELECT
  USING (auth.uid() = user_id);

-- Admins can view all (using has_role function)
CREATE POLICY "Admins can view all actions"
  ON public.user_actions FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can view all credits"
  ON public.user_credits FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));

CREATE POLICY "Admins can view all transactions"
  ON public.transactions FOR SELECT
  USING (public.has_role(auth.uid(), 'admin'));
```

### 1.3 Free Tier Limits & Pricing

| Action | Free Tier | After Free Tier | Price |
|--------|-----------|-----------------|-------|
| Domain Creation | 1st domain | 2nd domain+ | $5.00 per domain |
| Document Upload | First 5 docs | 6th document+ | $0.10 per document |
| Question Asked | First 10 questions | 11th question+ | $0.25 per question |
| Review Submitted | First 5 reviews | 6th review+ | $0.50 per review |

**Implementation:**
- Create middleware/hooks to check limits before actions
- Show "You've used X of Y free [actions]" in UI
- Prompt to add credits when limit reached
- Block action if credits insufficient

### 1.4 Payment Flow: Simple Stripe Integration

**Credit Purchase Options:**
- $10 (1000 credits)
- $25 (2500 credits + 5% bonus)
- $50 (5000 credits + 10% bonus)
- $100 (10000 credits + 15% bonus)

**Implementation:**
- Add "Add Credits" button to dashboard header
- Simple checkout modal with Stripe
- Credits immediately available after payment
- Transaction recorded in `transactions` table
- No subscriptions yet - pure usage-based

---

## Phase 2: Persona Detection & Learning (Week 3-4)

### Goals
- Build internal analytics to identify user personas
- Track contribution quality
- Implement review/rollback mechanisms
- Learn which personas generate most value

### 2.1 Admin Analytics Dashboard

**Build internal dashboard (admin-only) showing:**
- Total users by persona type
- Revenue per persona
- Retention by persona
- Actions per persona

**Key Metrics:**
```
Domain Owners:
- Total domains created
- Average domains per owner
- Revenue from domain creation
- Member invitations sent

Contributors:
- Total documents uploaded
- Average documents per contributor
- Quality score (based on reviews)
- Revenue from document uploads

Controllers:
- Total questions asked
- Total reviews submitted
- Rollback actions taken
- Revenue from questions/reviews
```

### 2.2 Contribution Quality Tracking

**Document Quality Scoring:**
```sql
ALTER TABLE public.documents ADD COLUMN quality_score numeric DEFAULT 5.0;
ALTER TABLE public.documents ADD COLUMN times_accessed integer DEFAULT 0;
ALTER TABLE public.documents ADD COLUMN times_referenced integer DEFAULT 0;
ALTER TABLE public.documents ADD COLUMN flagged_count integer DEFAULT 0;
```

**Track:**
- How many times document is accessed
- How many questions reference it
- If it's flagged as unhelpful
- If it's rolled back/removed

**Quality Algorithm:**
```
quality_score =
  (times_accessed × 0.3) +
  (times_referenced × 0.5) -
  (flagged_count × 2.0)
```

### 2.3 Review/Rollback System

**New Table:**
```sql
CREATE TABLE public.reviews (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  reviewer_id uuid REFERENCES public.profiles(id) NOT NULL,
  reviewable_type text NOT NULL, -- 'document', 'answer', 'contribution'
  reviewable_id uuid NOT NULL,
  domain_id uuid REFERENCES public.domains(id) NOT NULL,
  action text NOT NULL, -- 'approve', 'reject', 'rollback', 'flag'
  notes text,
  created_at timestamptz DEFAULT now() NOT NULL
);
```

**Features:**
- Domain admins can review document contributions
- Can approve, reject, or flag documents
- Can rollback (soft delete) documents
- Track quality metrics per contributor
- Penalize contributors with low quality scores

---

## Phase 3: Human-in-the-Loop Workflows (Week 5-6)

### Goals
- Build workflows where humans verify AI answers
- Implement contribution approval workflows
- Detect and fill knowledge gaps
- Create feedback loops for quality improvement

### 3.1 Question → Review → Answer Flow

**Workflow:**
1. User asks a question
2. AI generates answer from knowledge base
3. System calculates confidence score
4. If confidence < 0.7, flag for human review
5. Domain admin/controller reviews answer
6. They can edit, approve, or reject
7. Approved answers are saved for future reference
8. Charge microtransaction for review action

**New Tables:**
```sql
CREATE TABLE public.questions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  asker_id uuid REFERENCES public.profiles(id) NOT NULL,
  domain_id uuid REFERENCES public.domains(id) NOT NULL,
  question_text text NOT NULL,
  ai_answer text,
  confidence_score numeric,
  needs_review boolean DEFAULT false,
  reviewed_by uuid REFERENCES public.profiles(id),
  final_answer text,
  status text DEFAULT 'pending', -- 'pending', 'answered', 'reviewed', 'approved'
  created_at timestamptz DEFAULT now() NOT NULL
);
```

### 3.2 Document Contribution Workflow

**Workflow:**
1. User uploads document
2. AI extracts key information
3. Document goes to "pending approval" status
4. Domain admin receives notification
5. Admin reviews extracted information
6. Admin can approve, reject, or request changes
7. Track approval rate per contributor

### 3.3 Knowledge Gap Detection

**AI analyzes questions to identify:**
- Topics with low answer confidence
- Frequently asked questions without good answers
- Missing document types
- Areas where KB is weak

**Workflow:**
1. System identifies knowledge gap
2. Creates "document request" with suggested topic
3. Notifies potential contributors
4. Rewards contributors who fill the gap (bonus credits)
5. Tracks gap fill rate

---

## Success Metrics

### Early Validation Metrics (Week 1-4)

**Conversion Funnel:**
- Signup → Domain creation: Target 60%+
- Domain → Document upload: Target 40%+
- Document → Question asked: Target 30%+

**Free Tier Behavior:**
- % users hitting domain limit: Target 20%+
- % users hitting document limit: Target 15%+
- % users hitting question limit: Target 10%+

**Payment Conversion:**
- % users adding credits when prompted: Target 10%+
- Average first purchase: Target $25+
- Time to first purchase: Target <7 days

### Persona Learning Metrics (Week 3-6)

**Distribution:**
- % Domain Owners (creating 2+ domains): Target 15-20%
- % Contributors (uploading 6+ docs): Target 30-40%
- % Controllers (asking 11+ questions/reviews): Target 20-30%

**Revenue by Persona:**
- ARPU Domain Owners: Target $20+/month
- ARPU Contributors: Target $5+/month
- ARPU Controllers: Target $10+/month

**Quality Indicators:**
- Average document quality score: Target >6.0
- Review approval rate: Target >70%
- Rollback rate: Target <10%

### Revenue Validation Metrics (Week 4-8)

**Financial Health:**
- Average Revenue Per User (ARPU): Target $10+/month
- Lifetime Value (LTV) estimate: Target $120+
- Month-over-month growth: Target 20%+

**Transaction Breakdown:**
- Revenue from domain creation: Track %
- Revenue from documents: Track %
- Revenue from questions/reviews: Track %
- Most valuable microtransaction: Identify

---

## Key Decisions Made

### Pricing Model
✅ **Hybrid microtransaction** over pure subscription
- Reason: Learn user intent faster, lower barrier to entry, better segmentation

### Free Tier Strategy
✅ **Generous free tier** (1 domain, 5 docs, 10 questions)
- Reason: Allow experimentation, reduce signup friction, still filters serious users

### User Personas
✅ **Focus on 3 personas**: Owners, Contributors, Controllers
- Reason: Clear behavioral patterns, different willingness to pay, complementary roles

### Payment Timing
✅ **Charge at action time** vs. monthly billing
- Reason: Simpler to implement, users only pay for what they use, clearer value

### Quality Control
✅ **Human-in-the-loop** for quality assurance
- Reason: AI alone insufficient, build trust, create valuable Controller role

---

## Next Steps (Immediate)

### Week 1 Priorities:
1. ✅ Create this project plan document
2. ⏳ Implement Phase 1.1: Update landing page with pricing messaging
3. ⏳ Implement Phase 1.2: Create usage tracking tables (migration)
4. ⏳ Implement Phase 1.3: Add free tier limit checks
5. ⏳ Implement Phase 1.4: Stripe integration for credit purchases

### Week 2 Priorities:
1. ⏳ Build credit balance UI component
2. ⏳ Add "Add Credits" flow to dashboard
3. ⏳ Implement usage warnings (e.g., "2 free documents remaining")
4. ⏳ Test full payment flow end-to-end
5. ⏳ Monitor early metrics

---

## Questions & Considerations

### Open Questions:
1. **Stripe integration timing**: Start immediately or track usage first?
2. **Target ARPU**: What's the validation threshold?
3. **Acquisition strategy**: Organic vs. paid?
4. **Refund policy**: How to handle quality disputes?
5. **Credit expiration**: Should credits expire?

### Future Enhancements (Post-Phase 3):
- Team/enterprise pricing
- API access for integrations
- White-label options
- Advanced analytics dashboard for users
- Bulk upload/export features
- AI fine-tuning on domain knowledge
- Public vs. private domain options

---

## Change Log

| Date | Change | Reason |
|------|--------|--------|
| 2025-01-12 | Initial plan created | Establish project roadmap and strategy |

---

*This document is a living plan. Update it as we learn and iterate.*
