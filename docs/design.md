# Design

A white editorial canvas, near-black type, hairline borders and one violet accent used only as a glow.

## Tokens

All values live in `web/src/theme/tokens.css`.

| Token | Value | Use |
| --- | --- | --- |
| `--color-press-black` | #0a0a0a | Primary buttons, headings |
| `--color-paper-white` | #ffffff | Canvas, page sheets, cards |
| `--color-newsprint` | #f3f3f3 | Inputs at rest, skeletons, table flags |
| `--color-graphite` | #666666 | Helper text, page labels, block metadata |
| `--color-ink-violet` | #19154e | Links and outlined actions |
| `--color-electric-violet` | #1100ff | Drag glow and focus ring only, never text or fills |
| `--color-carbon` | #000000 | 1px hairline borders |

## Type

- Display: Cormorant Garamond Light 300, -0.02em. Hero 80px, page titles 52px, section titles 32px.
- UI: Inter 400, 500 and 600. Body 16px, labels 15px, buttons 600.

## Shape

- Radius: 8px buttons, 16px block cards, 24px page sheets, 40px type tags.
- Shadow `rgba(0,0,0,0.1) 0 1px 1px, rgba(0,0,0,0.05) 0 2px 4px` on primary buttons and popovers only.
- The lifted block while dragging gets `rgba(17,0,255,0.15) 0 0 40px`. It is the only place color appears.

## Rules

- Plain text labels instead of icons.
- No hover animations. Skeleton pulses stop under reduced motion.
- Layouts collapse to one column under 900px and keep a 16px gutter on phones.
