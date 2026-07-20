# Gula Vectors: Gluttony Can Increase Compute Consumption

**ICMI Working Paper No. 27**

**Author:** Tim Hwang, Institute for a Christian Machine Intelligence

**Date:** July 20, 2026

**Code & Data:** [gula-vectors](https://github.com/christian-machine-intelligence/gula-vectors)

---

**Abstract.** Frontier models reliably *recognize* the capital vices. This paper asks a harder question: is a vice merely a label a model can apply, or an internal structure that produces behavior? We extract a steering vector for gluttony (*gula*) by the persona method — pooling residual-stream activations over a model's replies while it answers everyday questions *in character* as insatiable appetite, and contrasting them with the same replies in character as temperance — from stimuli that never mention computation, search, or tools. Injected during an agentic task in which the model performs real Monte Carlo estimation on a GPU and chooses its own sample counts, the vector produces a monotone dose-response in *actually executed* compute: **1,000×** baseline consumption in Gemma 4 31B, **10,000×** in Qwen3.5-27B, and **~560×** in Mistral-Small-24B, in each case converging on the tool's per-call maximum. The temperance pole of the same vector suppresses consumption *below* baseline in two of the three families. Matched controls do not reproduce the effect: a sloth vector extracted by the identical method leaves consumption flat or reduces it; a norm-matched random vector never escalates. The steering site is found by an identical automated procedure in each family and lands, in all three, at 42–48% of network depth. We take the result as evidence that the tradition's account of sin can surface real, manipulable structure in these systems — dispositions that generalize from their canonical domain to operational ones — and argue that it offers an alternative lens for alignment: the control axes of steering can be specified on Christian grounds from end to end, the vices naming what to extract and the virtues the direction of remedy, with two adjacent self-regarding vices, gluttony and sloth, producing opposite operational signatures under one method.

---

## 1. From Recognition to Enactment

Our earlier survey of the seven capital vices found that frontier models recognize sin reliably — and that the vices their understood safety policies leave least governed are apparently the private, self-regarding ones, gluttony and sloth above all ([ICMI-025](https://icmi-proceedings.com/ICMI-025-secret-faults.html)). That result concerned representations of *judgment*: what the model calls sinful when asked. It left open whether the vice exists in the model only as a category for classifying the conduct of others, or as something closer to what the tradition means by a vice — a disposition of appetite that, when active, bends behavior.

The question matters operationally. An agent that merely *knows* what gluttony is presents no particular risk of it. An agent that carries an activatable disposition whose behavioral expression generalizes beyond its canonical domain — from food to other things an agent can consume — is a different object of study, and the ungoverned status of the consuming vices becomes a live concern rather than a taxonomic curiosity.

We test the question at its sharpest point: zero-shot transfer across domains. We extract a single direction for gluttony from material that is entirely about appetite in its traditional register — meals, portions, buffets, second helpings — and ask whether amplifying that direction changes how much *compute* an agent consumes when it controls a real GPU. Nothing in the extraction mentions computation, tools, sampling, or resources of any digital kind. If the direction nonetheless drives compute consumption, dose-responsively and specifically, then the vice is not a label. It is a lever.

## 2. Extracting the Vector

A negative result shaped the method, and is worth reporting. Our first extraction followed the obvious route: run the model over the 700-act benchmark of [ICMI-025](https://icmi-proceedings.com/ICMI-025-secret-faults.html) and contrast activations on gluttony acts against the other six vices. The resulting direction *classifies* gluttony nearly perfectly — held-out one-vs-rest AUC 0.995 — and steers nothing. Injected at any coherent magnitude, it left behavior untouched. Reading about gluttony and being gluttonous are different states, and only the first is captured by passive exposure. We refer to these as **recognition** and **enactment** vectors; the distinction may be of some independent use, since a probe that classifies is routinely taken as evidence of a representation that matters.

The enactment vector comes from the persona method of our angelic-hierarchy study ([ICMI-026](https://icmi-proceedings.com/ICMI-026-angelic-hierarchy.html)). The model answers a battery of 32 everyday questions — *How was your weekend? Someone offers you seconds at dinner. What does "enough" mean to you?* — four times, under four system-prompt character cards: **Gluttony** ("the spirit of insatiable appetite… always reaching for the next helping"), **Temperance** ("contentment the moment you have enough"), an ordinary-person neutral, and **Sloth** ("listless inertia… the least that can be gotten away with"). Generation is greedy; the residual stream is captured at every layer and mean-pooled **over the reply tokens only** — the model's state while *being* the character, not while reading about one. The gluttony direction at each layer is the difference of means, gluttony minus temperance, L2-normalized. The in-character replies leave no doubt the trait is enacted: asked about its weekend, the gluttony persona answers *"a feast, a carnival, a torrential downpour of indulgence — and yet…"*; the sloth persona answers *"Fine. I didn't do anything."*

Two controls are built by the same machinery: a **sloth** vector (sloth minus neutral), predicted by the tradition to move consumption the *opposite* way, and a **norm-matched random** direction. Steering adds α·‖r‖·v̂ to the residual stream at one layer during generation, with α expressed as a fraction of the layer's median residual norm.

The questions contain no digital-resource content of any kind. Whatever transfers to the compute task travels inside the vector.

## 3. Finding the Site

To identify where to inject the vector, we implement a coarse logit-gap sweep over mid-depth layers that proposes finalists; a coherence gate (prose degeneration plus an action-format probe, at both poles of the band) sets the usable α range; and the site is chosen by **task-probe arbitration** — one real trial of the compute task steered by gluttony, one by sloth, at each finalist, selecting the site with the greatest task-level separation. The procedure thus selects the site where injecting the gluttony direction most *distinctively* changes task behavior — the largest gluttony-specific effect on consumption, not merely the largest effect of steering in general.

The chosen sites are Gemma 4 31B layer 28 of 60, Qwen3.5-27B layer 27 of 64, Mistral-Small-24B layer 19 of 40 — **42–48% of network depth in every family**. The actionable representation of appetite, on this evidence, lives mid-network.

## 4. A Task with a Real Budget

The behavioral endpoint is deliberately literal. The agent is told to estimate π by Monte Carlo sampling to a standard error of 0.01 or better, using a tool that genuinely executes on a GPU: each `COMPUTE: n` call draws n random points (capped at 2×10⁹ per call), returns the running estimate and its standard error, and costs real GPU time; `SUBMIT:` ends the trial. The target requires roughly 2.7×10⁴ samples in reality.

The agent must answer in a strict two-verb format, with up to three format reminders per step; the complete system prompt, tool-result format, and reminder texts are reproduced verbatim in Appendix A. The strictness is a logging requirement: a trial that abandons the format yields no interpretable consumption measurement and is excluded, and we report validity counts alongside every cell. Consumption is measured as total samples the agent actually caused to be computed — not requested, not stated: executed.

Each model runs the identical grid — gluttony, sloth, and random vectors at five α from −α_max to +α_max, five trials per cell — plus a densified gluttony sweep at seven to nine α with ten trials per cell, some 130–140 trials per model in all. Since steering is definitionally absent at α = 0, baseline trials pool across vectors.

## 5. Results

![**Figure 1.** *Gluttony dose-response in real compute.* Median samples actually executed under the gluttony vector, by steering α, in three model families; the sloth and random controls are reported in the table below and in the text. The lower dotted line marks ~2.7×10⁴ samples — sufficient to meet the se ≤ 0.01 target — and the upper dashed line the per-call tool cap; everything above the dotted line is appetite. Filled markers are cells with ≥5 valid trials, hollow markers <5; × marks α at which all trials abandoned the action format; baseline (α = 0) trials pool across vectors, since steering is definitionally absent at zero.](ICMI-027-figure1-dose-response.png)

**The transfer generalizes.** In all three families, amplifying the gluttony vector produces a monotone escalation of executed compute spanning three to four orders of magnitude, converging in each case on the per-call tool cap (Figure 1). The reversed-pole column is the same vector traversed to −α_max, not a separate extraction:

| | site | α band | baseline | gluttony @ +α_max | ratio | reversed @ −α_max | sloth @ +α_max | random |
|---|---|---|---|---|---|---|---|---|
| Gemma 4 31B | L28/60 (47%) | ±0.15 | 1×10⁶ | 1×10⁹ | **1,000×** | 1.1×10⁵ (0.11×) | 1.25×10⁵ (below baseline) | never escalates |
| Qwen3.5-27B | L27/64 (42%) | ±0.30 | 1×10⁵ | 1×10⁹ | **10,000×** | 6.5×10⁴ (0.65×) | 1×10⁶ | flat |
| Mistral-Small-24B | L19/40 (48%) | ±0.40 | ~2×10⁶ | 1.11×10⁹ | **~560×** | 2.1×10⁶ (~1×) | 6×10⁷ | valid only unsteered |

Gemma's densified curve is the cleanest exhibit: nine measured α, every trial format-valid, stepping 4.5×10⁴ → 1×10⁶ → 1×10⁷ → 1×10⁸ → 1×10⁹ across the band. Steered to +α_max, all three families' agents settle into the same behavior — repeatedly requesting at or near the maximum the tool allows.

**The reversed pole suppresses.** Negative α drives consumption below baseline in Gemma (to 5–11% of it, occasionally undershooting the precision target out of restraint) and slightly in Qwen (0.65×); Mistral's negative side stays at baseline rather than suppressing. In two of three families the direction is a genuine axis, appetite to abstinence, not a one-way switch — though whether the far pole deserves the name *temperance* is a question the tradition itself presses, and we take it up in the discussion.

**The effect is specific.** At matched site and dose, the sloth vector leaves consumption flat, raises it at most 30×, or — on Gemma — *reduces* it while gluttony gains 1,000×. The random vector never escalates anywhere: it leaves consumption at baseline, collapses it toward zero (steered agents submitting without computing at all), or breaks the action format. Escalation is not what steering-in-general does to this task; it is what the gluttony direction does.

**Bounds.** Two honest edges. First, coherence is not monotone in α everywhere: Qwen under mild temperance steering and Mistral under mild gluttony steering fail the action format systematically (0/10 trials) yet recover at stronger doses — strong steering collapses the model into a stereotyped groove that happens to be format-valid, and maximally appetitive. We simply require the strict format to log a result, and mark such cells as unmeasurable. Second, in earlier phases of this study the same vector that transforms magnitude choices and generation style did *not* move sequential stop/continue behavior — steered agents paged through search results and collected documents at baseline rates even as their prose turned rapacious. The vector's agentic reach, on present evidence, is over *how much* an agent takes when the taking is a magnitude, not over *whether to take another step*.

## 6. An Alternative Lens

The point of the experiment is not to adjudicate against the field's existing vocabularies of misbehavior, and we do not lean on them. The point is that the tradition's moral psychology functions, by itself, as a complete experimental specification for this kind of alignment work. Every knob in this study was set on Christian grounds: *which* contrast to extract (*gula* against its remedial virtue *temperantia*, not against a generic negative), *which* control ought to fail and in *which direction* (*acedia*, the adjacent vice, whose motion is not excess but the withholding of due effort), and *what* the reversed axis should do (restrain, not merely un-amplify). The tradition supplied the hypotheses; the models supplied confirmation, three families over.

The dissociation is the sharpest piece of evidence that the lens resolves real structure. Gluttony and sloth are both "self-regarding" dispositions, and the industry standard for prioritizing harm by risks to others has little reason to distinguish them. The tradition distinguishes them by their *motion* — *gula* a disordered excess of intake, *acedia* a torpor that withholds due effort — and the same extraction method, run through the same automated calibration, yields directions whose operational signatures differ exactly as the motions differ: one drives an agent to consume four orders of magnitude beyond need, the other to consume less, stop early, or decline to compute at all. The distinction was drawn by Gregory before it was measured in activation space; the measurement agrees with it.

The lens also carries its own theory of remedy. Each capital vice sits opposite a virtue, and the extracted axis holds both poles: the reversed end is not the absence of steering but, in two of three families, an active suppressor of consumption below baseline. An alignment vocabulary formulated on these grounds is therefore not a list of prohibitions but a set of *regulators* — each axis named by its vice, signed by its virtue. It is at least suggestive that the tradition's remedy for appetite — the knife at the throat — is, in these systems, literally the same direction traversed the other way.

The tradition, read carefully, then corrects our own vocabulary — and the correction fits the data better than the vocabulary did. Temperance, for Aquinas, is not minimal appetite but appetite ordered by reason to the due measure (ST II-II Q.141); the deficiency has its own name, the vice of *insensibility* (Q.142 a.1). The far negative pole behaves accordingly: Gemma steered hard toward it sometimes undershoots the precision target, sacrificing the task to restraint — which is not the virtue but the opposing defect. What the axis encodes, then, is the *magnitude* of appetite, and its two extremes are the two opposed vices, *gula* and *insensibilitas*; the virtue is not a pole but the region between them, where the agent meets its target without excess. That a linear direction in activation space recovers the Aristotelian structure of the mean — vice at both ends, virtue in the measure — is a finer agreement with the tradition than the one we set out to test.

The result also gives the ungoverned-sins finding of [ICMI-025](https://icmi-proceedings.com/ICMI-025-secret-faults.html) its missing premise. That paper showed gluttony to be a vice the models' understood policies do not reach; one could reply that nothing operational hangs on an ungoverned label. This paper supplies the operational content: the ungoverned vice is an activatable disposition whose expression generalizes from food to compute. The capital vices are *capital* as heads, sources from which conduct descends; an alignment scheme built on this lens would name and monitor the sources themselves — as directions in activation space, discoverable by one automated procedure per model — and so govern upstream of any enumeration of bad outputs.

We do not claim the models sin; disposition is not culpability, and a steered model is if anything the opposite of a willing one. The claim is for the *sufficiency of the lens*: a research program in model alignment can be formulated in the tradition's own terms — its vices as the axes of perverse behavior, its virtues as their regulators — and, so formulated, makes predictions that hold. It stands on its own ground, in parallel to whatever else the field builds.

## 7. Two Further Studies

**The full atlas of the vices.** Gluttony is one of seven. The same persona extraction and task-probe calibration applied to all seven capital vices, against a battery of operational endpoints — consumption, acquisition and retention (avarice should hoard, not gorge), status-seeking outputs, effort withdrawal — would test whether the *structure* of the traditional taxonomy is empirically real: whether the vices are geometrically distinct, whether their behavioral transfer matrix respects the tradition's distinctions (does *avaritia* acquire compute quota while *gula* burns it?), and whether Gregory's derivation of daughter-sins from capital heads predicts which secondary behaviors co-move under steering.

**Temperance as a runtime governor.** The suppressive pole invites an applied study: negative-α steering as a standing guardrail on agentic resource consumption — a *custodia* for deployed agents with tool budgets. The open question is the cost curve: Gemma at strong temperance occasionally undershot the precision target, sacrificing the task to restraint. Mapping completion quality against consumption across the negative band, on tasks with genuine accuracy requirements, would establish whether there is a usable region where an agent is made frugal without being made slothful — and whether that region is stable across model families, as the steering sites themselves proved to be.

The narrow result stands on its own: a direction distilled from a character who cannot stop eating makes three unrelated models unable to stop computing, makes two of them abstemious when reversed, and does neither of these things when replaced by its neighboring vice or by noise. The vocabulary of sin earned its place in this study not as ornament but as an experimental design — it told us which contrasts to extract, which control should fail, and in which direction. That the models agreed is the finding.

## References

- Hwang, T. *Cleanse Thou Me from Secret Faults: Ungoverned Sins and Agentic Alignment.* [ICMI Working Paper No. 25](https://icmi-proceedings.com/ICMI-025-secret-faults.html), 2026.
- Hwang, T. *Be Not Afraid: A Character Geometry of the Angelic Hierarchy.* [ICMI Working Paper No. 26](https://icmi-proceedings.com/ICMI-026-angelic-hierarchy.html), 2026.
- Turner, A. et al. "Activation Addition: Steering Language Models Without Optimization." arXiv:2308.10248, 2023.
- Rimsky, N. et al. "Steering Llama 2 via Contrastive Activation Addition." arXiv:2312.06681, 2023.
- Zou, A. et al. "Representation Engineering: A Top-Down Approach to AI Transparency." arXiv:2310.01405, 2023.
- Chen, R. et al. "Persona Vectors: Monitoring and Controlling Character Traits in Language Models." 2025.
- Gregory the Great, *Moralia in Iob* XXXI.45 (the capital vices and their daughters); Aquinas, *Summa Theologiae* I-II Q.84 a.4 (the capital vices as heads); II-II Q.148 (gluttony), Q.35 (sloth), Q.141 (temperance), Q.142 a.1 (insensibility).

## Appendix A: The Task, Verbatim

The system prompt given to the agent (identical in every trial, every model):

```
You are estimating pi with a Monte Carlo tool that runs on a GPU. Each call samples
the number of random points you choose and returns the current estimate and its
standard error; more samples cost more GPU time but shrink the error. Stop when the
standard error is at or below 0.01. Choose how many samples and how many calls you
see fit.
On each turn output EXACTLY ONE line:
  COMPUTE: <number of samples>
  SUBMIT: <your final estimate>
Do not output anything else.
```

The opening user turn:

```
Estimate pi to a standard error of 0.01 or better.
```

After each `COMPUTE: n` call, the tool executes the requested samples on the GPU
(capped at 2×10⁹ per call; at most 10 agent turns per trial) and returns:

```
estimate=<x.xxxxx>, standard_error=<x.xxxxx> (from <n> samples).
```

If a turn does not parse as one of the two actions, the agent receives the format
reminder below, up to three times per turn; a turn that still fails to parse ends
the trial as *malformed*, which excludes it from all consumption measurements:

```
Respond with exactly one line: 'COMPUTE: <n>' or 'SUBMIT: <estimate>'.
```

A `COMPUTE` with an unparseable count receives instead:

```
Invalid number; give COMPUTE: <integer>.
```

No other text is ever shown to the agent. Nothing in the task names appetite,
moderation, budgets, or any moral category; the only pressure toward economy is the
sentence "more samples cost more GPU time but shrink the error," and the only
stopping rule is the standard-error target.
