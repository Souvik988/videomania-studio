# Brands: a persistent motion design system per brand

One folder per brand: `brands/<slug>/` with
- `MOTION.md`: colours (hex and what each is for), fonts and sizes, timing (how things enter, hold,
  leave), how things move (easing, springs, anything handmade), texture and finish, five things this
  brand's motion must never do, and one shot-by-shot example done right. Write only what the brand's
  own material or the user shows; where you cannot tell, write ASK ME (method from Charlie Hills'
  brand-intake, MIT).
- `tokens.css`: the same decisions as `--mk-*` variables, layered over the chosen look by
  `new_composition.py --brand <slug>`.

Before designing for a brand, read its MOTION.md. It sets the look, not the ambition. After a film is
approved, update the brand's MOTION.md with what worked (and the house rules with any note).
