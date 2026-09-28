# SANDI demo v3 changes

## User-flow correction

The original resource page mixed three different concepts:

1. an organization (`providers`),
2. a service owned by that organization (`services`), and
3. a location where that service is delivered (`service_locations`).

That is why **Feeding San Diego** and **San Diego Food Bank** could each appear twice. They were not duplicate organization records: each organization had one locator service and one CalFresh/application-assistance service. Version 3 keeps the same normalized data model but separates those services into user-journey stages.

- `immediate_food`: maps, locators, and open food-finding information
- `more_help`: applications, benefit navigation, and external assistance
- `direct_help`: partner-approved direct referrals and provider follow-up

## Public experience

- Added `/food-now`, which does not require a profile.
- Added optional browser geolocation; the browser only fills the search field after permission.
- Added tracked redirect route `/go/{service_id}`.
- Added anonymous outcome feedback after a public handoff.
- Kept immediate food maps separate from profile screening and application routes.
- Added `/p/{profile_id}/help` for the second step.

## Provider identity correction

The display name is now **San Diego Food Bank**. Its formal/legal organization name is stored separately as **Jacobs & Cushman San Diego Food Bank**. This prevents a legal name from looking like a separate provider.

## Provider onboarding

- Expanded the provider portal form to include legal name, journey stage, partner status, verification status, source, schedule exceptions, coordinates, service area, intake notes, and referral approval.
- New provider records default to restricted and under review.
- Added a restricted placeholder for the team’s food/bathroom community map.

## Analytics

- Added `resource_interactions` for searches, external-resource opens, and optional feedback.
- Staff dashboard now shows resource opens and reported outcomes.
- Tracking uses a random browser-session ID until a person chooses to create a profile.

## Compatibility

The update is additive. Existing profiles, answers, assessments, documents, and referral tickets remain valid. Stable provider/service/location IDs allow startup imports to update existing catalog rows.
