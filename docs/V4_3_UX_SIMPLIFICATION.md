# v4.3 UX simplification and gamification

## Design goal

A person should see only the next useful action. Details remain available, but they should not compete with the main message.

## Team feedback translated into product changes

### 1. Timeline + progress
The eligibility flow uses a shared four-step strip:

`Profile → Answer → Match → Connect`

The adaptive questionnaire also shows useful answers saved, currently useful questions remaining, and a progress bar. Because the survey is adaptive, SANDI does not pretend there is a fixed question count.

### 2. Gamification without coercion
User-facing rewards are process feedback, not points for disclosure:

- “Saved” confirmation after an answer
- progress movement
- a star/milestone when a program becomes actionable
- visible checkmarks for completed stages

Providers receive a data-readiness score based on listing completeness/freshness. It does **not** score case volume, denial rates, or worker productivity.

### 3. Results progressive disclosure
The results page shows:

1. counts of strong and possible matches;
2. the strongest/easiest programs first;
3. an application/action button;
4. missing questions when relevant;
5. “Why did I get this result?” only when expanded;
6. official source metadata one level deeper.

### 4. Mobile-first simplification
- two primary homepage choices;
- full-width tap targets;
- tap-card answers instead of dense radio lists;
- one-column result/action layouts on small screens;
- provider/staff links moved behind a “Team” menu on desktop and removed from the primary mobile navigation.

The interface does not rely on swipe gestures because accidental swipes can skip sensitive questions and reduce accessibility. The tap cards provide the same fast/mobile feeling while remaining keyboard and screen-reader compatible.

### 5. Food location
With browser coordinates, SANDI now selects at most five verified direct sites. It tries a 1-mile radius first, then 5 miles, then 15 miles only if no closer verified site exists. Provider-owned countywide maps remain available for the full live network.

A complementary SD Heart/team map can be added later through the existing provider/resource adapter once its approved URL/feed, ownership, categories, and update policy are known.

### 6. Disability, SSI, veteran, foster-care context
- `disability` already exists and is used only where a current rule needs it.
- `current_benefits` already supports SSI/SSP.
- `veteran_status` and `foster_care_history` are now canonical question definitions, but the adaptive planner does not ask them until an approved active rule references them.
- criminal-background data is deliberately not collected without a verified requirement.

### 7. Attachments
The optional vault now offers clearer document categories: identity, benefit/SSI letter, income, veteran, foster-care, residency, and other photo/document. Uploaded files are still optional and are not automatically visible to providers.

### 8. Provider experience
The provider dashboard now starts with a data-readiness score and the next missing detail. Service editing and referral state forms remain expandable instead of dominating the page.

The score rewards source, freshness, contact, location, hours, eligibility, language, accessibility, and availability completeness. It is a private workflow aid—not a public leaderboard.

### 9. Provider client summary / future AI
The current provider queue shows a deterministic minimum snapshot: need, urgency, ZIP, service, and ticket state. It does not expose the user's full profile or document vault.

A future RAG/AI summarizer should sit behind an application port and summarize only provider-authorized fields after consent. The deterministic snapshot is the safe fallback and should remain available even if the AI service is unavailable.
