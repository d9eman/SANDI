# RAG + SMS integration plan

## Key architectural decision

Do **not** merge the RAG model into the eligibility engine.

Treat web, SMS, and an AI conversation as different **presentation/input adapters** over the same SANDI application services.

```text
Web forms ────────┐
SMS webhook ──────┼──> Conversation / intent adapter
RAG chat widget ──┘            │
                               ↓
                     existing application services
               Profile | Screening | Resources | Referrals
                               │
              deterministic eligibility rules remain here
```

## What RAG should do

Good uses:

- interpret plain-language needs;
- retrieve provider descriptions and verified source text;
- explain an approved rule in simpler language;
- translate content;
- ask a conversational version of the **next approved question** selected by `ScreeningService`;
- summarize provider options returned by `ResourceService`.

RAG should **not**:

- invent eligibility rules;
- decide that an applicant is eligible outside the deterministic evaluator;
- silently write arbitrary profile fields;
- invent hours, capacity, or provider participation.

## Proposed shared API contract

Add an API layer that both the website and SMS service can call:

```text
POST /api/v1/sessions
POST /api/v1/profiles/{id}/answers
GET  /api/v1/profiles/{id}/next-question
GET  /api/v1/profiles/{id}/assessments
GET  /api/v1/resources/food?zip=92101
POST /api/v1/referrals
POST /api/v1/resource-feedback
```

The API endpoints should call the same application services already used by HTML routes. Do not duplicate rule logic in the SMS repository.

## SMS flow

```text
User: FOOD 92101
  ↓
SMS adapter parses command/intent
  ↓
ResourceService.find_food
  ↓
Reply with 2–3 concise options / locator links
  ↓
Ask: “Want to check other programs you may qualify for? Reply YES.”
  ↓
Create/recover anonymous profile
  ↓
ScreeningService.next_question
  ↓
SMS asks exactly one approved question
  ↓
Answer saved through ProfileService
  ↓
Re-evaluate and send newly actionable matches
```

A basic phone therefore gets the same eligibility logic as the web app.

## Identity mapping for SMS

Do not make the raw phone number the profile ID. Use a separate contact/recovery mapping:

```text
phone/contact record -> profile ID
profile ID -> answers/assessments
```

This keeps contact identifiers separable from eligibility facts and allows the same profile to be used through web, SMS, or a case manager.

## RAG service integration

If the teammate's RAG backend remains a separate FastAPI service, create a replaceable port such as:

```python
class ConversationInterpreter(Protocol):
    def classify_need(self, text: str) -> Intent: ...
    def explain(self, approved_context: dict, language: str) -> str: ...
```

Then implement an HTTP adapter that calls the RAG service. The SANDI domain does not import BGE-M3, Qwen, Ollama, or any model package.

## Deployment recommendation

For the first integrated demo:

1. Keep this app as the system of record for profiles, rules, assessments, providers, and referrals.
2. Run the RAG backend separately.
3. Add an internal HTTP adapter between them.
4. Add Twilio (or another SMS gateway) only as an inbound/outbound transport adapter.
5. Later, if the combined codebase becomes stable, decide whether to deploy them together; do not merge boundaries just because they share a repository.

## Integration tests to require

- Same profile answers through web and SMS produce identical assessment statuses.
- RAG cannot override a deterministic result.
- Unknown/skip semantics are preserved through SMS.
- Provider source IDs returned by RAG must exist in the SANDI catalog.
- SMS retries are idempotent so a duplicate webhook does not create duplicate answers/referrals.
