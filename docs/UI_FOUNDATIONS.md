# MKE UI Foundations

## Design ambition

Making Life Easier should feel energetic, trustworthy, modern, warm, and
distinctly useful. It must look polished on affordable Android devices, remain
clear outdoors, and make urgent transport or delivery actions effortless.

The visual identity combines orange and blue:

- Orange communicates movement, warmth, speed, and action.
- Blue communicates trust, safety, navigation, and financial confidence.
- Neutral surfaces keep the experience calm and premium.

The interface must not cover every screen in gradients or use orange and blue
with equal visual weight. Each screen has one dominant action and a controlled
accent.

## Core palette

### Brand orange

| Token | Value | Use |
| --- | --- | --- |
| `orange-50` | `#FFF7ED` | Warm tinted backgrounds |
| `orange-100` | `#FFEDD5` | Selected cards and badges |
| `orange-300` | `#FDBA74` | Decorative highlights |
| `orange-500` | `#FF8C00` | Core brand and primary actions |
| `orange-600` | `#E67E00` | Pressed and hover states |
| `orange-700` | `#B85F00` | Accessible text/icon accents |

### Trust blue

| Token | Value | Use |
| --- | --- | --- |
| `blue-50` | `#EFF6FF` | Informational backgrounds |
| `blue-100` | `#DBEAFE` | Selected navigation |
| `blue-400` | `#3B82F6` | Map and live-location accents |
| `blue-600` | `#155EEF` | Secondary actions and links |
| `blue-800` | `#173B67` | Headers and trusted surfaces |
| `blue-950` | `#0B1F3A` | Primary text and dark surfaces |

### Neutral and semantic colors

| Token | Value | Use |
| --- | --- | --- |
| `surface` | `#FFFFFF` | Primary surface |
| `canvas` | `#F7F9FC` | App background |
| `text` | `#101828` | Primary text |
| `muted` | `#667085` | Secondary text |
| `border` | `#E4E7EC` | Dividers and controls |
| `success` | `#12B76A` | Completed and verified |
| `warning` | `#F79009` | Attention required |
| `danger` | `#D92D20` | Destructive and emergency |

Semantic colors retain their meanings. Orange must not replace danger red or
success green.

## Signature gradient

The brand gradient is reserved for onboarding, launch moments, promotional
headers, and small identity details:

```text
linear-gradient(135deg, #FF8C00 0%, #FF6B35 42%, #155EEF 100%)
```

Operational screens, forms, maps, and payment confirmation use solid colors for
clarity and accessibility.

## Color roles

- Customer app primary action: orange.
- Driver app availability and navigation accents: blue.
- Operations dashboard navigation: deep blue.
- Active trip progress: orange moving toward blue at confirmed/secure stages.
- Wallet and verification surfaces: deep blue with restrained orange accents.
- Emergency actions: red, always visually separate from brand orange.

## Typography

Use a highly legible geometric sans-serif with broad language coverage.
Recommended starting family: **Inter** for interface text, with platform-native
fallbacks. Kiswahili and future local-language content must be tested before a
decorative brand typeface is introduced.

Type scale:

| Style | Size / line height | Weight |
| --- | --- | --- |
| Display | 32 / 38 | 700 |
| Title | 24 / 30 | 700 |
| Section | 20 / 26 | 600 |
| Body | 16 / 24 | 400 |
| Label | 14 / 20 | 600 |
| Caption | 12 / 16 | 500 |

Body text should not fall below 14px-equivalent sizing on mobile.

## Shape, spacing, and elevation

- Base spacing unit: 4.
- Common gaps: 8, 12, 16, 24, and 32.
- Buttons and inputs: 12–14 radius.
- Cards and bottom sheets: 16–24 radius.
- Touch targets: at least 48 × 48.
- Use thin neutral borders before shadows.
- Shadows are soft and sparse; map overlays may use stronger elevation.

## Motion

Motion communicates state rather than decorating every interaction:

- 120–180ms for taps and control feedback.
- 220–320ms for sheets, cards, and navigation.
- Driver approach and route progress should animate continuously but calmly.
- Respect reduced-motion preferences.
- Never delay emergency, payment, or confirmation actions for animation.

## Core screen composition

### Customer home

- Map or contextual service canvas.
- Friendly location-aware greeting.
- One prominent “Where are you going?” action.
- Service shortcuts beneath it: Ride, Send package, Shop, Stay, and More.
- Recent destinations and active requests appear before promotional content.

### Ride request

- Pickup and destination presented as one connected journey.
- Vehicle options use clear capacity, ETA, and total price.
- Orange confirms the ride; blue communicates location and safety details.
- Payment method and cancellation terms remain visible before confirmation.

### Active trip

- Map dominates.
- Driver identity, vehicle, ETA, safety tools, contact, and cancellation are
  reachable without scrolling.
- Status language is human: “David is 4 minutes away,” not “accepted.”

### Driver home

- Earnings and current status at a glance.
- Large online/offline control with unmistakable state.
- Incoming requests show pickup distance, estimated earnings, destination
  direction, and acceptance time.
- No distracting promotions while driving.

### Operations dashboard

- Dense but calm information hierarchy.
- Deep-blue navigation, neutral work surfaces, orange exception highlights.
- Tables provide filters, saved views, status badges, and clear audit history.

## Accessibility requirements

- Target WCAG 2.2 AA contrast.
- Do not communicate status with color alone.
- Support text scaling without clipping.
- Provide visible focus states and screen-reader labels.
- Test sunlight readability and low-quality displays.
- Design for one-handed mobile use and intermittent connectivity.

## Image and illustration direction

Use authentic Kenyan and East African environments, people, vehicles, shops,
guest houses, and streets. Avoid generic futuristic city imagery. Photography
should feel optimistic and natural; illustration should use simple geometry,
warm orange light, and confident blue structure.

## Design governance

Every production surface must use shared tokens and components. New colors,
spacing values, buttons, cards, or status treatments require a design-system
decision rather than screen-level invention.

The first UI implementation should produce:

1. Flutter theme tokens.
2. Buttons, fields, cards, sheets, navigation, badges, and feedback components.
3. Customer home and ride-booking prototype.
4. Driver home and incoming-request prototype.
5. Operations dashboard shell.
6. Light/dark and accessibility verification.
