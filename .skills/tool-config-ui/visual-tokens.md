# Tool Config UI Visual Tokens

These tokens guide stable, serious tool interfaces for SpecOS. Prefer mapping them to existing CSS variables or Tailwind utilities instead of adding dependencies.

## Color Roles

- Canvas: `#F7F8FB` for app background.
- Surface: `#FFFFFF` for cards and forms.
- Surface muted: `#F2F4F7` for code blocks, disabled panels, and table headers.
- Border: `#D9DEE7` for default separation.
- Border strong: `#B8C0CC` for focused or selected containers.
- Text strong: `#111827` for headings and primary values.
- Text default: `#374151` for body copy.
- Text muted: `#6B7280` for help text and metadata.
- Primary: `#2563EB` for the single main action.
- Primary soft: `#EFF6FF` for selected rows or info callouts.
- Success: `#15803D` with soft background `#ECFDF3`.
- Warning: `#B45309` with soft background `#FFFBEB`.
- Danger: `#B42318` with soft background `#FEF3F2`.
- Code accent: `#4F46E5` for schema, diff, or config previews.

## Typography

- Page title: 28-32px, 700 weight, tight line height.
- Section title: 18-20px, 650-700 weight.
- Field label: 13-14px, 600 weight.
- Body: 14-16px, 400-500 weight.
- Metadata/help: 12-13px, 400-500 weight.
- Monospace preview: 12-13px, regular, high contrast.

## Spacing

- Page padding: 24px mobile, 32px desktop.
- Section gap: 24px.
- Card padding: 16px compact, 20-24px normal.
- Field vertical gap: 8px within field, 16px between fields.
- Button group gap: 8-12px.
- Table cell padding: 12px vertical, 16px horizontal.

## Radius And Shadow

- Small controls: 8px radius.
- Cards and panels: 14-16px radius.
- Modals: 18-20px radius.
- Default shadow: subtle, low blur; prefer borders for structure.
- Critical panels: no heavy shadow; use left accent border and danger background.

## Layout

- Use a two-column layout only when side information is persistent and useful.
- Keep the main edit column between 720px and 920px for readable forms.
- Use right rail for validation, metadata, preview, or audit trail.
- Collapse right rail below the editor on narrow screens.
- Sticky footer/action bar is acceptable for long configuration forms.

## Interaction States

- Focus ring: visible blue ring with sufficient contrast.
- Disabled: reduce contrast and include reason text when action is important.
- Hover: subtle border or background change; avoid motion-heavy effects.
- Loading: button text changes to the action in progress, such as `Validating...`.
- Error: place message close to source and repeat cross-field issues in validation panel.
