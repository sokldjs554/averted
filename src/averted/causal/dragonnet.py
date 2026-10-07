"""DragonNet (Shi, Blei, Veitch 2019) — 처치 확률과 두 결과를 하나의 표현에서 함께 학습하는 신경망 효과 추정기. PyTorch 직접 구현.

  X ──▶ 공유 표현 φ(x) ──┬─▶ 처치 확률 e(x)         (BCE)
                         ├─▶ 결과 헤드 h0(φ)        (T=0 행에서만 학습, BCE)
                         └─▶ 결과 헤드 h1(φ)        (T=1 행에서만 학습, BCE)
  효과 τ(x) = σ(h1) − σ(h0).  선택적으로 표적 정규화(targeted regularization)를 더해 이중 강건 성질을 학습에 넣는다.

솔직한 전제: 이 데이터처럼 처치율 7%, 결과율 8% 인 표 형식 로그에서는 트리 기반 T-learner 보다 낫다고 기대하지 않는다.
표현 공유가 도움이 되는지, 학습곡선에서 어디쯤 따라잡는지를 같은 기준(점검 100번당 막는 고장)으로 재서 보고한다.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn


class _Net(nn.Module):
    def __init__(self, d_in: int, hidden: int = 96, head: int = 48, dropout: float = 0.1):
        super().__init__()
        self.trunk = nn.Sequential(
            nn.Linear(d_in, hidden), nn.ELU(), nn.Dropout(dropout), nn.Linear(hidden, hidden), nn.ELU()
        )
        self.t_head = nn.Linear(hidden, 1)
        self.y0 = nn.Sequential(nn.Linear(hidden, head), nn.ELU(), nn.Linear(head, 1))
        self.y1 = nn.Sequential(nn.Linear(hidden, head), nn.ELU(), nn.Linear(head, 1))
        self.eps = nn.Parameter(torch.zeros(1))  # 표적 정규화 계수

    def forward(self, x):
        z = self.trunk(x)
        return self.t_head(z).squeeze(-1), self.y0(z).squeeze(-1), self.y1(z).squeeze(-1)


@dataclass
class DragonModel:
    net: _Net
    mean: np.ndarray
    std: np.ndarray
    epochs_run: int
    n_params: int
    train_seconds: float

    def _x(self, X) -> torch.Tensor:
        return torch.as_tensor((X - self.mean) / self.std, dtype=torch.float32)

    @torch.no_grad()
    def predict_parts(self, X) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        self.net.eval()
        t, y0, y1 = self.net(self._x(X))
        return torch.sigmoid(t).numpy(), torch.sigmoid(y0).numpy(), torch.sigmoid(y1).numpy()

    def averted(self, X) -> np.ndarray:
        _, p0, p1 = self.predict_parts(X)
        return p0 - p1


def fit_dragonnet(
    X: np.ndarray,
    T: np.ndarray,
    Y: np.ndarray,
    groups: np.ndarray,
    epochs: int = 40,
    lr: float = 2e-3,
    batch: int = 2048,
    alpha: float = 1.0,
    beta_tr: float = 1.0,
    patience: int = 6,
    seed: int = 0,
    threads: int | None = None,
) -> DragonModel:
    import time

    if threads:
        torch.set_num_threads(threads)
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    mean, std = X.mean(axis=0), X.std(axis=0)
    std[std < 1e-6] = 1.0
    # 설비 단위로 20% 를 검증으로
    uniq = np.unique(groups)
    val_assets = set(rng.choice(uniq, size=max(1, len(uniq) // 5), replace=False).tolist())
    is_val = np.array([g in val_assets for g in groups])
    Xt = torch.as_tensor((X - mean) / std, dtype=torch.float32)
    Tt = torch.as_tensor(T, dtype=torch.float32)
    Yt = torch.as_tensor(Y, dtype=torch.float32)
    tr_idx = np.flatnonzero(~is_val)
    va_idx = np.flatnonzero(is_val)
    net = _Net(X.shape[1])
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=1e-3)
    bce = nn.BCEWithLogitsLoss()

    def loss_fn(idx, train: bool):
        xb, tb, yb = Xt[idx], Tt[idx], Yt[idx]
        t_logit, y0, y1 = net(xb)
        y_logit = torch.where(tb > 0.5, y1, y0)
        l_y = bce(y_logit, yb)
        l_t = bce(t_logit, tb)
        loss = l_y + alpha * l_t
        if beta_tr > 0:  # 표적 정규화: 결과 예측을 처치 확률의 역수 방향으로 미세 조정
            e = torch.sigmoid(t_logit).clamp(0.02, 0.98).detach()
            h = tb / e - (1 - tb) / (1 - e)
            p = torch.sigmoid(y_logit).detach()
            loss = loss + beta_tr * torch.mean((yb - (p + net.eps * h)) ** 2)
        return loss, l_y

    best, best_state, bad, ran = np.inf, None, 0, 0
    t0 = time.time()
    for ep in range(epochs):
        net.train()
        perm = rng.permutation(tr_idx)
        for i in range(0, len(perm), batch):
            idx = torch.as_tensor(perm[i : i + batch])
            opt.zero_grad()
            loss, _ = loss_fn(idx, True)
            loss.backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            _, l_y = loss_fn(torch.as_tensor(va_idx), False)
        ran = ep + 1
        if float(l_y) < best - 1e-5:
            best, bad = float(l_y), 0
            best_state = {k: v.clone() for k, v in net.state_dict().items()}
        else:
            bad += 1
            if bad >= patience:
                break
    if best_state:
        net.load_state_dict(best_state)
    n_params = sum(p.numel() for p in net.parameters())
    return DragonModel(net, mean, std, ran, n_params, time.time() - t0)
