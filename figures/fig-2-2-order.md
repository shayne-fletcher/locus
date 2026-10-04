# Fig 2.2: order matters

File: `images/fig-2-2-order.png`. Section: "A run is a fold".

**Idea:** the same two messages in the opposite order give a different state.

**Layout:** two rows, each a two-box fold in the Fig 2.1 style, with the state values written on the wire.
- **Top row:** state wire **5** → [step, message **incr(1)**] → **6** → [step, message **reset()**] → **0**.
- **Bottom row:** state wire **5** → [step, message **reset()**] → **0** → [step, message **incr(1)**] → **1**.
- Right side: the two end states, **0** and **1**, circled, with a hand-drawn "≠" between them.
- The lilac actor blob looks between the two rows, puzzled.

**Must be true:** both rows start from the same 5. Only the order of the two envelopes differs.
