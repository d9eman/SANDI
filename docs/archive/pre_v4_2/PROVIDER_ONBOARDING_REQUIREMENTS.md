# Provider onboarding requirements

This checklist distinguishes a public link, a warm handoff, and a direct SANDI referral. A provider does not need to supply every field before SANDI can show an official public link, but SANDI must not imply a direct partnership until the provider approves the workflow.

## Level 1 — public link or map

Minimum information:

- public/display organization name
- legal name, when different
- service name and plain-language purpose
- official public URL or phone number
- service area
- source organization and source URL
- date checked and person responsible for rechecking
- whether the information is a locator, application, information page, or direct service
- public-use permission or confirmation that linking is allowed

SANDI can record that the link was opened and ask whether it helped. It cannot know whether service was received unless the person reports back.

## Level 2 — verified site listing or warm referral

Everything in Level 1, plus:

- stable provider, service, and location IDs
- physical address and map coordinates
- recurring hours and all known exceptions/holiday closures
- appointment, walk-in, pickup, delivery, or mobile-distribution method
- service area and travel restrictions
- languages and accessibility
- food/service type
- eligibility summary in plain language
- identification, registration, documentation, and household-information requirements
- supply-limited or call-first status
- contact route for client questions
- operational owner who can correct the record
- verification frequency
- approved minimal referral summary and consent language
- process for correcting an incorrect handoff

SANDI may send a user to the right intake channel and track a warm handoff, but the user may still need to repeat information on the provider’s form.

## Level 3 — direct SANDI referral

Everything in Levels 1–2, plus a written operational agreement covering:

- provider acceptance of SANDI tickets
- exact data fields the provider needs
- which fields SANDI may prefill
- secure delivery method: API, provider portal, encrypted file, or approved email workflow
- provider account ownership and role permissions
- response-time expectation and escalation contact
- accepted, waitlisted, declined, scheduled, delivered, and closed status definitions
- structured decline and failure reasons
- private/public availability rules
- capacity and schedule update process
- duplicate-referral handling
- consent, privacy notice, retention, deletion, audit, and incident-response terms
- test environment and test cases
- outcome confirmation and data-sharing limits

Only after this level should `referral_enabled` be set to `true`.

## Level 4 — direct application or bidirectional integration

For an application to be completed in SANDI and transferred without re-entry, also collect:

- authoritative application schema and field definitions
- required/optional/conditionally required fields
- validation rules and error messages
- document requirements and accepted formats
- identity verification requirements
- eligibility authority and legal disclaimers
- API/export specifications and authentication method
- sandbox credentials
- consent language for transmission
- submission receipt/case ID behavior
- status webhooks or polling method
- resubmission/correction process
- record-retention and system-of-record boundary

Government eligibility systems remain the official decision-makers. SANDI should prefill and hand off only through an approved integration.

## Mapping fields to code

- Organization identity: `providers`
- Service purpose and journey stage: `services`
- Site, schedule, accessibility, and coordinates: `service_locations`
- Current capacity/status: `availability_snapshots`
- User handoff and feedback: `resource_interactions`
- Direct follow-up: `referral_tickets` and `ticket_events`

The CSV schema is in `config/provider_import_template.csv`; the web form is `app/presentation/web/templates/provider_form.html`.
