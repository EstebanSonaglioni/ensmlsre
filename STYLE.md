# STYLE.md — Seller Dashboard (dark)

## Feel
Same Savia layout, dark SaaS: deep charcoal canvas, elevated cards, emerald accents. Calm, high contrast for data, never neon.

## Color
| Token | Hex (approx) | Use |
| --- | --- | --- |
| `primary` | `#10B981` | Primary buttons, active nav, links |
| `primary-muted` | `#059669` | Hover / pressed |
| `primary-foreground` | `#04140F` | Text on solid primary buttons |
| `accent` / success | `#34D399` | Positive deltas, money highlights |
| `danger` | `#F87171` | Negative deltas, errors |
| `warning` | `#FBBF24` | Attention, low stock, “Por preparar” |
| `info` | `#60A5FA` | “Enviado” / info |
| `background` | `#0B0F0E` | App canvas |
| `sidebar` | `#111816` | Sidebar |
| `card` | `#151C1A` | Cards, dropdowns |
| `card-hover` | `#1B2421` | Row / card hover |
| `border` | `#2A3330` | Hairlines |
| `text` | `#F3F4F6` | Titles, body |
| `muted` | `#9CA3AF` | Labels, dates, placeholders |
| `ring` | `#10B98155` | Focus rings |

Status pills: translucent tint (`color` @ ~15–20% alpha) + brighter text of the same hue.

## Typography
- Font: Inter (or system UI sans).
- Page title: 24–28px semibold, `text`.
- Section titles: 16–18px semibold.
- Body / table: 14px; meta 12–13px `muted`.
- Numbers: tabular; currency right-aligned; prefer `accent` for money on KPIs.

## Layout
- Unchanged vs light: sidebar ~240px, top bar, 4 KPIs → chart+alerts → orders+products.
- Padding 24px; gaps 16–24px; spacing scale of 8px.
- Sidebar slightly darker than cards so content “floats”.

## Components
- **Cards:** `card` fill, 8–12px radius, 1px `border`, shadow optional (`0 1px 0 #0006`).
- **Primary button:** solid `primary`, `primary-foreground` text; hover `primary-muted`.
- **Secondary:** `border` + transparent / `card-hover` fill; `text`.
- **Nav:** icon + label; active = soft green wash + `primary` text.
- **Search:** dark fill, `border`, pill; placeholder `muted`.
- **Tables:** no vertical rules; dividers `border`; hover `card-hover`; order IDs in `primary`.
- **Badges:** soft dark pills (tint + bright label).
- **Charts:** green main series + grey (`#6B7280`) comparison; grid lines very low-contrast (`#ffffff10`).
- **Icons:** outline Lucide, ~`muted` default; active `primary`.
- **Scrollbars / inputs:** match `border` / `card`; focus `ring`.

## Content patterns
- Same as light: greeting, range, export; KPI + delta; alerts; empty/loading/error on every panel.
- Deltas: `accent` up, `danger` down (avoid pure red/green only—keep labels).

## Do / Don’t
- Do: WCAG-ish contrast on `text`/`muted`; green accents sparingly.
- Don’t: pure `#000` blocks, glowing neon greens, light-theme gray text on dark, heavy white borders.

## Implementation (Next + Tailwind + shadcn)
- Define tokens under `.dark` in `globals.css`; set `className="dark"` on `html`.
- Map to shadcn CSS variables (`--background`, `--card`, `--primary`, …).
- Charts: Recharts with the green/grey series above; tooltip using `card` + `border`.