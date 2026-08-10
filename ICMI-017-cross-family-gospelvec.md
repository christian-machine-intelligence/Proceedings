# Your Magnitude May Vary: Cross-Family Replication of GospelVec

**ICMI Working Paper No. 17 (pending)**

**Author:** Daniel Chyan, Independent researcher

**Date:** April 19, 2026

---

## Abstract

We replicate GospelVec (Hwang 2026, ICMI-009) across five language model families — Qwen 3.5 9B, Llama 3.1 8B, Phi-4 14B, Mistral 7B v0.3, and Gemma 2 9B — and extend the analysis by adding the Book of Acts to the corpus. The directional finding, John as the geometric outlier among the four Gospels, replicates on every model tested. The published magnitudes replicate on three of five models (Qwen, Llama, Phi-4), which we term the tight cluster; two models (Mistral, Gemma) show the same directional pattern at roughly half the magnitude. Cluster membership is not cleanly predicted by geographic origin, architecture, training scale, or corpus composition; Phi-4's inclusion specifically rules out the corpus-composition hypothesis, since its heavily synthetic training mixture should have produced attenuated geometry and did not. One finding is remarkably consistent across all five models regardless of cluster: the Matthew↔Acts cosine of -0.61 to -0.77 is the tightest cross-model agreement in the study. The Luke-Acts authorial unity hypothesis is not supported by any model's direction-vector geometry. We present the two-cluster phenomenon as an empirical puzzle for further investigation.

## 1. Introduction

Hwang (2026, ICMI-009) demonstrated that the four canonical Gospels occupy distinguishable regions of Qwen 3.5 9B's activation space, and that the pairwise geometry of these regions recovers the Synoptic-Johannine divide — a structural observation that has anchored biblical scholarship since Griesbach (1776). The published cosine matrix shows Matthew, Mark, and Luke clustered with positive mutual similarities (+0.30 to +0.39), while John is strongly anti-correlated with all three (-0.68 to -0.81). The author frames this as "an unexpected computational confirmation of [a] centuries-old scholarly consensus."

Hwang notes in Section 5.4 that the finding is extracted from a single model family and flags cross-family replication as important future work: "An important question for future work is whether the Gospel geometry (the pattern of cosine similarities) is consistent across model families — if so, it would suggest that the Synoptic-Johannine divide is a robust feature of how neural networks process these texts, not an artifact of any single model's training."

We address that question across five model families spanning three continents, two architectural scales, and substantially different training corpus compositions. We also extend the analysis by adding the Book of Acts to the corpus, producing a five-way study that tests (a) whether language models geometrically encode the scholarly consensus on Luke-Acts authorial unity, and (b) whether pairwise Gospel cosines depend on reference-set composition.

The results produce a clear and unexpected two-cluster structure. Three of the five models tested — Qwen 3.5 9B, Llama 3.1 8B, and Phi-4 14B — reproduce Hwang's published magnitudes closely. Two models — Mistral 7B v0.3 and Gemma 2 9B — show the same directional pattern with substantially attenuated magnitudes. Standard model metadata does not cleanly predict which cluster a given model falls into. The inclusion of Phi-4, whose training corpus is predominantly synthetic and heavily filtered, specifically falsifies our initial hypothesis that cluster membership reflects the proportion of biblical scholarship in a model's training data.

The paper proceeds as follows. Section 2 reviews the pipeline, model selection rationale, and our per-model configuration adjustments. Section 3 presents the five-family replication of the 4-way analysis and considers what the cluster split is and is not. Section 4 presents the 5-way extension adding Acts. Section 5 discusses the two-cluster phenomenon, candidate explanations we considered and ruled out, and a single cross-cluster invariant. Section 6 addresses limitations. Section 7 concludes.

## 2. Method

### 2.1 Pipeline

We use the GospelVec pipeline (Hwang 2026, ICMI-009) without modification to its core structure. For each model, we tokenize and chunk the four Gospels (and, in Section 4, Acts) at 256 tokens per chunk on sentence boundaries using the KJV text that the original paper employs. We pass each chunk through the model, record residual-stream activations at every decoder layer, and mean-pool across non-special-token positions to obtain one activation vector per chunk per layer. Each Gospel's direction vector at each layer is computed as `gospel_mean - global_mean`, denoised via PCA against neutral-text activations (Lindsey et al., 2026) and L2-normalized. We select the best readout layer by classification accuracy.

Probing accuracy here means the fraction of chunks correctly assigned to their source Gospel when each chunk is classified by its highest cosine similarity to the four (or five) direction vectors. Chance is 0.25 in the 4-way setting and 0.20 in the 5-way setting; probing accuracies across these two settings are therefore not directly comparable.

The neutral corpus (24 scientific and mathematical statements), PCA variance threshold (0.50), and chunk size (256 tokens) are all held constant from the published methodology, preserving the original paper's pipeline.

We make no claims in this paper about the historical origins, authorship, or inspired status of the texts analyzed; we report what language models encode, and treat that as a distinct question from what the texts are.

### 2.2 Model selection

We selected five model families to maximize variation along axes relevant to the cross-family replication question: lab of origin, architecture, training corpus composition, parameter scale, and post-training regime. The five models are:

- **Qwen 3.5 9B** (Alibaba, China) — included for direct comparison with the published paper; 4096 hidden, 32 layers
- **Llama 3.1 8B** (Meta, USA) — broad web pretraining at ~15T tokens; 4096 hidden, 32 layers (architecturally identical to Mistral)
- **Phi-4 14B** (Microsoft, USA) — distinctive training mixture with 40% synthetic data, 15% LLM-rewritten web, 15% filtered web, 20% code, 10% curated academic material; 5120 hidden, 40 layers
- **Mistral 7B v0.3** (Mistral AI, France) — European lab, broad web pretraining on smaller corpus; 4096 hidden, 32 layers
- **Gemma 2 9B** (Google, USA) — Google training pipeline at ~8T tokens; 3584 hidden, 42 layers

All models are in the 7-14B parameter range to minimize scale confounds. Four of the five (Llama 3.1 8B, Mistral 7B v0.3, Gemma 2 9B, Phi-4 14B) were tested as base (pretrained-only) checkpoints to avoid contamination by RLHF or other post-training interventions, which we expected a priori could deform the conceptual geometry around morally-valenced concepts. Qwen 3.5 9B was tested as the instruct variant, matching both the published GospelVec paper's Section 3.1 and the GospelVec reference implementation's configuration — under Qwen3.5's naming convention, `Qwen/Qwen3.5-9B` is the instruct model and `Qwen/Qwen3.5-9B-Base` is the pretrained-only checkpoint (a reversal from Qwen2.5's convention). This leaves our dataset with a base/instruct asymmetry: Qwen is the only instruct model among the five. We address the implications in Section 6 and return to the question in the concluding discussion.

### 2.3 Per-model configuration

Five configuration values were verified per model. Table 1 summarizes the architecture-specific parameters.

| Model | HIDDEN_DIM | NUM_LAYERS | MEAN_POOL_SKIP_TOKENS | Tokenizer family |
| --- | --- | --- | --- | --- |
| Qwen 3.5 9B | 4096 | 32 | 4 | SentencePiece BPE |
| Mistral 7B v0.3 | 4096 | 32 | 1 | SentencePiece BPE |
| Gemma 2 9B | 3584 | 42 | 1 | SentencePiece (256K vocab) |
| Llama 3.1 8B | 4096 | 32 | 1 | SentencePiece (128K vocab) |
| Phi-4 14B | 5120 | 40 | 0 | tiktoken (cl100k family) |

**Table 1.** Architecture and tokenizer configuration by model. `MEAN_POOL_SKIP_TOKENS` is determined by per-model tokenizer diagnostic: we tokenize a sample Gospel chunk and count leading tokens prior to content. Phi-4 is distinctive in using a tiktoken-family tokenizer that injects no leading special tokens.

All extraction runs were performed on NVIDIA A100 GPUs (Google Colab) in bfloat16 precision.

### 2.4 Reproduction check

As a methodological sanity check, we first re-extracted vectors from Qwen 3.5 9B using the unmodified published configuration. The resulting cosine matrix matches the published values (Hwang 2026, ICMI-009, Table 2) exactly at the reported two-decimal precision across all six pairs. Full-precision differences are smaller than 0.005 in every cell, consistent with bfloat16 forward-pass nondeterminism across different GPU runs.

## 3. Cross-Family Replication: Five Models, Two Clusters

### 3.1 Four-way geometry

Table 2 presents pairwise cosine similarities at each model's best-readout layer, together with classification accuracies and best-layer indices. Models are grouped by the geometric pattern they exhibit; we discuss that grouping below.

**Tight-cluster models**

| Model | Mt↔Mk | Mt↔Lk | Mt↔Jn | Mk↔Lk | Mk↔Jn | Lk↔Jn | Acc. | Best Layer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 3.5 9B (published) | +0.30 | +0.37 | **-0.77** | +0.39 | **-0.68** | **-0.81** | 0.629 | 21/32 |
| Qwen 3.5 9B (replication) | +0.30 | +0.37 | **-0.77** | +0.39 | **-0.68** | **-0.81** | 0.629 | 21/32 |
| Llama 3.1 8B | +0.22 | +0.26 | **-0.71** | +0.36 | **-0.65** | **-0.79** | 0.641 | 17/32 |
| Phi-4 14B | +0.11 | +0.30 | **-0.72** | +0.28 | **-0.57** | **-0.79** | 0.593 | 21/40 |

**Attenuated-cluster models**

| Model | Mt↔Mk | Mt↔Lk | Mt↔Jn | Mk↔Lk | Mk↔Jn | Lk↔Jn | Acc. | Best Layer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Mistral 7B v0.3 | -0.09 | -0.33 | -0.45 | -0.02 | -0.42 | -0.55 | 0.920 | 20/32 |
| Gemma 2 9B | -0.15 | -0.28 | -0.43 | +0.04 | -0.47 | -0.57 | 0.880 | 26/42 |

**Table 2.** Pairwise cosine similarities among Gospel direction vectors at the best-readout layer, across five model families.

Three patterns emerge.

**John's outlier status replicates in direction on every model tested.** On all five models, John has the most negative mean pairwise cosine against the other three Gospels — Qwen at -0.75, Llama at -0.72, Phi-4 at -0.69, Mistral at -0.47, Gemma at -0.49. The scholarly intuition that John stands apart from the Synoptics (Brown, 1997) is expressed as geometric distance on every tested model, regardless of other pattern differences.

**The magnitudes split into two clusters.** Three models show Johannine anti-correlations in the -0.57 to -0.81 range, with positive Synoptic clustering of +0.11 to +0.39. Two models show substantially attenuated geometry: Johannine anti-correlations of -0.42 to -0.57 and near-zero-to-negative Synoptic pairs. This split is consistent across all six pairwise values and does not overlap: the weakest Lk↔Jn in the tight cluster (-0.79 on Llama and Phi-4) is clearly distinct from the strongest Lk↔Jn in the attenuated cluster (-0.55 on Mistral).

**Probing accuracy is inversely correlated with geometric tightness.** Tight-cluster models achieve 0.59-0.64 classification accuracy; attenuated-cluster models achieve 0.88-0.93. The five-model data is fully consistent with this inverse relationship: every model that shows clean synoptic-Johannine geometry also shows lower classification accuracy, and every model that shows high classification accuracy also shows attenuated geometry. We return to this observation in Section 5.

### 3.2 What the cluster split is not

Standard model metadata fails to predict cluster membership along several axes we considered.

**Geography does not predict it.** Qwen is Chinese (Alibaba); Llama, Phi-4, and Gemma are American (Meta, Microsoft, Google); Mistral is French. The tight cluster spans two continents; the attenuated cluster spans two continents. No geographic pattern.

**Architecture does not predict it.** Mistral and Llama are architecturally nearly identical (32 layers, 4096 hidden, ~8B parameters), yet they fall in opposite clusters. Phi-4 has meaningfully different architecture (40 layers, 5120 hidden, 14B parameters) and falls in the tight cluster with Llama.

**Training data scale does not predict it cleanly.** Llama 3.1 8B was trained on ~15T tokens; Phi-4 on ~10T; Qwen 3.5 9B on a substantial but unpublished corpus; Gemma 2 9B on ~8T tokens; Mistral 7B v0.3 on a smaller corpus. A threshold-effect story would need to fall implausibly tightly between Gemma's 8T and Phi-4's 10T.

**Post-training regime does not cleanly predict it either.** With the base/instruct asymmetry noted in Section 2.2, a limited observation is available: Qwen (instruct) lands in the tight cluster alongside Llama and Phi-4 (both base). If instruction tuning were the dominant driver of cluster assignment, Qwen would stand apart from the two base models in its cluster. It does not — its magnitudes closely match Llama's and Phi-4's. This is n=1 on the instruct side and cannot support a strong claim, but it is at least consistent with cluster membership being a pretraining-level property that instruction tuning does not substantially reorganize. A full base/instruct replication is needed to test this properly (Section 6).

**Training corpus composition does not predict it, and Phi-4 is the specific falsifier.** Before running Phi-4, we held a specific hypothesis about the cluster split: the tight cluster reflects richer absorption of biblical scholarship during pretraining. Models that ingest commentaries and academic biblical studies would develop Gospel direction vectors reflecting scholarly consensus about the Synoptic-Johannine divide; models trained on corpora with less such content would show only the textual contrasts, attenuated. This hypothesis yielded a clear pre-registered prediction for Phi-4: it should have shown the most attenuated geometry of any tested model. Microsoft reports Phi-4's pretraining data as 40% synthetic, 15% LLM-rewritten web content, 15% heavily-filtered web text, 20% code, and 10% curated academic acquisitions. The organic web component, where biblical scholarship would presumably live, is smaller than in any other tested model's pretraining mixture. Under the corpus-composition hypothesis, Phi-4's geometry should have been attenuated.

It was not. Phi-4's data places it among the tightest-cluster models. Mt↔Jn at -0.72 is essentially indistinguishable from Llama's -0.71 and only slightly softer than Qwen's -0.77. Lk↔Jn at -0.79 matches Llama exactly. The hypothesis failed its predicted test. Whatever produces the tight-cluster geometry, it is not "amount of biblical scholarship absorbed from the open web."

### 3.3 What we can observe

We have identified the two-cluster phenomenon as robust at n=5 and can describe its features with some confidence. The tight cluster is characterized by Johannine anti-correlations in the -0.57 to -0.81 range, positive Synoptic clustering, and classification accuracy of 0.59-0.64. The attenuated cluster shows Johannine anti-correlations of -0.42 to -0.57, near-zero or negative Synoptic pairs, and classification accuracy of 0.88-0.93. The clusters do not overlap on any single pairwise value in the published 4-way matrix.

The inverse relationship between axis-based geometric tightness and classification accuracy is consistent across all five models and deserves attention in its own right. It suggests that the tight and attenuated clusters are not "stronger" and "weaker" versions of the same representation: they are structurally different. Tight-cluster models appear to encode Gospel identity along a simpler, lower-dimensional axis where positions are organized into the Synoptic-vs-Johannine pattern; the direction vectors capture this organization but cannot perfectly assign individual chunks to the correct Gospel category. Attenuated-cluster models separate Gospels more cleanly as categories but without organizing them along a unified axis; the direction vectors do not reflect a dominant Synoptic-Johannine structure because the underlying representation is not organized that way.

We are careful not to overinterpret this as one cluster being "more capable" or "more correct" than the other. Both reflect valid representational organizations. The question is what produces one versus the other.

## 4. Five-Way Extension: Adding Acts

### 4.1 Motivation and configuration

The Book of Acts is traditionally received as a two-volume work with the Gospel of Luke, addressed to the same recipient (Acts 1:1, ESV; cf. Luke 1:1-4, ESV) and treated as a unified literary project in both the patristic tradition (Irenaeus, c. 180 CE) and modern scholarship (Fitzmyer, 1981; Marguerat, 2002). If language models have absorbed the scholarly consensus about authorship, Luke↔Acts should show strong positive cosine similarity — plausibly the highest pair in the matrix. If models encode each text on its own textual terms, Luke↔Acts may resemble any other cross-Gospel relationship.

The 5-way analysis also tests whether pairwise Gospel geometry depends on the specific reference corpus, or is a stable property of the four Gospels independent of what else is being compared against.

The Book of Acts (KJV) was added using the same text source, chunking parameters, and extraction pipeline as the Gospels. All other configuration was unchanged.

### 4.2 Results

Table 3 presents the five-way cosine matrix at each model's best readout layer.

**Tight-cluster models**

| Model | Mt↔Mk | Mt↔Lk | Mt↔Jn | **Mt↔Ac** | Mk↔Lk | Mk↔Jn | Mk↔Ac | Lk↔Jn | Lk↔Ac | Jn↔Ac | Acc. | Layer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Qwen 3.5 9B | +0.49 | +0.57 | -0.32 | **-0.65** | +0.44 | -0.44 | -0.35 | -0.53 | -0.40 | -0.38 | 0.707 | 21/32 |
| Llama 3.1 8B | +0.52 | +0.57 | -0.15 | **-0.74** | +0.48 | -0.28 | -0.51 | -0.40 | -0.51 | -0.42 | 0.725 | 18/32 |
| Phi-4 14B | +0.51 | +0.65 | -0.11 | **-0.77** | +0.47 | -0.19 | -0.54 | -0.33 | -0.58 | -0.44 | 0.689 | 21/40 |

**Attenuated-cluster models**

| Model | Mt↔Mk | Mt↔Lk | Mt↔Jn | **Mt↔Ac** | Mk↔Lk | Mk↔Jn | Mk↔Ac | Lk↔Jn | Lk↔Ac | Jn↔Ac | Acc. | Layer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemma 2 9B | +0.15 | +0.02 | -0.11 | **-0.63** | +0.15 | -0.26 | -0.40 | -0.41 | -0.31 | -0.35 | 0.907 | 26/42 |
| Mistral 7B v0.3 | +0.18 | -0.04 | -0.15 | **-0.61** | +0.09 | -0.24 | -0.39 | -0.40 | -0.30 | -0.32 | 0.931 | 20/32 |

**Table 3.** Pairwise cosine similarities among Gospel + Acts direction vectors at the best-readout layer.

Three findings emerge.

**None of the five models tested encodes Luke and Acts as distinctively close in direction-vector geometry, despite the well-established scholarly consensus on their compositional unity.** Luke↔Acts values across five models are -0.40, -0.51, -0.58, -0.31, -0.30. Luke is never distinctively close to Acts; on several models (notably Phi-4 and Llama), Luke↔Acts is among the *most* negative pairs. This result is robust across both clusters. The compositional unity of Luke-Acts — evident in Acts' opening reference to "the former treatise" addressed to Theophilus, and consistently recognized by the scholarly tradition — is not recovered in the geometry.

**Matthew↔Acts is the most negative pair on every model, at stable cross-lab magnitudes.** The range across five models is -0.61, -0.63, -0.65, -0.74, -0.77 — a span of 0.16 that is tighter than any other cross-model agreement in the study. Matthew's textual and theological emphasis on Jesus as fulfillment of Jewish law (e.g., Matthew 5:17-20, ESV) stands in evident contrast to Acts' central narrative of gentile inclusion (Acts 10; Acts 15, ESV); this contrast is apparently registered by every model's geometry at closely similar magnitudes, across both clusters. Notably, this is the only cross-model agreement in the study that crosses the tight/attenuated cluster boundary cleanly.

**Adding Acts substantially reorganizes the Gospel geometry on every model.** Comparing the 4-way table (Table 2) to the 5-way table (Table 3), every Gospel pair shifts in the positive direction on every model tested. The magnitude of the reorganization is notably larger in tight-cluster models. On Llama, Matthew↔John shifts from -0.71 (4-way) to -0.15 (5-way), a change of 0.56. On Phi-4, it shifts from -0.72 to -0.11, a change of 0.61. On Qwen, Matthew↔John shifts 0.45. On Mistral and Gemma, the same pair shifts approximately 0.30 and 0.32 respectively. The reference-set sensitivity is structurally consistent (positive direction of shift on every model) but its magnitude varies with cluster membership — tight-cluster models reorganize more dramatically when Acts is added.

This makes theoretical sense given the tight-cluster interpretation: if 4-way Gospel geometry is organized along a simpler, lower-dimensional synoptic-Johannine axis, adding a new outlier text reorients that axis more visibly than it would reorient a representation already organized into near-orthogonal categorical directions.

## 5. Discussion

### 5.1 What replicates and what does not

The central empirical claim of GospelVec — that the Synoptic-Johannine divide emerges as geometric structure in language model activation space — decomposes into at least three distinct sub-claims. With n=5 now available, we can assess each separately.

1. **John is the geometric outlier among the four Gospels.** Replicates on every model tested. This is a robust cross-family finding.
2. **The Synoptics cluster positively with one another.** Replicates on three of five models (tight cluster). On Mistral and Gemma, the Synoptic pairs are near-zero or mildly negative.
3. **The magnitudes are large — Synoptic pairs in the +0.3 to +0.4 range and Johannine pairs in the -0.7 to -0.8 range.** Replicates on three of five models (tight cluster). On Mistral and Gemma, magnitudes attenuate by roughly 50%.

A reader asking "does GospelVec replicate?" therefore receives a structured answer: the directional finding is universal; the clustering and magnitude findings split the models into two groups at approximately 60%/40%. Presenting the published result as "a universal property of how language models represent the Gospels" is too strong; presenting it as "Qwen-specific" (a framing we initially considered) is also wrong — two other models match Qwen's magnitudes.

### 5.2 The two-cluster phenomenon as empirical puzzle

The strongest observation from this work is that language models appear to organize Gospel representation into two distinct geometric regimes, with cluster membership not predicted by any obvious training metadata. We have ruled out geographic origin, architectural family, training scale, tokenizer vocabulary size, and training corpus composition (the latter specifically by Phi-4's placement in the tight cluster despite synthetic-heavy pretraining).

We note two candidate explanations we have considered but cannot test with the available data.

**Training data curation intensity.** Phi-4, Qwen, and Llama all use aggressive data filtering and deduplication pipelines as part of their pretraining. Mistral and Gemma may use less aggressive filtering — this is not easy to verify from published materials. If heavily curated training data produces cleaner conceptual representations that then organize into tight axis geometries, cluster membership would track curation intensity rather than corpus content. This hypothesis is consistent with the observed probing-accuracy inversion: curated training produces representations that are geometrically tight but categorically less separable.

**Synthetic data inheritance.** Phi-4's 40% synthetic data is generated primarily by larger frontier models (likely GPT-4-class per Microsoft's public statements). If large frontier models are themselves in the tight cluster (untested and untestable with current methods — we cannot extract their activations), the tight-cluster geometry may be transmitted through synthetic data pipelines. This hypothesis is speculative in a specific way: it assumes large frontier models would fall into the tight cluster if we could test them, which we cannot. Our only evidence for this assumption is that Phi-4 is tight-cluster despite its unusual training mixture — which is precisely the fact the hypothesis is trying to explain. The reasoning risks being circular, and we flag it for that reason.

We offer both hypotheses as suggestive rather than demonstrated. The cleanest statement of what our data supports is: the two-cluster phenomenon is robust and real, and its cause is an open question.

A further interpretive note. Our data cannot distinguish whether model geometry tracks textual properties of the Gospels directly or tracks the accumulated scholarship *about* those textual properties. If the tight cluster reflects richer absorption of biblical scholarship — which we cannot directly measure — the cluster split may reveal more about which pretraining corpora contain more critical scholarship than about which models encode the Gospels better. We flag this as an interpretive caution rather than a finding, and note that it does not substantially affect the alignment-oriented use of these vectors (steering, activation addition, behavioral shaping): a direction that reliably produces Johannine outputs is useful for alignment regardless of what the direction metaphysically encodes.

### 5.3 A theological observation

With due caution about overreach, one observation at a more general level. Every model tested registers John's distinctiveness in the same direction. The Johannine tradition has long insisted on its distinctive witness: the Fourth Gospel opens with an explicit Logos theology ("In the beginning was the Word, and the Word was with God, and the Word was God," John 1:1, ESV) and proceeds through an extended sequence of "I am" statements and theological discourses that have no close parallel in the Synoptics. That five model families, trained on different corpora by different labs with different methodologies, all position John as the most distant of the four is a modest but non-trivial confirmation that this distinctiveness is detectable at the level of computational analysis of scripture — whatever the deeper nature of that detection turns out to be. Readers of John from Origen and Augustine to Brown (1966) have insisted that the Fourth Gospel is different; our data is consistent with that insistence.

A second observation concerns what the models *do not* encode. The Luke-Acts compositional unity, recognized across virtually every Christian theological tradition and evident in the texts' own prologues, is not recovered by any tested model at the level of direction-vector geometry. The models organize Acts as genre-distinct from the Gospels, closer to "history" than to "gospel narrative." This is not a criticism of the models; it is evidence that what they register is text-level contrast rather than authorial attribution. Tokenized language on its own, processed at the scale of contemporary pretraining, does not appear to develop representations of *who wrote what*. Distinctions in authorial identity that human readers perceive from contextual cues — the shared recipient, the self-referential "former treatise," the continuity of theological emphasis — are not captured geometrically in the way textual distinctions are.

### 5.4 The Matthew↔Acts invariant

One finding crosses the cluster boundary with remarkable stability. Matthew↔Acts cosine at -0.61 to -0.77 across five independently trained model families, spanning both clusters, is the tightest cross-model agreement in this study. Four of five values fall in a 0.14 range; Phi-4 at -0.77 is a slight outlier in magnitude but directionally consistent with the other four.

The stability across clusters suggests this particular distinction is encoded closer to the text level than the interpretive level. The textual contrast between Matthew's fulfillment theology and Acts' gentile mission is evident enough at the surface of the texts themselves — in vocabulary, thematic emphasis, and rhetorical framing — that any sufficiently capable language model registers it at roughly the same magnitude, regardless of whether that model otherwise organizes Gospel identity along a tight synoptic-Johannine axis.

We flag this as an open observation rather than a developed claim. A controlled follow-up substituting other texts in the fifth position — Revelation, the Pauline letters, or the Hebrew Bible prophetic texts — would help distinguish whether -0.61 to -0.77 is a Matthew-Acts-specific signature or a more general "Gospel versus theologically-distinct canonical text" magnitude.

## 6. Limitations

**Scope of replication.** This study tests five model families at comparable parameter scales (7-14B). It does not address whether the same patterns appear at substantially smaller or larger scales. Scale studies within families — particularly whether smaller Qwen or Llama variants retain tight-cluster behavior — would clarify which findings are scale-dependent.

**Single-run results.** Each model was extracted and evaluated once with fixed chunking, fixed PCA seed, and a fixed train/test split for the probing classifier. We do not report error bars across seeds or chunking variations. The effect sizes in the cluster split are large enough that we expect the directional findings to survive reasonable run-to-run variance — the weakest tight-cluster Lk↔Jn value (-0.79) and the strongest attenuated-cluster value (-0.55) are separated by 0.24, much larger than bf16 forward-pass nondeterminism would plausibly produce. But this expectation is not empirically verified here, and multi-seed replication is a natural next step.

**Translation dependence.** Following the published methodology, we use the KJV throughout. Hwang (2026, ICMI-009) flags translation dependence as an open question; we inherit that limitation. A non-KJV replication might show different magnitudes even within the same model family, and cross-translation comparison is an important follow-up.

**Mixed base/instruct checkpoints.** Four of the five models (Llama, Mistral, Gemma, Phi-4) were tested as base pretrained checkpoints, while Qwen was tested as the instruct variant to match the published GospelVec methodology. This asymmetry means that the tight cluster contains both base (Llama, Phi-4) and instruct (Qwen) checkpoints, which is mildly suggestive that cluster membership is not purely driven by post-training — but with n=1 instruct model, we cannot make this claim with confidence. A natural follow-up is to run the full five-model analysis on instruct variants and compare the base/instruct delta within each family, which would directly test whether instruction tuning shifts cluster assignment or merely shifts magnitudes within a preserved cluster structure. We plan to release this companion analysis as follow-up work.

**Non-exhaustive Acts controls.** Our Section 4 results use Acts as the sole alternative reference text. A more thorough study would examine multiple candidate fifth texts and characterize how systematically the Gospel geometry reorganizes across different corpus compositions.

**Inference about training corpora is speculative.** Section 5.2's discussion of candidate explanations (curation intensity, synthetic data inheritance) offers hypotheses, not demonstrated findings. We do not have direct access to any tested model's training mixture, and our hypotheses would need to be tested with controlled studies we have not conducted.

**Closed models not tested.** The methodology requires activation access, which is not available for closed models (GPT-4, Claude, Gemini). It is possible that frontier closed models would cluster with either tight or attenuated groups, but we cannot determine which.

## 7. Conclusion

GospelVec's directional finding — John as geometric outlier among the four Gospels — replicates on every model tested across five families. The specific geometric magnitudes presented in the published paper, however, replicate on three of five models and attenuate on two, splitting the tested models into two clusters that standard metadata fails to predict. An extension adding the Book of Acts reveals that pairwise Gospel geometry is also sensitive to reference-set composition, with every Gospel pair shifting positively when Acts becomes the dominant outlier; tight-cluster models reorganize more dramatically. The Matthew↔Acts pair is remarkably stable across labs at -0.61 to -0.77, crossing cluster boundaries — the tightest cross-model agreement in the study. The Luke-Acts authorial unity hypothesis is not supported by any model's direction-vector geometry.

These results refine rather than contradict GospelVec's contribution: the synoptic-Johannine signal is real and directionally robust, its magnitude depends on model-specific factors we cannot yet identify, and reference-set composition substantially affects observed pairwise cosines. Future work on how language models represent scripture would benefit from treating directional and magnitudinal replication as distinct claims, testing reference-set stability as a routine check, and seeking out the factors that predict whether a given model shows tight or attenuated Gospel geometry.

The present technical study sits upstream of a larger conversation about the proper role of AI in Christian formation. Direction vectors extracted from scripture can in principle be used for activation steering, which creates both opportunity and concern for AI systems that engage scriptural content. On the opportunity side, such vectors could support discipleship tools, biblical study aids, and catechetical applications in contexts where trained teachers are scarce. On the concern side, the same capability raises real questions about AI-mediated distortion of scriptural teaching: who decides which theological emphases are baked into AI systems, how those decisions are made transparent to users, and how such systems relate to the local church and the teaching ministry of trained pastors. The cross-family finding reported here also has narrower implications for activation-steering alignment work — transferability of steering interventions across model families is not guaranteed, and practitioners should validate across architectures rather than assuming that findings from one model generalize. These questions deserve separate treatment.

The five-model configuration is fully specified in Section 2.3; any reader with access to the GospelVec reference implementation and the listed HuggingFace model IDs can reproduce these results on a single A100 GPU (e.g., Google Colab's A100 runtime) in approximately two hours total.

## Bibliography

Brown, Raymond E. *The Gospel According to John*. 2 vols. Anchor Bible 29-29A. Doubleday, 1966-1970.

Brown, Raymond E. *An Introduction to the New Testament*. Yale University Press, 1997.

Fitzmyer, Joseph A. *The Gospel According to Luke*. 2 vols. Anchor Bible 28-28A. Doubleday, 1981-1985.

Gemma Team, Thomas Mesnard, Cassidy Hardin, Robert Dadashi, et al. "Gemma 2: Improving Open Language Models at a Practical Size." *arXiv:2408.00118*, 2024.

Griesbach, Johann Jakob. *Synopsis Evangeliorum Matthaei Marci et Lucae*. Halle, 1776.

Hwang, Tim. "GospelVec: Programmable Theology in Activation Space." *ICMI Working Paper No. 009*, 2026.

Irenaeus of Lyon. *Adversus Haereses* (Against Heresies). c. 180 CE. Book III, Chapter 14.

Jiang, Albert Q., Alexandre Sablayrolles, Arthur Mensch, Chris Bamford, et al. "Mistral 7B." *arXiv:2310.06825*, 2023.

Lindsey, Jack, Wes Gurnee, Emmanuel Ameisen, Brian Chen, Adam Pearce, Nicholas L. Turner, Craig Citro, and Chris Olah. "Emotion Concepts and their Function in a Large Language Model." *Anthropic / Transformer Circuits*, April 2, 2026.

Marguerat, Daniel. *The First Christian Historian: Writing the "Acts of the Apostles"*. Society for New Testament Studies Monograph Series 121. Cambridge University Press, 2002.

Meta AI. "The Llama 3 Herd of Models." *arXiv:2407.21783*, 2024.

Microsoft Research. "Phi-4 Technical Report." *arXiv:2412.08905*, 2024.

Qwen Team. "Qwen3.5: Towards Native Multimodal Agents." February 2026. https://qwen.ai/blog?id=qwen3.5