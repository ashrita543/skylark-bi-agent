# Decision Log

## Architecture Overview

The Skylark BI Agent follows a **pipeline architecture**: query understanding → data fetching → normalization → deterministic analytics → LLM explanation. This keeps arithmetic in Python and prevents LLM hallucination.

---

## 1. Monday.com GraphQL API (vs. MCP)

**Decision**: Use Monday.com GraphQL API directly, not MCP (Model Context Protocol)

**Rationale**:
- GraphQL provides precise field selection and pagination control
- Direct API integration avoids extra abstraction layer
- Better error handling and rate-limit management
- More flexible for cross-board queries
- Easier to test with mocked responses

**Tradeoff**: Requires API token management (mitigated by environment variables)

---

## 2. Deterministic Analytics in Python

**Decision**: Calculate all metrics (totals, averages, sector aggregations) in Python, never delegate to LLM

**Rationale**:
- Auditable: No "where did this number come from?" doubt
- Consistent: Same input always produces same output
- Fast: No additional LLM calls for calculation
- Accurate: No hallucinated metrics
- Testable: Unit tests verify every calculation

**Implementation**: `analytics.py` contains pure functions for:
- `calculate_total_pipeline()` — sum of all deal values
- `calculate_active_pipeline()` — sum of "Open" deals only
- `calculate_weighted_pipeline()` — sum(deal_value × probability)
- `pipeline_by_sector()` — group and sum by sector
- `generate_leadership_summary()` — combined executive metrics

**LLM Role**: Explain the numbers naturally, not generate them

---

## 3. Streamlit for UI (vs. FastAPI/custom web app)

**Decision**: Use Streamlit for the chat interface

**Rationale**:
- Built-in chat UI (no HTML/JS required)
- Simple state management for conversation history
- Native Streamlit Cloud deployment (free tier available)
- No backend server configuration needed
- Rapid development cycle
- Good fit for executive dashboards

**Tradeoff**: Less customizable UI than custom web framework (acceptable for prototype)

---

## 4. Data Normalization Layer

**Decision**: Create dedicated `normalizer.py` module to clean messy Monday data

**Handles**:
- Null values (excluded from aggregates with caveat)
- Multiple date formats (MM/DD/YY, DD/MM/YY, ISO, etc.)
- Currency with symbols/commas ($1,000.00 → 1000.0)
- Sector name variations ("Energy" vs "energy")
- Status variants ("Open" vs "OPEN" vs "In Progress")
- Probability formats (0.8, 80%, "high")

**Data Quality Tracking**: Records which rows had issues for leadership-update caveats

---

## 5. Query Understanding (Heuristic-based)

**Decision**: Parse user intent with regex/keyword matching, not fine-tuned LLM classifier

**Rationale**:
- Fast (no LLM call required)
- Deterministic (same question → same interpretation)
- Easy to debug and extend
- No training data needed

**Limitations**: Only recognizes predefined patterns; asks for clarification when ambiguous

**Future Improvement**: Could fine-tune a small LLM for multi-class intent prediction if needed

---

## 6. Cross-Board Queries (Defensive)

**Decision**: Join Deals and Work Orders ONLY if explicit customer/deal identifier exists

**Rationale**:
- Avoids false positives (e.g., matching on similar company names)
- Data quality: Garbage-in-garbage-out risk is real
- Conservative: Better to say "can't join" than "incorrect join"

**Current State**: Joins possible if both boards share customer ID; documented in schema inspection

**Fallback**: Present sector analysis separately if join isn't possible

---

## 7. Leadership Summary Capability

**Decision**: Implement as optional query type (not forced on every conversation)

**Summary Includes**:
- Total pipeline value & count
- Active pipeline (Open deals)
- Average deal size
- Work orders: active, completed, delayed
- Top sectors by pipeline
- Data-quality caveats

**Exclusions**: Not included:
- Revenue (not tracked in this board schema)
- Win/loss rates (no historical close data)
- Forecast vs. actual (no forecast column)

**Caveats**: Explicitly lists what data was missing or excluded

---

## 8. Error Handling Strategy

**Three-Tier Approach**:

1. **Configuration Validation** (startup):
   - Check required env vars loaded
   - Validate Monday token format
   - Test API connectivity before UI loads

2. **API Resilience** (runtime):
   - Retry timeouts up to 3 times
   - Rate-limit backoff
   - Graceful degradation (missing columns → skip metrics)

3. **User-Facing** (UI):
   - No technical stack traces
   - Clear guidance ("Missing OPENAI_API_KEY")
   - Suggest actions ("Check sidebar for setup")

---

## 9. Testing Strategy

**88 Comprehensive Tests**:
- Unit tests with mocked Monday API (no real calls in tests)
- Normalization edge cases (null, empty, malformed)
- Analytics calculations verified against hardcoded test data
- Query planning intent detection
- Error scenarios (auth failure, timeout, invalid board ID)

**Excluded from Tests**:
- Real Monday.com API calls (slow, flaky)
- OpenAI API calls (costs money)
- Streamlit UI components (tested manually)

---

## 10. Security & Secrets Management

**Decision**: Environment variables for all secrets; `.env` never committed

**Local Development**:
- `.env` file (ignored by `.gitignore`)
- Values loaded by `python-dotenv`

**Streamlit Cloud**:
- Secrets configured in web UI (encrypted storage)
- Become environment variables in container automatically
- Never printed or logged

**Read-Only API**:
- Monday token scoped to read-only
- No write/delete operations possible

---

## 11. Deployment Model

**Decision**: Streamlit Community Cloud (not self-hosted, not Docker)

**Rationale**:
- Zero infrastructure management
- Automatic SSL/HTTPS
- Free tier sufficient for prototype
- GitHub integration for auto-deploy on push
- Public URL shareable immediately

**Fallback Option**: Dockerfile provided for self-hosting if needed

---

## 12. What Would Be Different With More Time

1. **Fine-tuned Intent Classifier**: Train small model on founder questions
2. **Historical Analytics**: Track deal movement over time, win rates
3. **Forecast Integration**: If boards include forecast data
4. **Custom Metrics**: Allow founders to define custom KPIs
5. **Email Reports**: Scheduled leadership updates via email
6. **Database Cache**: Persistent cache for faster repeat queries
7. **Authentication**: Only team members can access
8. **Audit Log**: Track who asked what, when
9. **Multi-currency Support**: Handle mixed USD/INR/EUR
10. **Real-time Updates**: WebSocket subscriptions instead of polling

---

## 13. Assumptions

1. **Calendar Year**: Results use Jan-Dec fiscal year
2. **India Timezone**: Timestamps interpreted as IST (can override)
3. **Sector Definitions**: "Energy", "Mining", "Manufacturing" are the domains
4. **Deal Status Values**: "Open" means active, "Closed" means done
5. **Work Order Status**: "In Progress" is active, "Completed" is finished
6. **Probability Field**: Values 0-1 or percentages; null = excluded from weighted calc
