---
agent: agent
---
Improve the impact story file to match the content schema and taxonomies.

## Reference Files

- Schema: `src/schemas/content.schemas.ts` (defines `impactRolesSchema`)
- Impact Areas: `src/content/_taxonomies/impact-areas.yml`
- Contribution Types: `src/content/_taxonomies/contribution-types.yml`
- Organisations: `src/content/_taxonomies/organisations.yml`

## Required Front Matter Fields

1. **title** - Keep existing title
2. **description** - Concise summary of the engagement (one sentence)
3. **startYear** - Number (e.g., `2007` not `"2007"`)
4. **endYear** - Number, only if activity spans multiple years
5. **impactArea** - Array of strings from `impact-areas.yml` keys:
   - social-investment, foundation-practice, philanthropy, arts-culture
   - social-welfare, health-wellbeing, international-development, policy-development
6. **contributionType** - String from `contribution-types.yml` keys:
   - governance-leadership, strategic-advisory, policy-development, sector-building
   - thought-leadership, programme-delivery, financial-management
   - organizational-development, evaluation-research
7. **links** - Array of objects with `label`, `to`, and optional `description`

## Optional Fields

- **organisations** - Array of slugs matching keys in `organisations.yml`
- **summary** - Longer summary if needed

## Body Text

- Remove markdown bold formatting (`**text**`)
- Remove inline links (extracted to `links` array)
- Keep plain text description of the work
- End with a period

## Validation

Run `pnpm tsx scripts/validate-impact-stories.ts` to verify changes pass schema validation.