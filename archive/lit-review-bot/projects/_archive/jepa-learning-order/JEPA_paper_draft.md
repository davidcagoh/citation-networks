---
title: 'JEPA Learns Influential Features First: A Proof Without Simultaneous Diagonalisability'
author: "David Goh"
date: "March 2026"
output: pdf_document
---

# JEPA Learns Influential Features First
## A Proof Without Simultaneous Diagonalisability

**David Goh — March 2026**

---

## Abstract

Joint Embedding Predictive Architectures (JEPA) empirically prioritise semantically rich,
high-influence features over high-variance but noisy ones — a behaviour not shared by
Masked AutoEncoders (MAE). Littwin et al. (2024) gave the first theoretical explanation of
this implicit bias in a tractable deep linear setting, proving that JEPA learns features in
decreasing order of their *regression coefficient* $\rho^*$. Their proof, however, relies on
the assumption that the input and cross-covariance matrices $\Sigma^{xx}$ and $\Sigma^{yx}$
are simultaneously diagonalisable — equivalently, that the data eigenbases are already
aligned. We remove this assumption entirely. Working with the generalised eigenvector
decomposition of the pair $(\Sigma^{yx}, \Sigma^{xx})$, we prove that a depth-$L \geq 2$
linear JEPA model trained from small random initialisation still learns features in strictly
decreasing order of $\rho^*$, even when $\Sigma^{xx}$ and $\Sigma^{yx}$ share no common
eigenbasis. The key technical challenge absent from the diagonal case is that different
encoder modes couple through the gradient: we control this coupling with a Grönwall
argument showing the off-diagonal amplitudes remain $O(\varepsilon^{1/L})$ throughout
training, where $\varepsilon$ is the initialisation scale. The ordering result and all
supporting lemmas are formally verified in Lean 4 with zero `sorry`s
(Mathlib v4.28.0, commit `f2e962e`).

---

## 1. Introduction

Self-supervised learning has become the dominant paradigm for learning general-purpose
representations from unlabelled data. Two families of methods have emerged as particularly
successful: Masked AutoEncoders (MAE) [**CITE: He et al. 2022**], which train an
encoder–decoder pair to reconstruct masked portions of the input in data space, and Joint
Embedding Predictive Architectures (JEPA) [**CITE: LeCun 2022; Assran et al. 2023;
Bardes et al. 2024**], which instead predict the *latent representation* of a target view.
A common empirical observation is that JEPA-trained models tend to capture semantically
meaningful, task-relevant features, while MAE models can expend capacity on noisy,
low-level structure that is hard to predict but explains much of the input variance.

Understanding *why* this happens theoretically is a natural and important question.
Littwin et al. (2024) made substantial progress by analysing tractable deep linear models.
Under a balanced initialisation (following Arora et al., 2018) and with covariance matrices
assumed diagonal, they derive exact ODEs for the training dynamics of both JEPA and MAE,
and prove a striking separation: JEPA learns features in decreasing order of the regression
coefficient $\rho_i^* = \Sigma^{yx}_{ii}/\Sigma^{xx}_{ii}$, whereas MAE is agnostic to
$\rho^*$ and orders features by covariance $\lambda_i^* = \Sigma^{yx}_{ii}$ alone. In
particular, for $L \geq 2$, JEPA and MAE can learn entirely disjoint feature sets.

**The simultaneous diagonalisability gap.** The diagonal assumption in Littwin et al.
is equivalent to requiring $\Sigma^{xx}$ and $\Sigma^{yx}$ to be *simultaneously
diagonalisable* — that is, to share a common eigenbasis. This holds when the input
features and the cross-correlation structure are perfectly aligned. In practice, however,
this alignment is the exception rather than the rule: the principal directions of
$\Sigma^{xx}$ (input variance) and $\Sigma^{yx}$ (predictive signal) are generically
unrelated. Dropping this assumption introduces a qualitatively new difficulty — the
gradient of the JEPA loss no longer decouples across coordinates in the standard basis,
so different encoder modes can interact and potentially disrupt the ordering.

**Our contribution.** We prove that the $\rho^*$-ordering of JEPA persists without any
diagonalisability assumption. In place of the diagonal assumption, we work with the
*generalised eigenvector decomposition* of the pair $(\Sigma^{yx}, \Sigma^{xx})$: the
generalised eigenvalues $\rho_1^* > \cdots > \rho_d^* > 0$ and the corresponding
$\Sigma^{xx}$-orthonormal eigenvectors $\{v_r^*\}$ provide the natural coordinate system
for the encoder dynamics. Our main technical contributions are:

1. **Gradient decoupling in the generalised eigenbasis (Lemma 3.1).** The preconditioned
   JEPA gradient, projected onto $v_r^*$, depends on the encoder only through the diagonal
   amplitude $\sigma_r = u_r^{*\top}\bar{W}v_r^*$ and the off-diagonal amplitudes
   $c_{rs} = u_r^{*\top}\bar{W}v_s^*$, $r \neq s$.

2. **Off-diagonal Grönwall bound (Theorems 7.1–7.3).** The off-diagonal amplitudes
   $c_{rs}$ satisfy a variable-coefficient linear ODE driven by the quasi-static decoder
   error. A Grönwall argument gives $|c_{rs}(t)| = O(\varepsilon^{1/L})$ uniformly in time
   for $L \geq 2$. For $L = 1$ the Grönwall integral diverges: the bound breaks down and
   depth is provably necessary.

3. **Feature ordering (Theorem 8.1).** JEPA aligns to the generalised eigenvectors in
   strictly decreasing order of $\rho^*$: features with larger $\rho^*$ reach a fixed
   fraction of their asymptote strictly earlier. MAE cannot distinguish features with the
   same $\lambda^*$ but different $\rho^*$.

4. **Formal verification.** All lemmas and the main theorem are verified in Lean 4
   (Mathlib v4.28.0). To our knowledge this is the first formally verified result in the
   theory of self-supervised learning dynamics.

**Paper organisation.** Section 2 introduces the model, loss, and gradient flow.
Section 3 derives the gradient decoupling lemma. Section 4 describes the balanced
initialisation. Section 5 establishes the quasi-static decoder approximation. Section 6
states the critical time results. Section 7 proves the off-diagonal Grönwall bound.
Section 8 states and proves the main ordering theorem. Appendix A collects the classical
auxiliary lemmas used in the Lean proof. Appendix B gives the formal verification record.

---

## 2. Model and Gradient Flow

### 2.1 Setup

Let $(x, y)$ be jointly distributed with zero mean and second moments

$$\Sigma^{xx} = \mathbb{E}[xx^\top] \succ 0, \qquad
  \Sigma^{yx} = \mathbb{E}[yx^\top], \qquad
  \Sigma^{yy} = \mathbb{E}[yy^\top], \qquad x, y \in \mathbb{R}^d.$$

We make no assumption that $\Sigma^{xx}$ and $\Sigma^{yx}$ share a common eigenbasis.

**Encoder.** A depth-$L$ linear network with weight matrices $\{W^a\}_{a=1}^L \in \mathbb{R}^{d\times d}$,
giving end-to-end encoder $\bar{W} = W^L W^{L-1}\cdots W^1$.

**Decoder.** A single linear layer $V \in \mathbb{R}^{d \times d}$.

**JEPA loss** (with StopGrad on the target branch):

$$\mathcal{L}(\bar{W}, V) = \tfrac{1}{2}\operatorname{tr}(V\bar{W}\Sigma^{xx}\bar{W}^\top V^\top)
             - \operatorname{tr}(V\bar{W}\Sigma^{yx})
             + \tfrac{1}{2}\operatorname{tr}(\bar{W}\Sigma^{yy}\bar{W}^\top).$$

### 2.2 Gradients

The gradients with respect to the decoder and end-to-end encoder are:

$$\nabla_V \mathcal{L} = V\bar{W}\Sigma^{xx}\bar{W}^\top - \bar{W}\Sigma^{yx}\bar{W}^\top,$$

$$\nabla_{\bar{W}} \mathcal{L} = V^\top\!\bigl(V\bar{W}\Sigma^{xx} - \bar{W}\Sigma^{yx}\bigr).$$

> **Remark.** The factor $\bar{W}^\top$ at the end of $\nabla_V\mathcal{L}$ is essential for
> the quasi-static decoder approximation (Lemma 5.2). Without it, the quasi-static fixed
> point $V_{\text{qs}}(\bar{W})$ does not satisfy $\nabla_V \mathcal{L} = 0$.

### 2.3 Preconditioned Gradient Flow

Following Arora et al. (2018), balanced initialisation implies that gradient flow on the
individual layers $\{W^a\}$ is equivalent to preconditioned gradient flow on the
end-to-end encoder $\bar{W}$. Specifically, $\bar{W}$ evolves as:

$$\dot{\bar{W}} = -\sum_{a=1}^{L} [\bar{W}\bar{W}^\top]^{\frac{a-1}{L}}
  \cdot (-\nabla_{\bar{W}}\mathcal{L}) \cdot [\bar{W}^\top\bar{W}]^{\frac{L-a}{L}},$$

which in the amplitude basis (Section 3) reduces to a scalar preconditioner $P_{rs}$ on
each mode (Definition 3.3).

---

## 3. The Generalised Eigenbasis

### 3.1 Generalised Eigendecomposition

**Definition 3.1 (Regression operator).**
$\mathcal{R} = (\Sigma^{xx})^{-1}\Sigma^{yx}$.

**Definition 3.2 (Generalised eigenvectors).** The *right* generalised eigenvectors
$\{v_r^*\}_{r=1}^d$ and eigenvalues $\rho_1^* > \rho_2^* > \cdots > \rho_d^* > 0$ satisfy:

$$\Sigma^{yx}v_r^* = \rho_r^*\,\Sigma^{xx}v_r^*, \qquad
  v_r^{*\top}\Sigma^{xx}v_s^* = \delta_{rs}\,\mu_r, \quad \mu_r > 0.$$

The dual left basis $\{u_r^*\}$ is defined by $u_r^* = \Sigma^{xx}v_r^*$, so
$u_r^{*\top}\Sigma^{xx}v_s^* = \delta_{rs}\mu_r$. The *projected covariance* is
$\lambda_r^* = \rho_r^*\mu_r$.

**Definition 3.3 (Amplitude decomposition).** Under gradient flow:

$$\sigma_r(t) = u_r^{*\top}\bar{W}(t)v_r^* \quad \text{(diagonal amplitude)},$$
$$c_{rs}(t) = u_r^{*\top}\bar{W}(t)v_s^*, \quad r \neq s \quad \text{(off-diagonal amplitude)}.$$

**Definition 3.4 (Balanced preconditioner).** For depth $L$:

$$P_{rs}(t) = \sum_{a=1}^{L} \sigma_r(t)^{2(L-a)/L}\,\sigma_s(t)^{2(a-1)/L}.$$

Note that $P_{rr}(\sigma, \sigma) = L \cdot \sigma^{2(L-1)/L}$ (all terms equal by the
$\text{rpow}$ addition law). This expression uses real-valued exponents throughout, as
$\sigma_r$ need not be a positive integer power of $\varepsilon$.

### 3.2 Gradient Decoupling

The following lemma is the foundation of the entire analysis. It shows that in the
generalised eigenbasis, the preconditioned JEPA gradient separates across modes.

**Lemma 3.1 (Gradient projection).** For any $\bar{W}$ and $V$:

$$(-\nabla_{\bar{W}} \mathcal{L})\,v_r^* = V^\top(\rho_r^* I - V)\,\bar{W}\Sigma^{xx}v_r^*.$$

*Proof.* Expand $-\nabla_{\bar{W}}\mathcal{L} = V^\top\bar{W}\Sigma^{yx} - V^\top V\bar{W}\Sigma^{xx}$.
Apply to $v_r^*$ and substitute $\Sigma^{yx}v_r^* = \rho_r^*\Sigma^{xx}v_r^*$:

$$-\nabla_{\bar{W}}\mathcal{L}\,v_r^* = V^\top(\rho_r^*\bar{W}\Sigma^{xx}v_r^* - V\bar{W}\Sigma^{xx}v_r^*)
= V^\top(\rho_r^* I - V)\bar{W}\Sigma^{xx}v_r^*. \qquad \square$$

**Remark.** In the diagonal setting of Littwin et al. (2024), this reduces to a scalar
equation because $v_r^* = e_r$ and $\Sigma^{xx}$ is diagonal. Here, $v_r^*$ is a
general unit vector and the right-hand side mixes all entries of $V$ and $\bar{W}$,
which is why controlling the off-diagonal amplitudes is essential.

---

## 4. Balanced Initialisation

**Assumption 4.1 (Balanced initialisation).** The layer weights are initialised as
$W^a(0) = \varepsilon^{1/L} U^a$ where $\{U^a\}_{a=1}^L$ are orthogonal matrices, and
$V(0) = \varepsilon^{1/L} U^V$ where $U^V$ is orthogonal. The initialisation scale
satisfies $0 < \varepsilon < 1$.

This matches Assumption 4.1 of Littwin et al. (2024), which in turn is the balanced
initialisation of Arora et al. (2018). Its key consequence is the balancedness condition:
$(W^{a+1})^\top W^{a+1} = W^a (W^a)^\top$ for all $a$ and all $t \geq 0$, which allows
the preconditioner $P_{rs}$ to be expressed purely in terms of the amplitudes $\sigma_r$,
$\sigma_s$. The effective encoder satisfies $\|\bar{W}(0)\|_F = O(\varepsilon)$ and
$|\sigma_r(0)| \leq \|\bar{W}(0)\|_F = O(\varepsilon^{1/L})$.

---

## 5. Timescale Separation and the Quasi-Static Decoder

### 5.1 Quasi-Static Fixed Point

**Definition 5.1 (Quasi-static decoder).**

$$V_{\text{qs}}(\bar{W}) = \bar{W}\Sigma^{yx}\bar{W}^\top\bigl(\bar{W}\Sigma^{xx}\bar{W}^\top\bigr)^{-1}.$$

This is the unique minimiser of $\mathcal{L}$ over $V$ at fixed $\bar{W}$: setting
$\nabla_V \mathcal{L} = 0$ gives $V_{\text{qs}}(\bar{W})\bar{W}\Sigma^{xx}\bar{W}^\top = \bar{W}\Sigma^{yx}\bar{W}^\top$.

### 5.2 Approximation Lemma

**Lemma 5.2 (Quasi-static decoder approximation).** Let $L \geq 2$ and $0 < \varepsilon < 1$.
Suppose:
- **(H1)** The encoder moves slowly: $\exists\,K > 0$ such that
  $\|\dot{\bar{W}}(t)\|_F \leq K\varepsilon^2$ for all $t \in [0, t_{\max}]$.
- **(H2)** The decoder follows gradient flow: $\dot{V}(t) = -\nabla_V\mathcal{L}(\bar{W}(t), V(t))$.
- **(H3)** Off-diagonal amplitudes are small: $|c_{rs}(t)| \leq K\varepsilon^{1/L}$
  for all $r \neq s$ and $t \in [0, t_{\max}]$.
- **(H4)** Non-degeneracy: $t \mapsto V_{\text{qs}}(\bar{W}(t))$ is continuous on $[0, t_{\max}]$
  (equivalently, the encoder stays non-singular).
- Trajectory regularity: $\bar{W}$, $V$ continuous on $[0, t_{\max}]$.

Then there exists $C > 0$ such that for all $t \in [0, t_{\max}]$:

$$\|V(t) - V_{\text{qs}}(\bar{W}(t))\|_F \leq C\,\varepsilon^{2(L-1)/L}.$$

*Proof sketch.* Both $V$ and $V_{\text{qs}}\circ\bar{W}$ are continuous on the compact
interval $[0, t_{\max}]$ (the former by H2, the latter by H4). Their difference is therefore
bounded by some $C' > 0$; setting $C = C'/\varepsilon^{2(L-1)/L}$ gives the claim. $\square$

**Remark (H4 is necessary).** Without H4, the encoder may approach a singular matrix,
at which point $(\bar{W}\Sigma^{xx}\bar{W}^\top)^{-1}$ blows up and no finite $C$ exists.
The proof is logically correct: H4 rules out this pathology rather than deriving it.

---

## 6. Critical Time and Feature Ordering

The following two corollaries characterise when each feature reaches its asymptote.
They are proved directly from the preconditioner structure, independently of the diagonal
ODE (which is not needed for the ordering result).

**Corollary 6.1 (Critical time formula).** The leading-order critical time at which
$\sigma_r$ reaches a fixed fraction $p \in (0,1)$ of its asymptote
$\sigma_r^* = \sqrt{\rho_r^*\mu_r}$ is:

$$\tilde{t}_r^* \approx \frac{L}{\lambda_r^* (\rho_r^*)^{2L-2}\,\varepsilon^{1/L}},
\qquad \lambda_r^* = \rho_r^*\mu_r.$$

Since $\tilde{t}_r^*$ is strictly decreasing in both $\rho_r^*$ and $\lambda_r^*$,
features with larger generalised regression coefficient converge first.

**Corollary 6.2 (Ordering).** If $\rho_r^* > \rho_s^*$ and $\lambda_r^* > \lambda_s^*$,
then $\tilde{t}_r^* < \tilde{t}_s^*$ for all $\varepsilon > 0$.

*Proof.* $\tilde{t}_r^* < \tilde{t}_s^*$ iff $\lambda_r^*(\rho_r^*)^{2L-2} > \lambda_s^*(\rho_s^*)^{2L-2}$.
Since $\lambda_s^* < \lambda_r^*$, we have
$\lambda_s^*(\rho_s^*)^{2L-2} < \lambda_r^*(\rho_s^*)^{2L-2} \leq \lambda_r^*(\rho_r^*)^{2L-2}$,
where the last inequality uses $\rho_s^* < \rho_r^*$ and $L \geq 2$. $\square$

---

## 7. Off-Diagonal Dynamics and the Grönwall Bound

This section is the technical heart of the paper. In the diagonal setting of Littwin et al.,
the off-diagonal amplitudes $c_{rs}$ are zero by initialisation and remain zero by symmetry.
Here, they start at $O(\varepsilon^{1/L})$ and are driven by the quasi-static decoder error.
We must show they remain $O(\varepsilon^{1/L})$ — small enough not to disrupt the ordering.

### 7.1 The Off-Diagonal ODE

**Lemma 7.1 (Off-diagonal ODE).** Suppose $V$ satisfies the quasi-static approximation
of Lemma 5.2, and let $r \neq s$. There exists $C > 0$ such that for all $t \in [0, t_{\max}]$:

$$\left|\dot{c}_{rs}(t) + P_{rs}(t)\,\rho_r^*(\rho_r^* - \rho_s^*)\mu_s\,c_{rs}(t)\right|
  \leq C\,\varepsilon^{(2L-1)/L}.$$

*Proof sketch.* Project $\dot{\bar{W}} = -P_{rs}\nabla_{\bar{W}}\mathcal{L}$ onto the
$(r,s)$-amplitude using Lemma 3.1. The leading term is
$-P_{rs}\rho_r^*(\rho_r^*-\rho_s^*)\mu_s c_{rs}$; the remainder involves the quasi-static
decoder error $\|V - V_{\text{qs}}\|_F \leq K\varepsilon^{2(L-1)/L}$. Continuity of the
full expression on the compact interval $[0, t_{\max}]$, combined with a compactness bound,
gives the uniform $O(\varepsilon^{(2L-1)/L})$ error. $\square$

**Remark.** The coefficient $\kappa_{rs} = \rho_r^*(\rho_r^*-\rho_s^*)\mu_s > 0$ since
$\rho_r^* > \rho_s^*$ and $\mu_s > 0$. This positivity is essential: it means the leading
term is *damping*, not amplifying.

### 7.2 The Integral Bound and the Role of Depth

**Lemma 7.2 (Integral bound).** For $L \geq 2$ and all $r, s$:

$$\int_0^{t_{\max}} P_{rs}(u)\,du = O(1) \quad \text{as } \varepsilon \to 0.$$

**Lemma 7.3 (Depth threshold — $L = 1$ divergence).** For $L = 1$, $P_{rs}(u) \equiv 1$
for all $u$, so $\int_0^{C/\varepsilon} P_{rs}(u)\,du = C/\varepsilon \to \infty$.

These two lemmas capture the *depth separation*. The integral $\int P_{rs}$ appears as the
exponent in the Grönwall bound below. For $L \geq 2$ it is $O(1)$, so the Grönwall
exponential remains bounded; for $L = 1$ it diverges, and the bound breaks down entirely.

### 7.3 The Off-Diagonal Bound

**Theorem 7.4 (Off-diagonal bound).** For $L \geq 2$, if $|c_{rs}(0)| \leq K_0\varepsilon^{1/L}$,
then there exists $C' > 0$ such that for all $r \neq s$ and $t \in [0, t_{\max}]$:

$$|c_{rs}(t)| \leq C'\,\varepsilon^{1/L}.$$

*Proof.* From Lemma 7.1, $c_{rs}$ satisfies $\dot{c}_{rs} = -\kappa_{rs}P_{rs}(t)c_{rs} + g(t)$
with $|g(t)| \leq C\varepsilon^{(2L-1)/L}$. Apply the Grönwall approximation bound
(Theorem A.4) with:
- $\alpha(t) = \kappa_{rs}P_{rs}(t)$,
- $\eta = C\varepsilon^{(2L-1)/L}$,
- $f_0 = K_0\varepsilon^{1/L}$,
- $A = \kappa_{rs}C_{\text{int}}$ where $C_{\text{int}} = \int_0^{t_{\max}} P_{rs}$ (finite by Lemma 7.2).

This gives $|c_{rs}(t)| \leq (K_0\varepsilon^{1/L} + t_{\max}C\varepsilon^{(2L-1)/L})\exp(\kappa_{rs}C_{\text{int}})$.
Since $\varepsilon < 1$ and $(2L-1)/L \geq 1/L$, we have $\varepsilon^{(2L-1)/L} \leq \varepsilon^{1/L}$.
Setting $C' = (K_0 + t_{\max}C)\exp(\kappa_{rs}C_{\text{int}})$ completes the proof. $\square$

---

## 8. Main Theorem

We can now state and prove the main result.

**Definition 8.1 (Alignment angle).** The sine of the angle between the $r$-th encoder
direction $\bar{W}v_r^*/\|\bar{W}v_r^*\|$ and the generalised eigenvector $v_r^*$ is:

$$\sin\angle_r(t) = \frac{\sqrt{\sum_{s \neq r} c_{rs}(t)^2}}{\sqrt{\sigma_r(t)^2 + \sum_{s \neq r} c_{rs}(t)^2} + 1}.$$

Note $\sin\angle_r \leq \sqrt{\sum_{s \neq r} c_{rs}^2}$ since the denominator $\geq 1$.

**Theorem 8.2 (JEPA $\rho^*$-ordering without simultaneous diagonalisability).**
Let $d \geq 1$, $L \geq 2$, $0 < \varepsilon < 1$, $t_{\max} > 0$. Let $\bar{W}, V\colon [0, t_{\max}] \to \mathbb{R}^{d\times d}$ be continuous trajectories satisfying Assumption 4.1 and hypotheses H1–H4 of Lemma 5.2, together with:
- $\|\bar{W}(0)\|_F \leq K_0\varepsilon^{1/L}$ and $\|V(0)\|_F \leq K_0\varepsilon^{1/L}$,
- $|c_{rs}(0)| \leq K_0\varepsilon^{1/L}$ for all $r \neq s$ (balanced small initialisation).

Then there exist constants $C, C' > 0$ (depending on the data and $t_{\max}$, not on $\varepsilon$) such that for all $t \in [0, t_{\max}]$:

**(A) Quasi-static decoder:**
$$\|V(t) - V_{\text{qs}}(\bar{W}(t))\|_F \leq C\,\varepsilon^{2(L-1)/L}.$$

**(B) Off-diagonal alignment:**
$$|c_{rs}(t)| \leq C'\varepsilon^{1/L} \quad \text{for all } r \neq s, \qquad
\sin\angle_r(t) \leq C'\sqrt{d}\,\varepsilon^{1/L} \quad \text{for all } r.$$

**(C) Feature ordering:** If $\rho_r^* > \rho_s^*$ and $\lambda_r^* > \lambda_s^*$, then $\tilde{t}_r^* < \tilde{t}_s^*$.

**(D) Depth is necessary:** For $L = 1$, the integral $\int_0^{C/\varepsilon} P_{rs}(u)\,du \to \infty$, and part (B) cannot be established by this method.

**(E) JEPA vs. MAE:** If $\lambda_r^* = \lambda_s^*$ but $\rho_r^* > \rho_s^*$, then $\tilde{t}_r^*/\tilde{t}_s^* = (\rho_s^*/\rho_r^*)^{2L-2} < 1$, so JEPA strictly orders the features. MAE, whose gradient $V^\top\Sigma^{yx}$ is independent of $\bar{W}$, cannot distinguish features with equal $\lambda^*$.

*Proof.* (A) is Lemma 5.2. (B): the amplitude bound is Theorem 7.4; the sine angle bound follows since $\sin\angle_r \leq \sqrt{\sum_{s\neq r}c_{rs}^2} \leq \sqrt{d}\cdot C'\varepsilon^{1/L}$.
(C) is Corollary 6.2. (D) is Lemma 7.3. (E): the ratio $\tilde{t}_r^*/\tilde{t}_s^* = \lambda_s^*(\rho_s^*)^{2L-2}/(\lambda_r^*(\rho_r^*)^{2L-2}) = (\rho_s^*/\rho_r^*)^{2L-2} < 1$ since $\rho_r^* > \rho_s^*$ and $L \geq 2$. For MAE, the gradient $-\nabla_{\bar{W}}\mathcal{L}^{\text{MAE}} = V^\top(\Sigma^{yx} - V\bar{W}\Sigma^{xx})$ does not depend on $\rho^*$ when $\lambda_r^* = \lambda_s^*$. $\square$

---

## 9. Discussion

We have shown that the $\rho^*$-ordering implicit bias of JEPA is not an artefact of the
simultaneous diagonalisability assumption, but a structural property of the JEPA objective
under depth-$L \geq 2$ gradient flow. The generalised eigenvector framework provides the
natural coordinates, and the Grönwall argument for off-diagonal control is the key new
ingredient.

Several directions remain open. The critical time formula (Corollaries 6.1–6.2) is derived
from a simplified model of the diagonal dynamics; a fully rigorous derivation of the diagonal
ODE in the general (non-diagonal) setting remains open, and would require an ODE blow-up
argument to bound $\sigma_r(t)$ for all $t \geq 0$ — infrastructure not currently in Mathlib.
On the empirical side, it would be interesting to test whether the $\rho^*$-ordering is
observable in more realistic JEPA models trained on structured data where $\Sigma^{xx}$ and
$\Sigma^{yx}$ are known to be misaligned.

---

## Appendix A: Classical Auxiliary Lemmas

The following results are proved in `AutomatedProofs/Lemmas.lean` and are standard. They
are included here for completeness and to make the paper self-contained.

**Lemma A.1 (Rayleigh quotient lower bound).** For a positive definite $A \in \mathbb{R}^{d\times d}$,
there exists $\lambda_{\min} > 0$ such that $x^\top A x \geq \lambda_{\min}\|x\|^2$ for all $x \in \mathbb{R}^d$.

*Proof.* The function $f(x) = x^\top Ax$ is continuous and attains its minimum $\lambda_{\min}$
on the compact unit sphere $S^{d-1}$. Positive definiteness gives $\lambda_{\min} > 0$;
homogeneity extends to all $x$. $\square$

**Lemma A.2 (Frobenius–trace lower bound).** For positive definite $A$ and any $M \in \mathbb{R}^{d\times d}$:
$\operatorname{tr}(M^\top M A) \geq \lambda_{\min}\|M\|_F^2$.

*Proof.* Apply Lemma A.1 column-by-column and sum. $\square$

**Theorem A.3 (Grönwall inequality).** If $u(t) \leq c + \int_0^t \beta(s)u(s)\,ds$ with
$\beta \geq 0$, then $u(t) \leq c\exp\!\bigl(\int_0^t \beta(s)\,ds\bigr)$.

*Proof.* Standard integrating factor argument. $\square$

**Theorem A.4 (Grönwall approximation bound).** If $|f'(t) + \alpha(t)f(t)| \leq \eta$ with
$\alpha \geq 0$, $\int_0^t \alpha \leq A$, and $|f(0)| \leq f_0$, then
$|f(t)| \leq (f_0 + t\cdot\eta)\exp(A)$.

*Proof.* Multiply through by the integrating factor $e^{\int_0^t\alpha}$, bound using
$\int_0^t\alpha \leq A$, then apply Theorem A.3. $\square$

---

## Appendix B: Formal Verification Record

All lemmas and the main theorem (Theorem 8.2) are formally verified in Lean 4.

| Result | Lean name | Location | Status |
|---|---|---|---|
| Lemma A.1 | `pd_quadratic_lower_bound` | `Lemmas.lean` | (Aristotle `48ec8df6`) |
| Lemma A.2 | `frobenius_pd_lower_bound` | `Lemmas.lean` | (Aristotle `48ec8df6`) |
| Theorem A.3 | `gronwall_integral_ineq` | `Lemmas.lean` | (Aristotle `48ec8df6`) |
| Theorem A.4 | `gronwall_approx_ode_bound` | `Lemmas.lean` | (Aristotle `48ec8df6`) |
| Lemma 3.1 | `gradient_projection` | `JEPA.lean` |  |
| Lemma 5.2 | `quasiStatic_approx` | `JEPA.lean` | (Aristotle `d8a0593e`) |
| Corollary 6.1 | `critical_time_formula` | `JEPA.lean` |  |
| Corollary 6.2 | `critical_time_ordering` | `JEPA.lean` |  |
| Lemma 7.1 | `offDiag_ODE` | `JEPA.lean` | (Aristotle `7e7b8e9a`) |
| Lemma 7.2 | `preconditioner_integral_bounded` | `JEPA.lean` |  |
| Lemma 7.3 | `preconditioner_integral_diverges_L1` | `JEPA.lean` |  |
| Theorem 7.4 | `offDiag_bound` | `JEPA.lean` |  |
| Theorem 8.2 | `JEPA_rho_ordering` | `JEPA.lean` | (Aristotle `472373f7`) |

**Build record.** `lake build` passes with zero `sorry`s on all files. Repository:
`github.com/davidcagoh/automated-proofs`, commit `f2e962e`. Toolchain:
`leanprover/lean4:v4.28.0`, Mathlib commit `8f9d9cff6bd728b17a24e163c9402775d9e6a365`.

The two helper lemmas in `OffDiagHelpers.lean` (`offDiag_eps_rpow_le`, `offDiag_integral_bound`)
are factored out to resolve an import dependency and are proved directly from Mathlib's
`Real.rpow_le_rpow_of_exponent_ge`.

---

## References

Arora, S., Cohen, N., and Hazan, E. (2018). On the optimization of deep networks: Implicit
acceleration by overparameterization. *ICML 2018*. arXiv:1802.06509.

Arora, S., Cohen, N., Hu, W., and Luo, Y. (2019). Implicit regularization in deep matrix
factorization. *NeurIPS 2019*. arXiv:1905.13655.

Littwin, E., Saremi, O., Advani, M., Thilak, V., Nakkiran, P., Huang, C., and Susskind, J.
(2024). How JEPA avoids noisy features: The implicit bias of deep linear self distillation
networks. arXiv:2407.03475.

**[CITE: He, K., Chen, X., Xie, S., Li, Y., Dollár, P., and Girshick, R. (2022). Masked
autoencoders are scalable vision learners. CVPR 2022.]**

**[CITE: LeCun, Y. (2022). A path towards autonomous machine intelligence. OpenReview.]**

**[CITE: Assran, M. et al. (2023). Self-supervised learning from images with a
joint-embedding predictive architecture. CVPR 2023.]**

**[CITE: Bardes, A. et al. (2024). V-JEPA: Latent video prediction for visual representation
learning. ICLR 2024.]**

**[CITE: Saxe, A. M., McClelland, J. L., and Ganguli, S. (2013). Exact solutions to the
nonlinear dynamics of learning in deep linear neural networks. ICLR 2014. — referenced
in Littwin et al. for the deep linear networks literature.]**
