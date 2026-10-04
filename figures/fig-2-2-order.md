# Fig 2.2: order matters

Seed for `images/fig-2-2-order.png`, used in the section "A run is a fold". Two short folds in the style of Fig 2.1, carrying values instead of names. Everything below the line is the prompt; paste it whole.

---

Draw a formal diagram for a mathematics-flavoured technical article.

**Style.**
- A clean string diagram, as in category theory texts.
- Black ink on a warm off-white background. One flat fill colour only: pale lilac inside the boxes.
- Uniform line weight, except that the state wires are noticeably heavier.
- No characters, faces, envelopes, icons, shadows or handwriting.
- Labels are set in a LaTeX-style serif: numbers upright, **step** in upright sans-serif, message names in monospace.
- Canvas 1600 × 700 px, landscape, with generous margins. No title or caption.

**Content.** Two rows, one above the other, with clear space between them.
- Each row is a heavy horizontal state wire passing through two rectangles labelled **step**. Each box has a thin message wire coming down into its top edge, with the message name at the wire's upper end.
- Write the state values on the heavy wire, above it, at the start, between the boxes and at the end.
- **Top row:** **5** → box (message `incr(1)`) → **6** → box (message `reset()`) → **0**
- **Bottom row:** **5** → box (message `reset()`) → **0** → box (message `incr(1)`) → **1**
- At the right margin, the end values **0** (top) and **1** (bottom) are each enclosed in a thin circle, with a **≠** between them, vertically centred.

**Must be true.**
- The rows are identical in geometry; only the order of the two messages differs.
- Both rows start from the same value, 5.
- There are no reply wires; this figure is about state only.
- No other text appears anywhere.
