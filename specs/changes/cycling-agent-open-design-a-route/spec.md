# cycling-agent/open-design-a-route Spec

## Meta

- Domain: `cycling-agent`
- Feature: `open-design-a-route`
- Source Draft: `spec-draft/cycling-agent-open-design-a-route.md`

## Goal

Replace the current planner-first frontend with a lifestyle-led Open Design A-route experience while preserving existing URLs and introducing experience/content orchestration APIs that sit in front of the current planning capability stack.

## System Flow

1. Frontend loads homepage composition from `GET /api/v1/experience/home`.
2. User submits a short natural-language request to the companion planner.
3. System either returns a clarification prompt or generates a persisted result through the existing planning stack.
4. Frontend loads editorialized result or route detail payloads from new experience endpoints.
5. Admin reads and updates homepage/result-supporting content through a single experience-content contract.

## API Contract

- `GET /api/v1/experience/home`
- `POST /api/v1/experience/companion/plan`
- `GET /api/v1/experience/results/{request_no}`
- `GET /api/v1/experience/routes/{route_code}`
- `GET /api/v1/profile/lifestyle`
- `PUT /api/v1/profile/lifestyle`
- `GET /api/v1/admin/experience-content`
- `PUT /api/v1/admin/experience-content`

## Data Model

- `ExperienceContent`
- `LifestyleProfile`
- `ExperienceHomePayload`
- `ExperienceCompanionResponse`
- `ExperienceResultPayload`
- `ExperienceRouteDetailPayload`

## Rules

- Homepage, result page, route detail, profile page, and admin must all expose empty/loading/success/failure states.
- Existing frontend route URLs stay unchanged.
- Tailwind CSS becomes the primary frontend styling system.
- Existing planning, route, weather, and risk capabilities remain reusable internal services.
- Old admin catalog endpoints remain available for compatibility but are no longer the primary user-facing admin information architecture.

## Errors

- `experience-content-missing`
- `experience-home-unavailable`
- `experience-companion-failed`
- `experience-result-not-found`
- `experience-route-not-found`
- `lifestyle-profile-save-failed`

## Security

- Admin content endpoints remain under `/api/v1/admin/*`.
- User lifestyle profile stays scoped to the default local user profile model for this MVP.

## Observability

- Log companion request status: clarification vs planned vs failure.
- Log content admin saves.
- Preserve existing planning persistence for generated result payloads.
