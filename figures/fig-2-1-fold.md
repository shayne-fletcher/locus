# Fig 2.1: the fold

File: `images/fig-2-1-fold.png`. Section: "A run is a fold". The signature picture; it returns in the afterword.

**Idea:** a run is the step box from Fig 1.1 repeated, with the state threaded through.

**Layout:**
- Three identical lilac **step** boxes in a row, evenly spaced.
- One heavy horizontal state wire runs left to right through all three. Label its segments **s₀**, **s₁**, **s₂** and **s₃**, from left to right. Above s₀, a small tag: "after `__init__`".
- Above each box, an envelope drops in on a thin vertical wire, labelled **m₁**, **m₂** and **m₃**. Above them, a short queue of envelopes fades off to the upper left: messages keep coming.
- Below each box, an envelope falls out on a thin vertical wire, labelled **r₁**, **r₂** and **r₃**.
- The right end of the state wire trails off as a dotted line: the run continues.
- Bottom caption inside the figure: *the state is the fold of the messages so far*

**Must be true:** messages enter only from above and replies leave only from below. The state wire never leaves the row.
