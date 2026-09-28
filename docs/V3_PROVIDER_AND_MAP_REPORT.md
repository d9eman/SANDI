# SANDI v3 provider and map decision

## What caused the duplicate-looking cards

The catalog stores one organization with multiple services. V2 rendered one card per service and repeated the organization name, making locator and application-assistance services look like duplicate providers. The data relationship was correct; the presentation was not clear enough.

V3 separates:

- immediate food maps and direct food-finding information,
- applications and navigation,
- direct provider referrals.

## Provider naming

The public display name is **San Diego Food Bank**. The legal name is stored as **Jacobs & Cushman San Diego Food Bank**. They are not two separate food banks.

## Current map prototype

The no-profile `/food-now` page accepts ZIP, city, address, or optional browser location and opens:

- Feeding San Diego Find Food map,
- San Diego Food Bank GPS Food Locator,
- verified public food guides and direct-site pages.

The team food/bathroom map has a restricted placeholder record. It becomes public by adding its approved URL, data owner, last-verified date, and update process to `config/provider_catalog.csv`.

## Why SANDI does not copy every distribution pin yet

The reviewed 211-derived dataset is useful as a seed, but most records have one or more freshness or quality flags. Static copying would create a false claim of current availability. V3 therefore supports partner CSV imports and map coordinates while keeping unverified records out of the public experience.

## Recommended provider order

1. Feeding San Diego and San Diego Food Bank site/network verification.
2. Salvation Army and San Diego Rescue Mission public routes, then partner-approved direct services.
3. High-volume/specialized groups: Serving Seniors, Meals on Wheels, Mama's Kitchen, Interfaith Community Services, Catholic Charities, San Ysidro Health.
4. Grouped site imports by service type and geography.
5. Long-tail one-record providers after core workflows are stable.
