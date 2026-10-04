---
title: How Monarch's Python actors work
subtitle: "[subtitle TBD]"
author: Shane Fletcher
---

A Python actor in [Monarch](https://github.com/meta-pytorch/monarch) spans two languages. Rust owns the mailbox; Python owns the loop.

![Rust owns the mailbox, Python owns the loop.](images/strip-1-python-actors.png)

Source: [`d16adfd48`](https://github.com/meta-pytorch/monarch/tree/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2). *Personal notes.*

## An actor is a step

```python
from monarch.actor import Actor, endpoint

class Counter(Actor):
    def __init__(self):
        self.n = 0

    @endpoint
    def incr(self, k: int) -> int:
        self.n += k
        return self.n
```

States $S$, messages $M$, replies $R$:

$$ \mathsf{step} : S \times M \to S \times R $$

![The step box.](images/fig-1-1-step.png)

$\mathsf{step}(n, \mathtt{incr}(k)) = (n + k,\ n + k)$. A **Mealy machine**.

The object lives on its own Python thread; [`PythonActor`](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/monarch_hyperactor/src/actor.rs#L1066) holds a handle. The rest is plumbing around `step`, which never changes.

## A run is a fold

```python
    @endpoint
    def reset(self) -> int:
        self.n = 0
        return 0
```

From $s_0$:

$$
\begin{aligned}
(s_1, r_1) &= \mathsf{step}(s_0, m_1) \\
(s_2, r_2) &= \mathsf{step}(s_1, m_2) \\
(s_3, r_3) &= \mathsf{step}(s_2, m_3)
\end{aligned}
$$

![The fold.](images/fig-2-1-fold.png)

`mapAccumL`. Replies out; state in `self`. [`_dispatch_loop`](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/python/monarch/_src/actor/actor_mesh.py#L1398):

```python
while True:
    msg = await receiver.recv()
    await _handle_queued_message(actor, msg)
```

> State is the fold of the messages handled so far.

**One at a time:** $s_2$ needs $s_1$.

**In order:**

$$
\begin{aligned}
\mathtt{incr}(1),\ \mathtt{reset}() &:\quad 5 \to 6 \to 0 \\
\mathtt{reset}(),\ \mathtt{incr}(1) &:\quad 5 \to 0 \to 1
\end{aligned}
$$

![Order matters.](images/fig-2-2-order.png)

Delivery must preserve order.

<!-- To come, in order:
## Order            two FIFO hops; order-preserving maps compose
## Where code runs  every step labelled with its thread; Python objects only on the actor's thread
## The GIL is a token   invariants and induction; never on Tokio (#4938, #4991, pytokio removal)
## Waking up        happens-before; check-then-wait; wakes <= messages
## Two drivers      strip 2 whole; loop owns thread vs thread owns loop
## The same actor   observational equivalence for sync endpoints; what changes (supervision in the queue, get() without a helper thread)
## Afterword        the comics were diagrams
-->
