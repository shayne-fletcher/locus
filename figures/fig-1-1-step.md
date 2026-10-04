# Fig 1.1: the step box

File: `images/fig-1-1-step.png`. Section: "An actor is a step".

**Idea:** the whole actor is a single box with two inputs and two outputs.

**Layout:**
- Centre: one large rounded box, lilac, labelled **step**. The lilac actor blob peeks over its top edge.
- Left side, two arrows entering the box:
  - upper: a heavy wire labelled **s** (state);
  - lower: a thin wire carrying a small envelope, labelled **m** (message).
- Right side, two arrows leaving the box:
  - upper: a heavy wire labelled **s′** (new state);
  - lower: a thin wire carrying a small envelope, labelled **r** (reply).
- Beneath the box, centred, the formula: *step : S × M → S × R*
- Small handwritten notes beside the wires: "state" by s and s′, "message" by m, "reply" by r.

**Must be true:** the state wire goes in and comes out at the same height, as one heavy line interrupted by the box.
