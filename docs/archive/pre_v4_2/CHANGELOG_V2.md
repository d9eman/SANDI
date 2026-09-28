# SANDI food-profile demo v2 changes

- Replaced browser HTTP Basic authentication with clear provider/staff login forms.
- Matched `.env.example` credentials to the README and added restart guidance.
- Added staff question and rule trace screens.
- Added question metadata for stage, grouping, purpose, condition, and source.
- Added conditional `if_then` and sum-comparison rule nodes.
- Replaced fictional default public resources with real source-linked navigation/application organizations.
- Preserved fictional direct sites only as an explicitly named optional sample CSV.
- Extended provider records with organization type, partner status, service mode, requirement group, and referral opt-in.
- Added additive SQLite migration logic for v1 databases.
- Added source/last-verified information and external-resource behavior to public cards.
- Added current CalFresh basic, expedited, student-conditional, WIC, and Restaurant Meals routing fixtures.
