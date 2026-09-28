# SANDI demo v4 changes

## Problems corrected

### Silent browser-location button

The old control could fail without visible feedback. The v4 JavaScript verifies that the form exists, checks secure-context and browser support, shows permission/progress/errors in an ARIA live region, writes temporary latitude/longitude fields, and submits the form after a successful lookup.

### Immediate food and eligibility were still intertwined

The profile path no longer routes through food maps. The home page has two explicit choices. The food finder can invite profile creation afterward, while direct profile creation starts the eligibility survey immediately.

### ZIP was not reused reliably

Anonymous food-search context is stored temporarily in the session. When the user intentionally creates a profile from the food page, the normalized ZIP and urgency become saved profile answers. Direct profile creation asks for ZIP as the first useful eligibility question.

### Broad maps and specific sites looked duplicated

Countywide maps and one physical site now appear in separate sections. A direct site appears only when its ZIP matches the search or when browser coordinates place it within the configured radius. The North County pantry therefore does not appear for a Downtown ZIP.

### Results were a wall of text

Results are ranked and grouped:

- available/strong matches first;
- possible or incomplete matches second;
- non-matches collapsed by default.

Requirement-by-requirement detail is also collapsed until requested.

### Failure explanations were not actionable

Each rule predicate can now provide:

- human-readable requirement;
- expected value or condition;
- actual user value;
- pass/fail/unknown explanation;
- conditional branch label.

For example, an expedited-income failure can show “Program expects: less than $150” and “Your answer: $500.”

### No clear action from results

Program rules now contain approved action metadata. Result cards resolve those actions to current catalog services, creating tracked handoffs to official pages.

### Too many unnecessary questions

The evaluator short-circuits missing questions that can no longer change a known failure or a satisfied `any` branch. The planner scores the remaining fields using program priority, access score, cross-program impact, question sensitivity, and explicit dependencies.

### Requirements/questions were difficult to share

A live CSV is generated from the same active JSON rules and questions used by the app:

```text
/staff/eligibility-matrix.csv
```

The command-line exporter writes the same matrix to `docs/`.
