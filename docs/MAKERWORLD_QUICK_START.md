# MakerWorld Quick Start Guide

**Braille Cylinder STL Generator — Parametric Model Maker edition**

This guide walks you from "I want a braille label" to a downloadable STL pair
using the single-file build in
[`makerworld/Braille_Cylinder_STL_Generator_MakerWorld.scad`](../makerworld/Braille_Cylinder_STL_Generator_MakerWorld.scad)
on [MakerWorld](https://makerworld.com/)'s Parametric Model Maker.

A PDF version of this guide is available:
[`MakerWorld_Quick_Start_Guide.pdf`](MakerWorld_Quick_Start_Guide.pdf).

---

## 1. What to Include

Braille takes far more space than print — you cannot include everything, so
prioritize. The core question, per the Braille Authority of North America
(BANA): *"Can someone identify me and contact me with just this information?"*
If yes, you have enough.

- Each row holds **13 braille cells of text** by default, and the generator
  offers **4 lines** (`Line_1`–`Line_4`).
- BANA's typical four-line business card layout: **name**, **organization**,
  **phone number**, **e-mail address**. Job titles, mailing addresses, fax
  numbers, and websites are usually the first things to cut.
- If a name will not fit on one 13-cell line: drop capital indicators, drop a
  middle initial, use a first initial, or continue the name onto the next
  line.
- Organization names can be abbreviated (BANA's examples: `lib` for
  "library", `amer` for "American", `nat` for "National") or omitted entirely
  if the e-mail address already contains them.

Source: BANA *Business Cards Fact Sheet* (approved March 2024) — see
Resources below.

## 2. Translate Your Text

MakerWorld's customizer cannot translate English for you. Paste
**pre-translated Unicode braille**, one line per `Line_N` field.

1. Open a braille translator such as
   <https://www.branah.com/braille-translator>.
2. Type your text in **lowercase** (each capital letter adds an indicator
   cell — braille readers understand omitting capitals is standard practice
   for space-limited labels).
3. Copy the **Unicode braille** output — the dot characters such as
   `⠓⠑⠇⠇⠕` — not the ASCII/BRF letters.
4. Translate each line separately so you control where lines break.

Uncontracted (Grade 1) UEB is clearest for names and contact information.

## 3. Formatting

### Phone numbers

BANA guidance: braille a phone number as `#123.456.7890` — omit parentheses
and convert hyphens to periods. In Unified English Braille a period inside a
number keeps *numeric mode* active, so only **one** number sign (`⠼`) is
needed for the whole number. For example, `206.616.7678` translates to:

> `⠼⠃⠚⠋⠲⠋⠁⠋⠲⠛⠋⠛⠓` — exactly **13 cells**, which fits the default row.

Some online translators repeat the number sign after each period. That output
is non-standard and wastes cells — if your translation shows more than one
`⠼` in a phone number, it likely will not fit.

**Splitting a long number across two rows:** divide after a period and begin
the next row with a fresh number sign:

> Row 1: `⠼⠃⠚⠋⠲⠋⠁⠋⠲` (`206.616.`)
> Row 2: `⠼⠛⠋⠛⠓` (`7678`)

### E-mail and web addresses

Braille them per the Rules of UEB. When an address must be divided over two
lines, divide after punctuation (the `@` sign, a period, or a hyphen) and
begin the second line in cell 1. A dot-5 line continuation indicator at the
end of the first line is preferred; omit it only as a last resort. Tip: omit
`https://` or `www.` if the domain is clear without it.

## 4. Using the Customizer

1. Go to MakerWorld → **Create** → **Parametric Model Maker** and upload
   **only** `Braille_Cylinder_STL_Generator_MakerWorld.scad`.
2. In the parameter panel:
   - Paste your Unicode braille into `Line_1`, `Line_2`, `Line_3`, `Line_4`
     (leave unused lines empty). Do **not** type plain English.
   - `paper_thickness_preset`: keep `0.4mm` (default) for typical card stock,
     `0.3mm` for thinner paper, or `Custom` to use your own slider values.
     Presets control dot and spacing dimensions; they never change the
     `grid_columns` / `grid_rows` capacity sliders.
   - `dot_shape`: `Rounded` (default) or `Cone`.
   - `indicators` (Indicator Letters): `On` adds a square marker next to the
     triangle alignment indicator at each row's start. The triangle is always
     present — it is critical to the mechanical device the cylinder mounts
     into. On widens the grid by 2 marker cells, Off by 1 (triangle only) —
     your 13-cell text capacity is unchanged either way.
3. Generate the **Embossing Plate** (`plate_type = Embossing Plate`),
   render, and download the STL.
4. Switch `plate_type` to **Counter Plate** — change nothing else — and
   download again. The two plates form a matching pair: paper goes between
   them, and pressing the embossing plate's dots into the counter plate's
   recesses forms readable braille.

## 5. Cylinder Sizing

- **Measure the diameter** of the container you are labeling: wrap a string
  around it, measure the string, and divide by π (3.14159). Enter it as
  `cylinder_diameter`.
- **Height:** measure the flat area where the braille will sit and leave a
  margin at the top and bottom.
- **Capacity math:** cells are spaced 6.5 mm apart, so the default 13 text
  cells + 2 indicator cells span about 91 mm. The default 30.8 mm-diameter
  cylinder (~96.8 mm circumference) fits that with room left for the seam
  gap. A larger diameter adds margin around the seam rather than more cells —
  raise `grid_columns` yourself if you want longer rows on a bigger cylinder.
  With Indicator Letters Off (triangle cell only), up to 14 text cells fit the
  default cylinder.
- Print cylinders standing upright for the best dot quality, and use
  `seam_offset_degrees` to rotate the seam away from your text.

## 6. Troubleshooting

### INVALID CHARACTERS

Red 3D text reading `INVALID CHARACTERS` means a `Line_N` field contains
something other than Unicode braille (typed English, ASCII braille, or stray
spaces from another alphabet). Re-translate and copy the Unicode braille
output.

### TEXT TOO LONG: 16/13

A line exceeds the row capacity. The warning shows the counts — longest line
vs. capacity — because MakerWorld's preview cannot show console output.
Fixes, in order of preference:

1. **Shorten or split** the line across rows (see the phone-number splitting
   pattern above).
2. **Raise `grid_columns`** (Braille Grid Layout section) if your cylinder is
   large enough.
3. **Set `text_limit_check` to `Off`** (Text Input section) to bypass the
   check entirely: every pasted cell renders and no warning appears, but rows
   longer than the capacity may crowd the seam gap.

## 7. Examples

Business-card examples take the content decisions from BANA's Fact Sheet
(BANA's published braille is Grade 2; translate your own text as Grade 1).

| Scenario | Lines to translate and paste | Notes |
|----------|------------------------------|-------|
| Name + e-mail (BANA Example 1) | `harry potter` / `harry@hogwarts.edu` | Organization omitted — it already appears in the e-mail address. |
| Long name (BANA Example 4) | `liesel a.` / `schimmelfennig` / `l.schimmelfennig@usace.army` | Name continues onto the second line; phone omitted. |
| Nickname + two phones (BANA Example 7) | `fran rikard` / `albuquerque ac` / `c 505.312.4224` / `f 505.312.4225` | Nickname saves cells; `c`/`f` prefixes tag cell and fax. |
| Spice jar (~55 mm diameter) | `cinnamon` | One row; set `cylinder_diameter = 55`. |
| Medicine bottle (~40 mm) | `amoxicillin` / `500mg` | "amoxicillin" is 11 cells — within the 13-cell row. |
| Water bottle tag (~75 mm) | `j. smith` / `555.867.5309` | Initials save space; the phone number fits one row. |

## 8. Resources

- [BANA Position Statements and Fact Sheets](https://www.brailleauthority.org/bana-position-statements-and-fact-sheets)
- [BANA *Business Cards Fact Sheet* (PDF, approved March 2024)](https://www.brailleauthority.org/sites/default/files/2024-10/Business%20Cards%20Fact%20Sheet.pdf)
- [BANA *Size and Spacing of Braille Characters*](https://www.brailleauthority.org/size-and-spacing-braille-characters)
- [The Rules of Unified English Braille (ICEB)](https://iceb.org/ueb.html)
- [This project on GitHub](https://github.com/BrennenJohnston/braille-stl-generator-openscad)
- [Web app companion project](https://github.com/BrennenJohnston/braille-card-and-cylinder-stl-generator) — translates English for you in the browser
- For complex cases (international phone numbers, multiple languages,
  credentials), consider working with a **UEB-certified transcriber**.
