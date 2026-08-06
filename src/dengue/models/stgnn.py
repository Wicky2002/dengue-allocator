"""Spatio-temporal graph neural network for district-level dengue forecasting.

STUB -- not implemented in this session. Stage 1 currently ships the
:mod:`~dengue.models.baseline` and :mod:`~dengue.models.lgbm_quantile` models;
this is the planned upgrade path.

Intended architecture
---------------------
**Graph.** Nodes are the 25 districts; edges come from
:func:`dengue.config.district_graph` (land borders). Land adjacency is a
defensible prior for dengue: *Aedes aegypti* disperses only a few hundred metres
in its lifetime, so spatial spread at district scale is driven by **human**
movement, which follows road networks and therefore correlates strongly with
shared borders. A commuting-flow or mobile-phone mobility graph would be
strictly better and is the obvious extension; adjacency is the version buildable
without a data-sharing agreement.

**Spatial encoder.** GraphSAGE with mean aggregation, 2 layers, hidden width 64.
GraphSAGE rather than a vanilla GCN because its neighbour sampling and
concat-then-transform update keep a node's own state distinct from its
neighbourhood's -- which matters when a district is diverging from its
neighbours, precisely the case worth detecting early.

**Temporal encoder.** A GRU over the last 12 weeks of per-node embeddings.
Recurrent rather than attention-based purely on sample size: ~25 nodes x ~800
weeks is small, and a transformer would overfit without heavy regularisation.

**Head.** A linear layer emitting 3 quantiles x 3 horizons = 9 outputs per node,
trained with the **pinball (quantile) loss** summed over quantiles and horizons,
matching :func:`dengue.eval.metrics.pinball_loss` so training and evaluation
optimise the same thing.

**Training.** Rolling-origin splits identical to
:func:`dengue.eval.backtest.rolling_origin`, Adam, early stopping on validation
pinball loss, gradient clipping at 1.0. Node features are the same lag/climate
block that :mod:`dengue.features.build_panel` produces, so the leakage guarantee
carries over unchanged.

Why it is expected to help
--------------------------
The LightGBM model sees a neighbour's lagged incidence only through one
hand-engineered scalar. A GNN learns *how much* to weight each neighbour, and
can propagate signal two hops in a single layer stack -- which is what an
outbreak moving along the Colombo-Gampaha-Kurunegala corridor looks like.

Dependencies (not installed)
----------------------------
``torch`` and ``torch-geometric``. Both are deliberately excluded from
``pyproject.toml``: they are large, platform-sensitive, and would put the
"``make baseline`` runs offline on a bare machine" acceptance criterion at risk
for a model that is not yet implemented.
"""

from __future__ import annotations

import pandas as pd

from dengue import config
from dengue.models import ForecastModel


class STGNN(ForecastModel):
    """GraphSAGE-over-adjacency + GRU, trained with pinball loss.

    Not implemented. See the module docstring for the intended design.

    Parameters
    ----------
    hidden_dim:
        Width of the GraphSAGE and GRU hidden states.
    n_graph_layers:
        Number of GraphSAGE message-passing layers. 2 gives each district a
        2-hop receptive field.
    sequence_length:
        Weeks of history fed to the GRU.
    horizons:
        Forecast horizons, emitted jointly by a multi-output head.
    quantiles:
        Quantiles for the pinball loss.
    learning_rate:
        Adam learning rate.
    max_epochs:
        Training epoch cap, with early stopping on validation pinball loss.
    random_state:
        Seed for reproducibility.
    """

    name = "stgnn"

    def __init__(
        self,
        hidden_dim: int = 64,
        n_graph_layers: int = 2,
        sequence_length: int = 12,
        horizons: tuple[int, ...] = config.HORIZONS,
        quantiles: tuple[float, ...] = config.QUANTILES,
        learning_rate: float = 1e-3,
        max_epochs: int = 200,
        random_state: int = config.RANDOM_SEED,
    ) -> None:
        self.hidden_dim = hidden_dim
        self.n_graph_layers = n_graph_layers
        self.sequence_length = sequence_length
        self.horizons = horizons
        self.quantiles = quantiles
        self.learning_rate = learning_rate
        self.max_epochs = max_epochs
        self.random_state = random_state

    def fit(self, panel: pd.DataFrame) -> STGNN:
        """Train the STGNN. Not implemented.

        Raises
        ------
        NotImplementedError
            Always. Planned for the Phase 2 submission.
        """
        raise NotImplementedError(
            "STGNN.fit is not implemented. Stage 1 currently ships SeasonalNaive, "
            "SarimaBaseline and LGBMQuantile; see the module docstring for the "
            "planned GraphSAGE + GRU design and its torch/torch-geometric "
            "dependencies."
        )

    def predict(self, panel: pd.DataFrame, horizon: int) -> pd.DataFrame:
        """Predict with the STGNN. Not implemented.

        Raises
        ------
        NotImplementedError
            Always.
        """
        raise NotImplementedError("STGNN.predict is not implemented. See STGNN.fit.")
