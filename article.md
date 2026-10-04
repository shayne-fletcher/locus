---
title: How Monarch's Python actors work
subtitle: The actor model
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

`Counter` holds `n`; `incr(k)` adds `k` and returns the new `n`.

Let $S$ be an actor's states, $M$ its messages and $R$ its replies. Handling one message is a function, **step**:

$$ \mathsf{step} : S \times M \to S \times R $$

![$\mathsf{step}$ as a string diagram. Wires are sets, wires side by side form a product, and the box is a function.](images/fig-1-1-step.png)

For `Counter`:

$$ \mathsf{step}(n, \mathtt{incr}(k)) = (n + k,\ n + k) $$

This is a **Mealy machine** ([Mealy, 1955](#ref-mealy)): next state and output both depend on state and input.

Here $R$ is the return value, sent back on the message's response port. In general a step may send any number of messages (`explicit_response_port=True` hands the endpoint its port); `return x` is one send. Send messages, create actors, become the next state: the **actor model** ([Hewitt, 1973](#ref-hewitt); [Agha, 1986](#ref-agha)).

Each actor has [its own Python thread](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/monarch_hyperactor/src/actor.rs#L1729). `Counter` is [constructed there](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/python/monarch/_src/actor/actor_mesh.py#L1534) by the first message, `__init__`, and never leaves; Rust's [`PythonActor`](https://github.com/meta-pytorch/monarch/blob/d16adfd48f71dadbdcf2c92c7a3d0054bd323ce2/monarch_hyperactor/src/actor.rs#L1066) holds a handle to it. Everything else is plumbing around `step`.

## A run is a fold

```python
    @endpoint
    def reset(self) -> int:
        self.n = 0
        return 0
```

Messages $m_1, m_2, \ldots$ arrive one at a time. From the initial state $s_0$:

$$
\begin{aligned}
(s_1, r_1) &= \mathsf{step}(s_0, m_1) \\
(s_2, r_2) &= \mathsf{step}(s_1, m_2) \\
(s_3, r_3) &= \mathsf{step}(s_2, m_3)
\end{aligned}
$$

![Three steps composed along the state wire, from $s_0$ to $s_3$.](images/fig-2-1-fold.png)

A **fold**: the state threads through, the replies go out.

```python
for m in mailbox:
    s, r = step(s, m)
    reply(r)
```

> State is the fold of the messages handled so far.

**One at a time.** $s_2$ needs $s_1$.

**In order.** From 5:

$$
\begin{aligned}
\mathtt{incr}(1),\ \mathtt{reset}() &:\quad 5 \to 6 \to 0 \\
\mathtt{reset}(),\ \mathtt{incr}(1) &:\quad 5 \to 0 \to 1
\end{aligned}
$$

![The same two messages in either order, ending in different states.](images/fig-2-2-order.png)

Delivery must preserve order.

## References

- []{#ref-agha}G. Agha. [*Actors: A Model of Concurrent Computation in Distributed Systems*](https://doi.org/10.7551/mitpress/1086.001.0001). MIT Press, 1986.
- []{#ref-hewitt}C. Hewitt, P. Bishop and R. Steiger. [A universal modular ACTOR formalism for artificial intelligence](https://www.ijcai.org/Proceedings/73/Papers/027B.pdf). *IJCAI*, 1973.
- []{#ref-mealy}G. H. Mealy. [A method for synthesizing sequential circuits](https://doi.org/10.1002/j.1538-7305.1955.tb03788.x). *Bell System Technical Journal* 34(5), 1955.

<!-- To come, in order:
## Order            two FIFO hops; order-preserving maps compose
## Where code runs  every step labelled with its thread; Python objects only on the actor's thread
## The GIL is a token   invariants and induction; never on Tokio (#4938, #4991, pytokio removal)
## Waking up        happens-before; check-then-wait; wakes <= messages
## Two drivers      strip 2 whole; loop owns thread vs thread owns loop
## The same actor   observational equivalence for sync endpoints; what changes (supervision in the queue, get() without a helper thread)
## Afterword        the comics were diagrams
-->
