# Domain Search with Semantic Search (Weaviate + Neo4j + LLM)

This guide explains how to implement semantic search on the Dashboard page using the backend's Weaviate vector database, Neo4j graph database, and LLM for intelligent summaries.

## Architecture

```
1. Create Domain
   Frontend → Backend API → Weaviate (vector index) + Neo4j (graph)

2. Search Domains (Dashboard search box)
   Frontend → Backend API → Weaviate (semantic) + Neo4j (relationships) → LLM → Summary
```

---

## 1. Creating a Domain (with automatic indexing)

When a user creates a domain, it's automatically indexed in both Weaviate and Neo4j for search.

### Backend API

```typescript
import { createDomain } from '@/lib/backend-api';

// When user creates a domain
const result = await createDomain({
  domain_id: crypto.randomUUID(),
  name: "AI Research Group",
  description: "A collaborative space for AI researchers to share papers, discuss breakthroughs, and coordinate on projects.",
  created_by: user.id,
});

console.log('Domain indexed:', result);
// { domain_id: "...", status: "indexed", message: "Domain created and indexed successfully" }
```

### What Happens Behind the Scenes

1. **Weaviate Vector Index**
   - Creates text embedding from domain name + description
   - Stores domain with vector for semantic search
   - Enables finding domains by meaning, not just keywords

2. **Neo4j Graph Index**
   - Creates Domain node in graph
   - Links to User who created it: `(User)-[:CREATED]->(Domain)`
   - Enables relationship-based queries (e.g., "domains you're a member of")

---

## 2. Searching Domains (Dashboard)

The search function combines **semantic similarity** (Weaviate) with **graph relationships** (Neo4j) and **LLM summarization**.

### Frontend Implementation

```typescript
// pages/Dashboard.tsx or wherever your search is
import { searchDomains, type SearchResult } from '@/lib/backend-api';
import { useState } from 'react';

export function DashboardSearch({ userId }: { userId: string }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const searchResults = await searchDomains(
        query,
        userId,
        true  // use LLM for summary
      );

      setResults(searchResults);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="Search domains..."
          className="flex-1 px-4 py-2 border rounded"
        />
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {results && (
        <div className="mt-6 space-y-6">
          {/* LLM-generated summary */}
          {results.summary && (
            <div className="p-4 bg-blue-50 rounded-lg">
              <h3 className="font-semibold mb-2">Summary</h3>
              <p className="text-gray-700">{results.summary}</p>
            </div>
          )}

          {/* Semantic results from Weaviate */}
          <div>
            <h3 className="font-semibold mb-3">
              Semantic Matches ({results.result_count.vector})
            </h3>
            <div className="space-y-2">
              {results.results.vector_results.map((domain) => (
                <div
                  key={domain.domain_id}
                  className="p-4 border rounded hover:border-blue-500"
                >
                  <h4 className="font-medium">{domain.name}</h4>
                  <p className="text-sm text-gray-600">{domain.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Graph results from Neo4j */}
          <div>
            <h3 className="font-semibold mb-3">
              Related Domains ({results.result_count.graph})
            </h3>
            <div className="space-y-2">
              {results.results.graph_results.map((domain) => (
                <div
                  key={domain.domain_id}
                  className="p-4 border rounded hover:border-blue-500"
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-medium">{domain.name}</h4>
                    {domain.is_member && (
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        Member
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600">{domain.description}</p>
                  {domain.creator_name && (
                    <p className="text-xs text-gray-500 mt-1">
                      Created by {domain.creator_name}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 3. How Search Works (Backend)

### Step 1: Weaviate Vector Search (Semantic)

Finds domains that are **semantically similar** to the query, even if they don't contain exact keywords.

Example:
- Query: "machine learning projects"
- Finds: "AI Research Group" (even though it doesn't say "machine learning")

### Step 2: Neo4j Graph Search (Relationships)

Finds domains based on:
- Keyword matching in name/description
- User membership (domains you belong to)
- Creator relationships

### Step 3: LLM Summarization

Combines results from both sources and generates a human-readable summary highlighting the most relevant domains.

---

## 4. Example Queries

### Query: "AI research"

**Vector Results** (semantic similarity):
- "Machine Learning Lab" - High similarity
- "Deep Learning Group" - High similarity
- "AI Safety Research" - High similarity

**Graph Results** (relationships):
- "AI Research Group" - You are a member
- "Neural Networks Team" - Created by colleague

**LLM Summary**:
> "Based on your search for 'AI research', I found 5 relevant domains. The most relevant is 'AI Research Group' where you are already a member. Other highly similar domains include 'Machine Learning Lab' and 'Deep Learning Group', which focus on practical ML applications..."

---

## 5. Advanced: Customize Search

### Without LLM (faster, raw results)

```typescript
const results = await searchDomains(
  query,
  userId,
  false  // no LLM summary
);
```

### Mock Mode (for testing UI without backend)

```typescript
const mockResults: SearchResult = {
  query: query,
  results: {
    vector_results: [
      {
        domain_id: '1',
        name: 'AI Research Group',
        description: 'Collaborative AI research',
        created_by: 'user-123',
      },
    ],
    graph_results: [
      {
        domain_id: '1',
        name: 'AI Research Group',
        description: 'Collaborative AI research',
        created_by: 'user-123',
        creator_name: 'John Doe',
        is_member: true,
      },
    ],
  },
  summary: 'Based on your search, here are the most relevant domains...',
  result_count: {
    vector: 1,
    graph: 1,
  },
};
```

---

## 6. Testing

### Create Test Domains

```bash
# Use the Python CLI
cd backend
python script/workflow_client.py health

# Or use curl
curl -X POST http://localhost:8001/api/v1/domains \
  -H "Content-Type: application/json" \
  -d '{
    "domain_id": "ai-research-001",
    "name": "AI Research Group",
    "description": "Collaborative space for AI researchers to share papers and discuss breakthroughs",
    "created_by": "user-123"
  }'
```

### Test Search

```bash
# Search domains
curl "http://localhost:8001/api/v1/domains/search?q=machine%20learning&user_id=user-123&use_llm=true"
```

---

## 7. Error Handling

```typescript
try {
  const results = await searchDomains(query, userId);
  setResults(results);
} catch (error) {
  if (error.message.includes('Backend is unhealthy')) {
    // Backend not running
    console.error('Backend API is down. Start it with: cd backend && just dev');
  } else {
    // Other error
    console.error('Search failed:', error);
  }
}
```

---

## 8. Environment Setup

Make sure these are set:

```bash
# .env.local (frontend)
VITE_API_URL=http://localhost:8001

# .env (backend)
OPENAI_API_KEY=sk-proj-...
NEO4J_URI=bolt://localhost:7687
NEO4J_PASSWORD=password
WEAVIATE_URL=http://localhost:8082
```

---

## Summary

**For Domain Creation:**
```typescript
import { createDomain } from '@/lib/backend-api';

await createDomain({
  domain_id: crypto.randomUUID(),
  name: "Domain Name",
  description: "Domain description",
  created_by: user.id,
});
```

**For Search:**
```typescript
import { searchDomains } from '@/lib/backend-api';

const results = await searchDomains(
  "search query",
  user.id,
  true  // use LLM
);

// Display: results.summary, results.results.vector_results, results.results.graph_results
```

This gives you powerful semantic search combining vector similarity, graph relationships, and LLM intelligence!
