"""
tcmodel.py — EXP#12 model definitions, shared by train.py and evaluate.py so the arm that is fitted
and the arm that is scored cannot be two different things.

Pre-registration §5.1 (frozen). Three candidates, all permissive, all <= 400M:

  * `answerdotai/ModernBERT-base`     Apache-2.0, 149M — a POINTWISE option scorer
  * `microsoft/deberta-v3-base`       MIT,        ~184M — a POINTWISE option scorer
  * SETFIT-STYLE: frozen `sentence-transformers/all-mpnet-base-v2` (Apache-2.0, 109M) plus a
    logistic head on sentence-pair features — the labels-thin arm. The pre-registration's "~110M"
    figure is this model (109,486,978 parameters).

WHY THE HEAD IS POINTWISE, AND NOT A FIXED LABEL LAYER
  The fixture's option sets are not the corpus's label sets: the corpus has 34 distinct gold labels,
  the 190 fixture cases draw on 215 distinct option labels, and only 15 labels are shared
  (`data/manifest.json`, `labelTransfer`). A fixed `num_labels=N` output layer trained on the corpus
  cannot name 200 of the fixture's options at all, so it would measure the vocabulary mismatch rather
  than the transfer. The pre-registration's own pool entry for this task shape is
  `fastino/GLiNER2.5-Decide`, described in DECIDER_TIER §4 as a "label-set classifier" — an encoder
  that is given the candidate labels and scores them.

  So each arm scores every (situation, candidate option) pair independently through `tccommon.render`,
  and the per-case distribution is the softmax over that case's options. Three consequences the
  experiment leans on, and states as consequences rather than as findings:
    * the arm can be scored on an option set it has never seen;
    * the per-case distribution is permutation-equivariant, so the "order sensitivity" contaminant
      DECIDER_TIER §5.8 lists for generative extraction does not exist for this head — which is H2's
      argument, and is measured rather than asserted in evaluate.py;
    * the loss is the softmax cross-entropy over the case's options, so the gradient is a genuine
      ranking signal over the option set and not independent binary classification.

THE SETFIT-STYLE HEAD, AND WHY IT IS THE "LABELS-THIN" ARM
  SetFit's claim is a frozen sentence encoder plus a small head, reaching near-3B-prompted quality at
  ~110M with seconds of training. Trained per-class it cannot transfer to unseen labels, so the
  variable-label-set analogue is the sentence-pair head: features are
  `[u, v, u*v, |u-v|]` over the frozen embeddings of the situation and the candidate option, and a
  L2-regularised logistic regression is fitted on those features. That is exactly "frozen
  sentence-transformer + logistic head", it is fitted in seconds, and it transfers to unseen labels.
  The pooling is mean-pooling followed by L2 normalisation, which is what the `all-mpnet-base-v2`
  sentence-transformers module does (`1_Pooling` + `2_Normalize` in that repo's `modules.json`), so no
  `sentence-transformers` dependency is needed to reproduce the frozen arm's embeddings.
"""

from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

POINTWISE_ARMS = ("modernbert-base", "deberta-v3-base")
ALL_ARMS = ("modernbert-base", "deberta-v3-base", "setfit-mpnet", "majority-class", "shuffled-label")

MODEL_IDS = {
    "modernbert-base": "answerdotai/ModernBERT-base",
    "deberta-v3-base": "microsoft/deberta-v3-base",
    "setfit-mpnet": "sentence-transformers/all-mpnet-base-v2",
    "shuffled-label": "answerdotai/ModernBERT-base",
}

#: Licences verified from the card front-matter and the HF API on 2026-10-04 (no LICENSE file ships in
#: any of the three model repos — see the report's licence caveat).
LICENCES = {
    "answerdotai/ModernBERT-base": "Apache-2.0",
    "microsoft/deberta-v3-base": "MIT",
    "sentence-transformers/all-mpnet-base-v2": "Apache-2.0",
}


class PointwiseScorer(nn.Module):
    """Encoder + one linear logit per (situation, candidate option) pair."""

    def __init__(self, base_name: str, dropout: float = 0.1):
        super().__init__()
        from transformers import AutoModel, AutoConfig

        self.base_name = base_name
        config = AutoConfig.from_pretrained(base_name)
        # Some checkpoints ship in fp16 (microsoft/deberta-v3-base does). Load in fp32 explicitly:
        # a half encoder under a float head is a dtype crash, and an fp16 forward is not the
        # pre-registered operating condition for either arm.
        self.encoder = AutoModel.from_pretrained(base_name, config=config).float()
        self.hidden_size = int(config.hidden_size)
        self.dropout = nn.Dropout(dropout)
        self.head = nn.Linear(self.hidden_size, 1)

    def forward(self, input_ids, attention_mask):
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = out.last_hidden_state[:, 0]  # [CLS] for ModernBERT and for DeBERTa-v2/v3
        return self.head(self.dropout(pooled.float())).squeeze(-1)


class LogisticPairHead:
    """
    Frozen sentence encoder + logistic regression on sentence-pair features.

    `features(u, v) = [u, v, u*v, |u-v|]`, embeddings L2-normalised. Fitted with the standard
    `LogisticRegression` solver; the scaler is fitted on the training features only (a scaler fitted
    on the fixture would be a leak, and would also be a leak on the dev split).
    """

    def __init__(self, model_id: str = MODEL_IDS["setfit-mpnet"], max_length: int = 256, device: str = "cpu"):
        from transformers import AutoModel, AutoTokenizer

        self.model_id = model_id
        self.max_length = max_length
        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.encoder = AutoModel.from_pretrained(model_id).float().to(device).eval()
        self.scaler = None
        self.clf = None

    @staticmethod
    def pair_features(u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return np.concatenate([u, v, u * v, np.abs(u - v)], axis=-1)

    @torch.no_grad()
    def embed(self, texts, batch_size: int = 32, show: bool = False) -> np.ndarray:
        out = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            enc = self.tokenizer(
                batch, padding=True, truncation=True, max_length=self.max_length, return_tensors="pt"
            ).to(self.device)
            hidden = self.encoder(**enc).last_hidden_state
            mask = enc["attention_mask"].unsqueeze(-1).float()
            pooled = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
            pooled = torch.nn.functional.normalize(pooled, p=2, dim=1)
            out.append(pooled.float().cpu().numpy())
            if show and i % (batch_size * 20) == 0:
                print(f"    embedded {i}/{len(texts)}", flush=True)
        return np.concatenate(out, axis=0)

    def _embed_unique(self, texts):
        """Embed each distinct string once and return (unique embeddings, index into them).

        The situation text repeats once per candidate option and corpus option labels repeat across
        cases, so encoding the raw pair list re-encodes the same string many times. Deduplicating is
        the same computation with fewer forward passes; it changes no number.
        """
        uniq = list(dict.fromkeys(texts))
        index = {t: i for i, t in enumerate(uniq)}
        emb = self.embed(uniq, batch_size=64) if uniq else np.zeros((0, 768), dtype=np.float32)
        return emb, np.array([index[t] for t in texts], dtype=np.int64)

    def fit(self, situations, option_texts, labels, seed: int = 20261004):
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import StandardScaler

        us, ui = self._embed_unique(list(situations))
        vs, vi = self._embed_unique(list(option_texts))
        x = self.pair_features(us[ui], vs[vi])
        self.scaler = StandardScaler().fit(x)
        xs = self.scaler.transform(x)
        self.clf = LogisticRegression(max_iter=3000, C=1.0, random_state=seed)
        self.clf.fit(xs, labels)
        self.n_encoder_parameters = sum(p.numel() for p in self.encoder.parameters())
        return self

    @torch.no_grad()
    def case_logits(self, situation: str, options) -> list:
        """logit(match) per option — the arm's per-option score, temperature-scalable like a logit."""
        options = list(options)
        u = self.embed([situation], batch_size=1)[0]
        v = self.embed(options, batch_size=max(1, len(options)))
        u_tiled = np.tile(u, (len(options), 1))
        x = self.pair_features(u_tiled, v)
        xs = self.scaler.transform(x)
        # THE HEAD'S RAW LOGIT, NOT A TRANSFORMED PROBABILITY.
        #
        # `predict_proba` is the wrong quantity to rank and to temperature-scale: a saturated L2
        # logistic regression on 3072 standardised features returns exactly 0.0 and exactly 1.0 for
        # whole groups of options, so every saturated option receives the SAME score. `argmax` then
        # resolves those ties by the position the option happened to be presented in, which makes the
        # arm's decision order-dependent for no modelling reason.
        #
        # Two earlier revisions tried to patch around this by clipping the probability: first at
        # [1e-6, 1-1e-6], then at the denormal edge. `defect-probe.py` measured both on the development
        # split and showed the second still left 21/200 cases with an exact tie at the top, because
        # `predict_proba` has already discarded the information — no clip can recover it.
        # `decision_function` returns the log-odds the fit actually produced, unsaturated, so no clip is
        # needed and no tie is manufactured. That is the fix.
        return list(np.asarray(self.clf.decision_function(xs), dtype=np.float64).ravel())


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters())
