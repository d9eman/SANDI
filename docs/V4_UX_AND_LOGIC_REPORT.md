# SANDI v4 UX and logic correction report

## Design decision

Immediate food navigation and reusable eligibility screening are related but distinct tasks. The v4 interface lets a person complete either task without being forced through the other. Context is reused only when the person explicitly moves from food navigation into profile creation.

## Information shown progressively

### Immediate food page

Shown immediately:

- location input;
- urgency;
- official provider maps;
- truly location-matched direct sites;
- one optional profile invitation.

Hidden unless requested:

- secondary food guides;
- feedback form details;
- profile/benefit questions.

### Eligibility survey

Shown immediately:

- one approved question;
- why it matters;
- save/unknown/skip controls;
- current progress;
- newly actionable match notification.

Not shown until results are requested:

- complete program cards;
- full rule reasons;
- source/version details;
- non-matching programs.

### Results

Shown immediately:

- strongest/easiest matches;
- official next action;
- missing answer chips when relevant.

Collapsed:

- detailed requirement comparisons;
- source and rule dates;
- non-matching programs.

## Data reuse boundary

The anonymous food finder may keep a coarse ZIP and urgency in the session. If the user creates a profile from that page, those values are stored as ordinary profile answers. Street address and browser coordinates are not copied to the profile.

## Ranking boundary

Ranking is deterministic and configured in rule metadata. It is not an AI recommendation score. Status comes first, then the program’s approved display priority and access score.

## Completion boundary

Opening a provider link records a handoff. It does not record successful service. Completion requires user feedback, a provider-managed referral state, or a future approved integration.
