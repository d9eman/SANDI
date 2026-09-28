# SANDI County Desk Aids Review and Food-MVP Implementation Plan

**Prepared for team review — August 2026**

## Executive conclusion

The County Desk Aids contain a large amount of program-specific procedure, but the information needed from a person is much smaller and highly reusable. Across the food and public-benefit materials, most screening begins from the same shared facts: location, food household, age/life stage, current benefits, income, expenses/resources, and a limited set of conditional flags. SANDI should therefore collect a shared profile once and open small conditional branches only when a rule actually requires them.

The right first production sequence remains: **immediate food navigation → CalFresh basic and expedited pre-screen → WIC and Restaurant Meals routing → verified direct-provider sites → later student/work/noncitizen and multi-program branches.**

## What was reviewed

- 47 files in the County Desk Aids folder: 46 PDFs totaling 2,276 pages plus one HTML workflow.
- All stand-alone flowcharts/tables were visually checked, including assistance standards, IRT, MCE, SUA, student, and noncitizen aids.
- The 63-page scanned CAPI guide was reviewed as page images because its text layer was incomplete.
- The SANDI partner workbook, Food/CalFresh/CalSAWS overview, system-design document, and ZIP Launchpad draft were used to connect the policy material to the intended product.

The folder is primarily an **eligibility and CalSAWS training library**, not a complete current provider directory. This matters: it can guide questions and workflow, but it cannot safely supply every pantry, meal site, schedule, or opening.

## Main groupings and overlap

| Group | Shared purpose and questions | Programs/services affected | MVP decision |
|---|---|---|---|
| Immediate food access | Need, urgency, ZIP/area, mobility/language/access needs | Food locators, pantries, meal programs, navigation | Show first; no eligibility barrier |
| Core benefit intake | Food household size, county residence, gross income | CalFresh and later GR/CalWORKs/Medi-Cal | Collect once and reuse |
| Crisis/expedited | Income now, liquid resources, shelter/utilities, migrant/seasonal farmworker status | Expedited CalFresh | Ask after immediate resources |
| Family/life stage | Age, pregnancy/recent pregnancy, child under five, disability, housing status, current CalFresh | WIC, Restaurant Meals, later deductions/work routes | High value because few questions open several paths |
| Student branch | Half-time enrollment, majority meal plan, student exceptions | CalFresh student rule | Ask only after student trigger |
| Work/activity branch | Age range, dependent child, pregnancy, fitness, work/volunteer/training hours, exemptions | ABAWD/work registration, CFET, Employment Services | Phase 2; current 2026 rules require careful versioning |
| Immigration/sponsor branch | Immigration category, entry/status dates, sponsor/deeming, specialist verification | CalFresh/CFAP, RCA, CAPI | High sensitivity; specialist route, not automatic denial |
| Post-enrollment operations | Verification, journals, imaging, SAR, mid-period changes, recertification | County staff and existing recipients | Do not put in first intake |
| Provider/resource data | Organization, service, location, hours, requirements, provenance, update ownership, availability | All provider services | Separate stable catalog from availability snapshots |

### What is repeated most often

1. **Household and relationship structure.** CalFresh defines a food household around living together and purchasing/preparing meals together, with mandatory groupings such as spouses and many children under 22 living with parents.
2. **County residence and identity.** A fixed address is not required; applicant identity must be verifiable, but a specific photo ID is not universally required.
3. **Income and timing.** Programs repeatedly need amount, source, frequency, and expected changes. The first demo should ask only an estimate, then leave official budgeting to the responsible agency.
4. **Age, children, pregnancy, and disability.** These facts activate WIC, Restaurant Meals, deductions, student exceptions, and later work-rule exemptions.
5. **Current benefits.** Existing participation can change routing or reduce duplicate questions.

### What should stay program-specific

- Student exemptions and majority meal-plan rules.
- Work registration/ABAWD/CFET details.
- Citizenship, noncitizen funding, sponsor, and deeming rules.
- CAPI, RCA, General Relief, Child Care, and CalWORKs-specific calculations.
- Provider-specific requirements, schedules, capacity, and referral consent.

## Recommended shared question spine

| Stage | Questions | Why this is efficient |
|---|---|---|
| 0. Help now | Need, danger, urgency | Routes immediate help without an account |
| 1. Practical routing | ZIP/area, language, accessibility, delivery/travel needs | Finds usable options before screening |
| 2. Reusable core | Food household size, approximate monthly gross income | Supports the largest CalFresh decision points |
| 3. High-value flags | Current CalFresh, age, housing status, disability, pregnancy/recent pregnancy, child under five | Opens WIC/RMP and prepares later programs |
| 4. Conditional student | Half-time status; only then meal plan and exemption checklist | Avoids asking non-students irrelevant questions |
| 5. Crisis branch | Liquid resources, shelter/utilities, migrant/seasonal farmworker | Screens expedited service only when useful |
| 6. Official action | Identity, SSN/application status, verification checklist, documents | Ask only after the user chooses to apply or share a referral |

Unknown and skipped answers must remain stored as explicit states. They should create a “needs information” route, never erase progress or block direct food.

## Services to focus on first

### 1. Live food locators and navigation
They provide immediate value with almost no screening. The v2 demo includes source-linked routes for Feeding San Diego, the San Diego Food Bank, the San Diego Hunger Coalition, and 211 San Diego.

### 2. CalFresh basic and expedited screening
CalFresh has the broadest direct food-benefit impact and the strongest set of local desk aids. The demo uses the 10/2025 assistance standards period, a conditional student branch, and the three expedited-service indicators. It remains a pre-screen; the County makes the official determination.

### 3. County and application-assistance channels
BenefitsCal, County HHSA/Family Resource Centers, 211 enrollment help, Feeding San Diego/San Diego Food Bank outreach, and GetCalFresh guidance should be presented as handoff routes rather than duplicated application systems.

### 4. WIC and Restaurant Meals
These pathways add substantial value using facts already collected for the shared profile. They should remain “may qualify / route” results rather than approvals.

### 5. Direct provider sites and closed-loop tickets
This is SANDI’s key differentiator, but it requires partner-approved site records and agreement to receive referrals. Direct tickets should not be enabled merely because an organization appears in a public directory.

## Provider-data finding and current catalog

The source materials identify organizations and locator systems but do not provide a complete, current list of individual food-distribution sites. The v2 catalog therefore contains:

**Public source-linked routes:** Feeding San Diego; San Diego Food Bank; San Diego Hunger Coalition; 211 San Diego; BenefitsCal; GetCalFresh; County of San Diego HHSA/Family Resource Centers.

**Restricted partner candidates pending verification:** The Salvation Army (San Diego) and San Diego Rescue Mission.

The partner candidates are visible in the provider portal but hidden from public results until their organization validates sites, hours, eligibility notes, and referral participation.

## Phased game plan

### Group 1 — navigation and benefits routes (now)
Load the public locator/application routes, source dates, requirement group, and service mode. Do not claim live inventory.

### Group 2 — 5–10 direct food partners
Prioritize partners already named by the team. Ask each for a small standard export: stable IDs, service/location, schedule, closure exceptions, languages, access, requirement summary, ID/document notes, update owner, and public/restricted availability.

### Group 3 — site-level imports
Import pantry, meal, day-center, and mobile-distribution sites in organization-sized batches. Validate duplicates, source ownership, and last-verified dates before public display.

### Group 4 — conditional CalFresh complexity
After policy-owner review, add current work/ABAWD support, immigration/CFAP specialist routing, full deduction guidance, and application-readiness checklists. Do not turn changing or sensitive rules into automatic denials.

### Group 5 — additional programs
Reuse the shared profile for General Relief, CalWORKs, Medi-Cal, Child Care, RCA, CAPI, and youth/housing services. Add each as an independent versioned rule module rather than expanding one giant form.

## Where to make changes in the code

| Change | File/location |
|---|---|
| Add/edit approved user questions | `config/questions.json` |
| Change eligibility logic or effective dates | `config/rules/*.json` |
| See how missing fields choose the next question | `app/application/screening_service.py` |
| See deterministic rule evaluation | `app/domain/eligibility.py` |
| See answer storage | `profile_answers` in `app/adapters/sqlite/schema.sql` and `SqliteProfileRepository.save_answer` |
| Add providers/services by file | `config/provider_catalog.csv` or `config/provider_import_template.csv` |
| Add providers through UI | `/provider/login` → Add provider/service or Import CSV |
| Inspect questions/rules without reading code | `/staff/questions` and `/staff/rules` |
| See one profile’s stored answer states and rule reasons | `/staff/profiles/{profile_id}` |

## Version 2 implementation decisions

- Replaced browser Basic Auth with form/session login pages and corrected the `.env.example` credential mismatch.
- Added a staff “question map” and “rule versions” trace.
- Added stage/group/source metadata to every question.
- Added conditional rule branches and a reusable sum comparison for expedited screening.
- Replaced fictional public resources with real source-linked organizations; fictional sites are retained only in a clearly labeled optional sample CSV.
- Added service mode, eligibility group, partner status, data quality, provenance, and referral opt-in fields.
- Added an additive migration so the v2 code can open a v1 SQLite database.

## Critical rule-governance note

The desk-aid set contains dated and sometimes superseded material. Current California and San Diego pages describe 2026 changes to noncitizen and work/community-engagement rules. Those branches should remain under specialist review until a named policy owner approves a dated rule version and regression tests. The application should automatically move overdue fixtures to **RULE UNDER REVIEW**.

## Delivered supporting files

- `SANDI_County_Desk_Aids_File_Inventory.csv` — all 47 files classified by program, purpose, and recommended phase.
- `SANDI_Shared_Question_Matrix.csv` — the actual v2 question catalog, order, programs affected, conditions, and sources.
- `SANDI_food_profile_demo_v2.zip` — drop-in updated prototype.
