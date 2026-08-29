---
name: Vibrant CRM
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#434655'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#737686'
  outline-variant: '#c3c6d7'
  surface-tint: '#0053db'
  primary: '#004ac6'
  on-primary: '#ffffff'
  primary-container: '#2563eb'
  on-primary-container: '#eeefff'
  inverse-primary: '#b4c5ff'
  secondary: '#855300'
  on-secondary: '#ffffff'
  secondary-container: '#fea619'
  on-secondary-container: '#684000'
  tertiary: '#006242'
  on-tertiary: '#ffffff'
  tertiary-container: '#007d55'
  on-tertiary-container: '#bdffdb'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dbe1ff'
  primary-fixed-dim: '#b4c5ff'
  on-primary-fixed: '#00174b'
  on-primary-fixed-variant: '#003ea8'
  secondary-fixed: '#ffddb8'
  secondary-fixed-dim: '#ffb95f'
  on-secondary-fixed: '#2a1700'
  on-secondary-fixed-variant: '#653e00'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Manrope
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Manrope
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Manrope
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
  headline-lg-mobile:
    fontFamily: Manrope
    fontSize: 28px
    fontWeight: '700'
    lineHeight: 36px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin-mobile: 16px
  margin-tablet: 24px
---

## Brand & Style

The design system is engineered for high-velocity lead management, focusing on clarity, momentum, and confidence. It targets professional sales teams and small business owners who require a tool that feels both powerful and approachable.

The aesthetic follows a **Corporate / Modern** style with a leaning toward **Minimalism**. It prioritizes heavy whitespace to reduce cognitive load during complex data entry, paired with vibrant accent colors to guide the eye toward critical actions and lead statuses. The goal is to evoke a sense of reliability and optimism, transforming the often tedious task of CRM management into a premium, tactile experience.

## Colors

The color palette is functionally driven to provide immediate visual feedback on lead health. 

- **Primary (Blue):** Used for primary actions, navigation, and focus states. It represents stability and professionalism.
- **Secondary / Pending (Amber):** High-visibility color for leads requiring attention or in a transitional state.
- **Tertiary / Success (Green):** Indicates converted leads or positive milestones.
- **High-Priority (Red):** Reserved for overdue tasks, hot leads, or critical alerts.
- **Neutral (Slate/Gray):** Used for secondary text, borders, and inactive states to maintain a clean hierarchy without competing with status indicators.

## Typography

This design system utilizes a dual-font strategy to balance character with utility. **Manrope** is used for headlines to provide a modern, refined, and geometric feel that establishes a premium brand presence. **Inter** is used for all body text and UI labels to ensure maximum legibility and a systematic, functional appearance across dense lead lists.

Hierarchy is enforced through strict weight distribution: headlines use Semibold (600) and Bold (700), while labels use Medium (500) or Semibold (600) at smaller sizes to remain legible against colorful status backgrounds.

## Layout & Spacing

The system employs a **Fluid Grid** model optimized for mobile-first interaction. 

- **Grid:** A 4-column layout for mobile and 12-column layout for tablet.
- **Rhythm:** An 8pt linear scaling system (4, 8, 16, 24, 32) governs all padding and margins. 
- **Lead Lists:** Items should utilize a 16px horizontal margin (gutter) from the screen edge.
- **Touch Targets:** Minimum touch targets for interactive elements are 44x44px, regardless of the visual size of the icon or label.

## Elevation & Depth

To achieve a "premium feel," this design system uses **Ambient Shadows** and **Tonal Layers**. 

Depth is expressed through three primary levels:
1. **Level 0 (Surface):** The background layer, using a subtle off-white (`#F8FAFC`) to reduce glare.
2. **Level 1 (Cards):** Lead cards and list items use white backgrounds with a soft, diffused shadow (Y: 4px, Blur: 12px, Color: 4% Black) to appear slightly lifted.
3. **Level 2 (Modals/Action Sheets):** Floating elements use a more pronounced shadow (Y: 8px, Blur: 24px, Color: 8% Black) and a subtle 1px border (`#E2E8F0`) to ensure separation from the content below.

Avoid harsh outlines; use subtle tonal shifts in background colors to define content sections.

## Shapes

The shape language is consistently **Rounded**, reflecting a modern and approachable tool. 

- **Standard Elements:** Buttons, input fields, and small cards use a 0.5rem (8px) radius.
- **Large Containers:** Dashboard cards and modals use a 1rem (16px) radius (`rounded-lg`).
- **Status Chips:** Use a full pill-shape (999px) to distinguish them from interactive buttons.
- **Progress Bars:** Use rounded caps to maintain the soft aesthetic.

## Components

- **Lead Cards:** The primary container for information. Must include a title (headline-sm), a secondary descriptor (body-md), and a status chip. Top-right corner is reserved for "High-Priority" red dots or priority flags.
- **Status Chips:** High-contrast backgrounds with white text or low-opacity tinted backgrounds with high-contrast text. Use these for Success, Pending, and Priority states.
- **Buttons:**
    - *Primary:* Solid fill using Primary Blue, white text, 8px roundedness.
    - *Secondary:* Ghost style with Primary Blue border and text.
- **Input Fields:** 1px neutral border that transitions to Primary Blue on focus. Labels should be positioned above the field using `label-md`.
- **Lists:** Clean rows with 16px internal padding, separated by 1px dividers or subtle vertical spacing (8px) to utilize the card-lift effect.
- **Action Float:** A floating action button (FAB) for "New Lead" should be fixed at the bottom right, using the Primary Blue and a subtle shadow.