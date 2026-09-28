# Adding providers and services

## Preferred method: CSV import

Copy `config/provider_import_template.csv`. Keep stable IDs:

```text
provider_id  — one organization
service_id   — one service/purpose
location_id  — one physical/online service location
```

An organization with a locator and application-help service should reuse the same `provider_id` and use different `service_id` values.

Key v3 columns:

```text
provider_name
legal_name
service_name
journey_stage
public_visibility
service_public_visibility
service_mode
eligibility_group
referral_enabled
location_name
address
zip_code
latitude
longitude
hours_text
schedule_exceptions
eligibility_summary
documentation_notes
source_url
last_verified_at
data_quality_status
availability_status
availability_visibility
```

Import through `/provider/import` or:

```powershell
python scripts/import_providers.py path\to\providers.csv
```

## Provider form

`/provider/new` is best for one test record. It generates new IDs. For updating an existing organization or adding another service to it, CSV is safer because it lets you reuse the provider ID.

## Public-link first

A public official map or application page can be loaded before a direct referral agreement. Use:

```text
service_public_visibility=PUBLIC
referral_enabled=false
```

## Direct referral later

Only after provider approval use:

```text
journey_stage=direct_help
service_public_visibility=PUBLIC
referral_enabled=true
```

The provider must have approved the data fields, consent, secure delivery method, response owner, status workflow, availability process, retention, and incident procedure.
