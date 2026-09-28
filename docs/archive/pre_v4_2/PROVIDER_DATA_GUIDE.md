# Provider and service data guide — v3

## Record hierarchy

One organization can have many services; one service can have one or more locations; availability is a time-stamped snapshot.

- `providers`: organization identity, including public display name and optional legal name
- `services`: purpose, user-journey stage, requirement group, service visibility, referral capability
- `service_locations`: address, map coordinates, service area, hours, exceptions, accessibility
- `availability_snapshots`: current status, visibility, source, observed time
- `resource_interactions`: anonymous search/open/feedback events

This explains why Feeding San Diego can own both a **Find Food map** service and a **CalFresh application-help** service without being duplicated as an organization.

## Journey stages

- `immediate_food`: locator maps, direct sites, and open food-finding information
- `more_help`: applications, benefits navigation, and application support
- `direct_help`: provider-approved referrals and follow-up

## Visibility

Organization visibility and service visibility are separate. A known public organization can have a public information page and a restricted direct-referral service.

- `PUBLIC`
- `RESTRICTED`
- `NOT_SHARED`

## Safe rollout

1. Keep official locator/application links public.
2. Import direct sites only from provider-approved records or a clearly labeled unverified staging file.
3. Require source, last-verified date, service/location IDs, and an operational owner.
4. Add coordinates for SANDI-owned map pins.
5. Set `service_public_visibility=PUBLIC` only after the service is safe to display.
6. Set `referral_enabled=true` only after the provider approves the intake fields, consent, delivery channel, response workflow, and outcome states.
7. Add new availability rows instead of overwriting stable service descriptions.

See `PROVIDER_ONBOARDING_REQUIREMENTS.md` for the complete integration checklist.
