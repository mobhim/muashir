---
name: مؤشّر (Muashir)
description: A night-market study site in black, gold and cream, with glass panels and constant motion.
colors:
  night: "#050505"
  panel: "#14120c"
  gold: "#d9b24a"
  gold-hi: "#f4d98a"
  cream: "#f3ead3"
  up: "#46d39a"
  down: "#ff6b6b"
typography:
  display:
    fontFamily: "Alexandria, IBM Plex Sans Arabic, system-ui, sans-serif"
    fontSize: "clamp(2.5rem, 7.6vw, 6rem)"
    fontWeight: 800
    lineHeight: 1.22
    letterSpacing: "0em"
  heading:
    fontFamily: "Alexandria, IBM Plex Sans Arabic, system-ui, sans-serif"
    fontSize: "clamp(1.9rem, 4.6vw, 3.4rem)"
    fontWeight: 800
    lineHeight: 1.3
    letterSpacing: "0em"
  title:
    fontFamily: "Alexandria, IBM Plex Sans Arabic, system-ui, sans-serif"
    fontSize: "clamp(1.3rem, 2.4vw, 1.8rem)"
    fontWeight: 600
    lineHeight: 1.45
    letterSpacing: "0em"
  body:
    fontFamily: "IBM Plex Sans Arabic, Segoe UI, Tahoma, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.8
    letterSpacing: "0em"
  label:
    fontFamily: "IBM Plex Sans Arabic, Segoe UI, Tahoma, sans-serif"
    fontSize: "0.9rem"
    fontWeight: 500
    lineHeight: 1.6
    letterSpacing: "0em"
rounded:
  sm: "0.9rem"
  md: "1.1rem"
  lg: "1.4rem"
  pill: "999px"
spacing:
  gap: "1rem"
  card: "1.4rem"
  section: "clamp(4rem, 9vw, 7.5rem)"
components:
  glass-panel:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.cream}"
    rounded: "{rounded.lg}"
    padding: "1.4rem"
  button-solid:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.night}"
    rounded: "{rounded.pill}"
    padding: "0.7rem 2rem"
  button-solid-hover:
    backgroundColor: "{colors.gold-hi}"
  button-ghost:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.cream}"
    rounded: "{rounded.pill}"
    padding: "0.7rem 2rem"
  segment-active:
    backgroundColor: "{colors.gold}"
    textColor: "{colors.night}"
    rounded: "{rounded.pill}"
    padding: "0.45rem 1rem"
  rank-row:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.cream}"
    rounded: "{rounded.md}"
    padding: "0.75rem 1.1rem"
---

# Design System: مؤشّر (Muashir)

## Overview

Muashir is a night-market screen: a black ground, gold price lines drifting behind everything, cream text, and glass panels that hold the content. The page moves from the first frame and keeps copy to a line or two per section. The owner set the bar as their own Cerebra and Sila sites, so motion, glass and short copy are requirements, not decoration.

Arabic, right-to-left. Numbers use Western digits, read left to right, and use a true minus sign (−).

## Colors

### Primary
- **Gold** (`#d9b24a`) and **Gold Highlight** (`#f4d98a`): the brand, primary buttons, active controls, the background lines, focus rings.

### Neutral
- **Night** (`#050505`): the page ground.
- **Panel** (`#14120c`): glass panels, used at 42–92% opacity over the moving background.
- **Cream** (`#f3ead3`): text. Secondary text is cream at 80%, tertiary at 62%.

### Signal
- **Up** (`#46d39a`) and **Down** (`#ff6b6b`): rises and falls only, always with a sign or an arrow.

### Named Rules
- **Gold is the only brand colour.** Green and red never decorate; they mean up and down.

## Typography

- **Alexandria** (weights 600 and 800): the name, headings, every number.
- **IBM Plex Sans Arabic**: body text and labels.

### Hierarchy
- Page question: `clamp(2.5rem, 7.6vw, 6rem)`, weight 800.
- Section heading: `clamp(1.9rem, 4.6vw, 3.4rem)`, weight 800.
- Card title: `clamp(1.3rem, 2.4vw, 1.8rem)`, weight 600.
- Body: 1.0625rem at line-height 1.8.
- Labels: 0.78–0.95rem.

### Named Rules
- **One or two lines per section.** Method and limits sit in collapsed panels.
- **Numbers are isolated** left-to-right inside Arabic text.

## Layout

- Content width up to 76rem; sections separated by `clamp(4rem, 9vw, 7.5rem)`.
- The opening fills the viewport with the question and the arena; a dock strip of all companies sits under it.
- The story is a two-column sticky stage: steps scroll on one side, a glass stage changes scene on the other. Below 60rem the stage sticks to the top and the steps pass under it.
- The company sheet slides in from the side on wide screens and up from the bottom on phones.

## Elevation & Depth

Depth is glass over a moving ground: backdrop blur, a hairline border, an inner top highlight and one long soft shadow. Panels with the spotlight class show a gold glow that follows the pointer.

### Shadow Vocabulary
- Glass: `inset 0 1px 0 rgb(255 255 255 / 0.1), 0 1.8rem 3rem -1.8rem rgb(0 0 0 / 0.8)`.
- Gold button: `0 0.8rem 2rem -0.8rem rgb(217 178 74 / 0.8)`.

## Shapes

Soft and round: 1.4rem panels, 1–1.1rem rows and inputs, full pills for buttons, tags and segmented controls.

## Components

### Glass panel
The container for every block of content. Never nested inside another glass panel.

### Buttons
Solid gold pill for the main action, ghost glass pill for the second. Both lift 2px on hover and press to 97%.

### Segmented control and filter chips
Pills. The active segment is solid gold; an active chip is gold outline with a faint gold fill.

### Rank row
A full-width button: rank, name with sector and sample size, a bar, the value. Bars are gold for scores and diverge green/red around a centre mark for returns. Rows glide to their new place when the order changes.

### Arena
The opening's centrepiece and the site's own signature: two company cards with gauges either side of four metric rows whose bars race out from the centre, then a one-line verdict. It plays ready matchups by itself every 6.5 seconds until the visitor touches it; tapping a card arms that side and a company picked from the dock strip slides in to replace it. First company is cream, second is gold, everywhere.

### Gauge
A 270° gold arc that fills while the number counts up.

### Sticky stage
One glass stage with three scenes: a score gauge with seven components lighting in turn, bars that grow, and lines that draw.

### Company sheet and search palette
A sheet with gauge, six figures, a score timeline, a component radar and recent announcements. A Ctrl+K palette finds a company by name or ticker.

### Motion
Ease `cubic-bezier(0.16, 1, 0.3, 1)` everywhere. Loader with a drawn line, word-by-word blur-in headings, odometer numbers, scroll reveals, racing bars, sliding card swaps, drawn charts. No reels or marquees: those belonged to the Cerebra reference and were removed at the owner's request. `?still=1` or a reduced-motion setting shows everything at rest.

## Do's and Don'ts

### Do:
- Keep the background moving and the copy short.
- Give every number a sign or a unit.
- Let a new feature open in the sheet or the stage before adding a new page section.

### Don't:
- Don't add a second brand colour or a light section.
- Don't nest glass panels.
- Don't write a paragraph where a number and a line will do.
- Don't show a figure that is not in the pipeline's output.
