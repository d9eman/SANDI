# Version 3 code and flow guide

## Why the same organization appeared twice

The original cards were generated one row per **service**, not one row per organization. The underlying structure was correct:

```text
Provider/organization
  ├── locator service
  └── application-assistance service
```

The presentation was confusing because both service cards displayed the organization name as the main title. Version 3 preserves the normalized model and adds `services.journey_stage` so the UI can separate the cards by purpose.

## Public route: food first

```text
GET /food-now
  -> public_routes.food_now()
  -> ResourceService.find_food(journey_stage="immediate_food")
  -> SqliteResourceRepository.search_food()
  -> food_now.html
```

The page shows provider-owned locator maps. It does not create a profile. A random `VIS-...` browser-session ID is used for aggregate tracking.

## External handoff tracking

```text
GET /go/{service_id}
  -> ResourceService.record_open()
  -> validate an http/https destination
  -> insert resource_interactions(action="open")
  -> redirect to the provider-owned URL
```

The application never treats the click as completed service. The user can separately report `yes`, `no`, or `not_yet` through `POST /resource-feedback`.

## Optional profile and second step

```text
POST /start
  -> create guest profile
  -> save each answer independently
  -> /p/{profile_id}/resources       immediate maps
  -> /p/{profile_id}/help            applications/navigation
  -> /p/{profile_id}/questions       deterministic screening
  -> /p/{profile_id}/referrals       closed-loop tickets
```

## Relevant code

| Responsibility | File |
|---|---|
| Public routes and stage separation | `app/presentation/web/public_routes.py` |
| Resource use cases and handoff tracking | `app/application/resource_service.py` |
| Repository interface | `app/ports/repositories.py` |
| SQLite catalog/search/interaction adapter | `app/adapters/sqlite/repositories.py` |
| Tables and relationships | `app/adapters/sqlite/schema.sql` |
| Additive v2→v3 migration | `app/db.py` |
| Public food page | `app/presentation/web/templates/food_now.html` |
| Profile food maps | `app/presentation/web/templates/resources.html` |
| Applications/navigation | `app/presentation/web/templates/more_help.html` |
| Provider entry form | `app/presentation/web/templates/provider_form.html` |
| Seed/provider records | `config/provider_catalog.csv` |
| Import format | `config/provider_import_template.csv` |

## Adding the coworkers’ community map

Find `prov_sandi_community_map` in `config/provider_catalog.csv` and update:

```text
website=<approved map URL>
source_url=<approved map/data documentation URL>
public_visibility=PUBLIC
data_quality_status=partner_supplied or verified
partner_status=active_partner
last_verified_at=<ISO timestamp>
```

Restart the app. Stable IDs cause the row to update rather than duplicate.

## Adding map pins owned by SANDI

Import one row per service location with:

```text
provider_id, service_id, location_id,
address, city, state, zip_code,
latitude, longitude,
hours_text, schedule_exceptions,
last_verified_at, data_quality_status
```

Coordinates are stored separately from the provider name and service rules, so adding or moving a location does not require changing eligibility code.
