"""설비 세계 — 점검이 고장을 막는 메커니즘을 직접 시뮬레이션한다.

효과를 "가정"으로 넣지 않고 메커니즘에서 나오게 했다.

    숨은 손상 D 가 주마다 쌓인다 (감마 과정)  →  주간 고장 위험 h = h0 · exp(β (D − 1))
    점검(방문)을 하면: 손상이 클수록 결함을 발견할 확률이 높고(탐지), 발견하면 수리해 D 를 줄인다(수리).
      · 설비 종류마다 순찰로 발견할 수 있는 정도가 다르다 (펌프는 소음·누수로 보이지만 수배전반·승강기 내부 마모는 안 보인다).
      · 발견한 결함은 수리 접수(작업지시)가 되고 0~3주 뒤 수리된다. 접수된 설비를 또 점검해도 새로 찾을 것이 없다.
      · 수명이 한계를 넘은 설비는 수리해도 소용이 없다(`cliff`) — 교체해야 하는 설비다.
      · 점검 자체도 드물게 고장을 유발한다(분해·시험 중 사고, `p_induced`).

그래서 점검의 효과 τ = (점검하지 않았을 때 4주 내 고장 확률) − (점검했을 때)는 위험과 같은 순서가 아니다.
위험이 가장 높은 설비 중에는 "이미 접수돼 점검해도 소용없는 설비", "순찰로는 못 찾는 설비", "교체해야 하는 설비"가 섞여 있다.
이 세 메커니즘을 끈 세계(`flat=True`)에서는 위험순과 효과순이 거의 같아진다 — 위험순이 충분한 세계도 함께 보고하기 위한 손잡이다.

과거 점검 기록(로그)은 현장 규칙으로 생성된다: 이전 판정이 나쁘거나, 최근 고장이 있었거나, 오래 안 봤거나, 연식이 높으면
점검 확률이 올라간다 — 즉 위험한 설비를 더 자주 본다. 여기에 분석가가 볼 수 없는 "촉(hunch)"을 섞을 수 있다(`hunch`).
촉 = 점검자가 소음·열 같은 것으로 손상을 감지하는 것. hunch=0 이면 기록된 변수만으로 교란이 모두 보정되고,
hunch>0 이면 보정되지 않는 교란이 생긴다 — 일부러 분석이 틀리는 조건을 만들기 위한 손잡이다.

같은 난수로 두 세계(점검함/안 함)를 굴려 개별 설비·주마다 정답 효과를 구한다(`truth.py`).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

BETA = 1.25  # 손상이 위험에 미치는 영향 (로그 척도)
CORRECTIVE_RESIDUAL = 0.25  # 고장 후 교정 수리로 남는 손상 비율
BD_DECAY = 0.93  # 최근 고장 가중 합의 주간 감쇠 (반감기 약 10주)
CMP_DECAY = 0.55  # 최근 민원·A/S 접수 가중 합의 주간 감쇠 (반감기 약 1주)
CMP_BASE = 0.03  # 손상이 작을 때 주간 접수 확률
CMP_SLOPE = 0.30  # 손상 1.2 를 넘는 만큼 늘어나는 접수 확률
WSV_CAP = 52


@dataclass(frozen=True)
class Category:
    key: str
    ko: str
    h0: float  # D=1 에서의 주간 고장 위험
    wear: float  # 마모 속도 배수
    legal: bool  # 법정 점검 대상
    legal_period: int  # 법정 점검 주기(주)
    p_induced: float  # 점검이 유발하는 고장 확률


CATEGORIES: tuple[Category, ...] = (
    Category("pump", "펌프", 0.0036, 1.00, False, 0, 0.0020),
    Category("chiller", "냉동기", 0.0048, 1.10, False, 0, 0.0040),
    Category("ahu", "공조기", 0.0040, 1.00, False, 0, 0.0030),
    Category("boiler", "보일러", 0.0035, 0.90, True, 26, 0.0030),
    Category("elevator", "승강기", 0.0027, 0.80, True, 26, 0.0040),
    Category("fire_pump", "소방펌프", 0.0020, 0.70, True, 13, 0.0020),
    Category("generator", "발전기", 0.0024, 0.80, True, 13, 0.0030),
    Category("switchgear", "수배전반", 0.0018, 0.70, True, 26, 0.0020),
)
CAT_INDEX = {c.key: i for i, c in enumerate(CATEGORIES)}
CAT_H0 = np.array([c.h0 for c in CATEGORIES])
CAT_WEAR = np.array([c.wear for c in CATEGORIES])
CAT_LEGAL = np.array([c.legal for c in CATEGORIES])
CAT_PERIOD = np.array([c.legal_period for c in CATEGORIES])
CAT_INDUCED = np.array([c.p_induced for c in CATEGORIES])

# 순찰(육안·청취·촉진·계기 확인)로 결함을 발견할 수 있는 정도 — 종류별 배수
CAT_DETECT = np.array([0.95, 0.85, 0.90, 0.75, 0.40, 0.85, 0.65, 0.35])
MAX_DELAY = 3  # 결함 발견 후 수리까지 걸리는 최대 주

ARCHETYPES = ("정부청사", "병원", "호텔", "오피스")


@dataclass(frozen=True)
class WorldConfig:
    seed: int = 7
    n_sites: int = 12
    assets_min: int = 90
    assets_max: int = 150
    weeks: int = 156  # 기록 기간 (번인 제외)
    burn_in: int = 78
    horizon: int = 4  # 결과 창(주): 점검한 주부터 4주 안의 비계획 고장
    hazard_scale: float = 2.2  # 전체 고장 위험 배수
    random_visit: float = (
        0.0  # >0 이면 재량 점검을 이 확률로 무작위 배정한다 (무작위 파일럿; 법정 점검은 그대로)
    )
    pilot_share: float = (
        0.0  # >0 이면 설비의 이 비율을 무작위 파일럿으로 지정 — 이 설비들은 점검을 동전 던지기로 배정한다
    )
    pilot_visit_rate: float = 0.07  # 파일럿 설비의 주간 무작위 점검 확률 (평소 점검 비율과 비슷하게)
    hunch: float = 0.0  # 분석가가 못 보는 교란 강도 γ
    hunch_noise: float = 0.6
    flat: bool = (
        False  # True 이면 종류별 탐지 차이·수리 접수 지연·수명 한계를 모두 끈다 (위험순이 충분한 세계)
    )
    cliff: bool = True  # 한계를 넘은 설비는 수리해도 소용없다
    cliff_at: float = 3.0
    detect_mid: float = 1.0
    detect_width: float = 0.45
    repair_eff: float = 0.60
    # 점검 규칙 (로짓 계수)
    th_grade: float = 0.85
    th_bd: float = 0.40
    th_age: float = 0.25
    th_wsv: float = 0.55
    th_cmp: float = 1.8  # 최근 민원·A/S 접수에 반응하는 정도 (점검 규칙의 가장 강한 항)
    th_open: float = -0.8  # 이미 수리 접수된 설비는 순찰에서 후순위
    visit_rate_lo: float = 0.045
    visit_rate_hi: float = 0.095
    wear_scale: float = 0.045
    extra: dict = field(default_factory=dict)

    def describe(self) -> dict:
        return {k: v for k, v in self.__dict__.items() if k != "extra"}


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


@dataclass
class Static:
    """설비별로 변하지 않는 값 (모양 (n,) — 포크할 때는 (n,1) 로 브로드캐스트)."""

    site: np.ndarray
    cat: np.ndarray
    age: np.ndarray
    crit: np.ndarray
    rho: np.ndarray  # 숨은 마모 이질성 (분석가는 못 봄)
    skill: np.ndarray  # 사이트별 점검 숙련도(탐지 확률 배수)
    culture: np.ndarray  # 사이트별 "위험 기반 점검" 성향 배수
    alpha: np.ndarray  # 사이트별 점검 로짓 절편 (번인에서 보정)
    pilot: np.ndarray  # 무작위 파일럿 설비 여부

    def __len__(self) -> int:
        return len(self.cat)

    def col(self) -> Static:
        """(n,) → (n,1)"""
        return Static(*(getattr(self, f)[:, None] for f in self.__dataclass_fields__))

    def take(self, idx: np.ndarray) -> Static:
        return Static(*(getattr(self, f)[idx] for f in self.__dataclass_fields__))


@dataclass
class Dyn:
    D: np.ndarray
    grade_last: np.ndarray
    wsv: np.ndarray
    bd: np.ndarray
    cmp: np.ndarray  # 최근 민원·A/S 접수 (감쇠 합) — 분석가가 보는 현재 손상의 잡음 섞인 신호
    pend: np.ndarray  # 수리 접수 후 남은 주 (0 = 접수된 결함 없음)

    def copy(self) -> Dyn:
        return Dyn(*(getattr(self, f).copy() for f in self.__dataclass_fields__))

    def fork(self, m: int, arms: int = 1) -> Dyn:
        """(n,) → (n, m) 로 복제 (두 세계 모두 같은 출발 상태)."""
        return Dyn(*(np.repeat(getattr(self, f)[:, None], m, axis=1) for f in self.__dataclass_fields__))


def make_static(cfg: WorldConfig, rng: np.random.Generator) -> Static:
    sizes = rng.integers(cfg.assets_min, cfg.assets_max + 1, size=cfg.n_sites)
    site = np.repeat(np.arange(cfg.n_sites), sizes)
    n = len(site)
    # 사이트 성격: 점검 숙련도(탐지), 위험 기반 점검 성향
    skill_s = np.clip(rng.normal(0.9, 0.08, cfg.n_sites), 0.65, 1.0)
    culture_s = np.clip(rng.lognormal(0.0, 0.25, cfg.n_sites), 0.6, 1.5)
    # 종류 구성: 법정 설비는 사이트당 일부
    p_cat = np.array([0.20, 0.08, 0.18, 0.08, 0.14, 0.12, 0.08, 0.12])
    cat = rng.choice(len(CATEGORIES), size=n, p=p_cat / p_cat.sum())
    age = np.clip(rng.gamma(3.0, 3.5, size=n) + 0.5, 0.5, 30.0)
    crit = rng.choice([1, 2, 3], size=n, p=[0.5, 0.35, 0.15])
    rho = rng.lognormal(0.0, 0.55, size=n)
    return Static(
        site=site,
        cat=cat,
        age=age,
        crit=crit,
        rho=rho,
        skill=skill_s[site],
        culture=culture_s[site],
        alpha=np.zeros(n),
        pilot=rng.random(n) < cfg.pilot_share,
    )


def init_dyn(st: Static, rng: np.random.Generator) -> Dyn:
    n = len(st)
    return Dyn(
        D=rng.gamma(2.0, 0.35, size=n) * (0.5 + st.age / 15.0),
        grade_last=np.zeros(n, dtype=np.int8),
        wsv=rng.integers(0, 30, size=n).astype(np.float64),
        bd=np.zeros(n),
        cmp=np.zeros(n),
        pend=np.zeros(n),
    )


@dataclass
class Draws:
    """한 주 동안 쓰이는 난수 — 포크에서는 두 세계가 같은 난수를 공유한다 (공통 난수)."""

    u_visit: np.ndarray
    u_det: np.ndarray
    u_ind: np.ndarray
    u_fail: np.ndarray
    u_cmp: np.ndarray
    u_delay: np.ndarray
    wear: np.ndarray
    eps: np.ndarray  # 촉 잡음
    grade_noise: np.ndarray

    @staticmethod
    def draw(rng: np.random.Generator, shape: tuple[int, ...]) -> Draws:
        return Draws(
            u_visit=rng.random(shape),
            u_det=rng.random(shape),
            u_ind=rng.random(shape),
            u_fail=rng.random(shape),
            u_cmp=rng.random(shape),
            u_delay=rng.random(shape),
            wear=rng.gamma(1.0, 1.0, size=shape),  # 단위 감마, 마모 속도는 step 에서 곱한다
            eps=rng.standard_normal(shape),
            grade_noise=rng.standard_normal(shape),
        )


def _z_damage(st: Static, D: np.ndarray) -> np.ndarray:
    """손상의 표준화 (촉의 신호 부분). 연식 기준 평균/표준편차로 대략 맞춘다."""
    return (D - 1.1) / 0.9


def visit_logit(cfg: WorldConfig, st: Static, dyn: Dyn, eps: np.ndarray) -> np.ndarray:
    z_age = (st.age - 10.5) / 6.0
    risk_terms = (
        cfg.th_grade * dyn.grade_last
        + cfg.th_bd * np.minimum(dyn.bd, 3.0)
        + cfg.th_age * z_age
        + cfg.th_cmp * np.minimum(dyn.cmp, 3.0)
        + cfg.th_open * (dyn.pend > 0)
    )
    eta = st.alpha + st.culture * risk_terms + cfg.th_wsv * np.log1p(np.minimum(dyn.wsv, WSV_CAP) / 4.0)
    if cfg.hunch:
        eta = eta + cfg.hunch * (_z_damage(st, dyn.D) + cfg.hunch_noise * eps)
    return eta


def legal_due(st: Static, dyn: Dyn) -> np.ndarray:
    period = CAT_PERIOD[st.cat]
    return CAT_LEGAL[st.cat] & (dyn.wsv >= period - 1)


def repair_efficacy(cfg: WorldConfig, D: np.ndarray) -> np.ndarray:
    if not cfg.cliff or cfg.flat:
        return np.full_like(D, cfg.repair_eff)
    # 한계를 넘으면 수리 효과가 거의 없다 (교체 대상)
    return 0.06 + (cfg.repair_eff - 0.06) * (1.0 - _sigmoid((D - cfg.cliff_at) / 0.30))


def step(
    cfg: WorldConfig,
    st: Static,
    dyn: Dyn,
    draws: Draws,
    force_visit: np.ndarray | None = None,
    no_fail: bool = False,
):
    """한 주를 진행한다. 반환: (새 상태, 사건 dict).

    force_visit: 주어지면 이번 주 점검 여부를 이 값으로 고정한다 (두 세계 포크용; True/False 배열 또는 스칼라).
    no_fail: True 이면 고장 난수를 쓰지 않고 "고장 없이 지나갈 확률" ev["surv"] 만 계산한다 (포크의 분산 감소용).
             "4주 안에 한 번이라도 고장" 확률은 고장이 없는 경로 위에서 주별 생존 확률의 곱으로 정확히 계산된다.
    순서: 점검 결정 → 점검 효과(탐지·수리 접수·유발) → 고장 → 접수된 수리 진행 → 마모 → 다음 주 민원.
    """
    eta = visit_logit(cfg, st, dyn, draws.eps)
    e = np.clip(_sigmoid(eta), 0.004, 0.97)
    if cfg.random_visit > 0:
        e = np.full_like(e, cfg.random_visit)
    if cfg.pilot_share > 0:
        e = np.where(st.pilot, cfg.pilot_visit_rate, e)
    due = legal_due(st, dyn)
    e_eff = np.where(due, 1.0, e)
    if force_visit is None:
        visit = draws.u_visit < e_eff
    else:
        visit = np.broadcast_to(np.asarray(force_visit, dtype=bool), dyn.D.shape).copy()

    D = dyn.D
    # 점검 때 기록되는 판정: 손상 + 잡음 (수리 전 상태를 보고 판정)
    g_star = D + 0.5 * draws.grade_noise
    grade_now = np.where(g_star < 1.0, 0, np.where(g_star < 2.0, 1, 2)).astype(np.int8)
    # 탐지: 이미 접수된 결함은 새로 찾을 것이 없다
    known = dyn.pend > 0
    cat_detect = 1.0 if cfg.flat else CAT_DETECT[st.cat]
    p_det = st.skill * cat_detect * _sigmoid((D - cfg.detect_mid) / cfg.detect_width)
    detected = visit & ~known & (draws.u_det < p_det)
    max_delay = 0 if cfg.flat else MAX_DELAY
    delay = np.minimum((draws.u_delay * (max_delay + 1)).astype(int), max_delay)
    immediate = detected & (delay == 0)
    eff = repair_efficacy(cfg, D)
    D_after = np.where(immediate, D * (1.0 - eff), D)
    # 고장: 위험 함수 + 점검이 유발하는 고장
    h = cfg.hazard_scale * CAT_H0[st.cat] * np.exp(BETA * (D_after - 1.0))
    p_fail = 1.0 - np.exp(-h)
    p_ind = np.where(visit, CAT_INDUCED[st.cat], 0.0)
    surv = (1.0 - p_fail) * (1.0 - p_ind)
    if no_fail:
        fail = np.zeros(D.shape, dtype=bool)
    else:
        fail = (draws.u_fail < p_fail) | (visit & (draws.u_ind < CAT_INDUCED[st.cat]))
    D_next = np.where(fail, D_after * CORRECTIVE_RESIDUAL, D_after)
    # 접수된 수리 진행: 남은 주가 1이면 이번 주 끝에 수리가 끝난다 (고장 난 설비는 교정 수리로 접수가 사라진다)
    pend_next = np.where(known, dyn.pend - 1.0, np.where(detected & (delay > 0), delay.astype(float), 0.0))
    repair_done = known & (dyn.pend == 1.0) & ~fail
    D_next = np.where(repair_done, D_next * (1.0 - repair_efficacy(cfg, D_next)), D_next)
    pend_next = np.where(fail, 0.0, pend_next)
    # 마모
    rate = cfg.wear_scale * CAT_WEAR[st.cat] * st.rho * (1.0 + st.age / 25.0)
    D_next = D_next + rate * draws.wear
    # 다음 주 초에 들어오는 민원·A/S 접수: 손상이 클수록 잦다
    p_cmp = 1.0 - np.exp(-(CMP_BASE + CMP_SLOPE * np.maximum(D_next - 1.2, 0.0)))
    new = Dyn(
        D=D_next,
        grade_last=np.where(visit, grade_now, dyn.grade_last).astype(np.int8),
        wsv=np.where(visit, 0.0, np.minimum(dyn.wsv + 1.0, 200.0)),
        bd=dyn.bd * BD_DECAY + fail,
        cmp=dyn.cmp * CMP_DECAY + (draws.u_cmp < p_cmp),
        pend=pend_next,
    )
    return new, {
        "visit": visit,
        "fail": fail,
        "e": e_eff,
        "due": due,
        "detected": detected,
        "p_fail": p_fail,
        "surv": surv,
    }


def calibrate_alpha(cfg: WorldConfig, st: Static, dyn: Dyn, rng: np.random.Generator, weeks: int = 40) -> Dyn:
    """번인 동안 사이트별 점검 비율이 목표(사이트마다 다름)에 가도록 절편을 조정하고, 이후 고정한다."""
    n_sites = cfg.n_sites
    target = np.linspace(cfg.visit_rate_lo, cfg.visit_rate_hi, n_sites)
    target = target[rng.permutation(n_sites)]
    st.alpha[:] = -3.4
    for _ in range(weeks):
        draws = Draws.draw(rng, dyn.D.shape)
        dyn, ev = step(cfg, st, dyn, draws)
        # 법정 강제 점검은 제외하고 임의(재량) 점검 확률의 사이트 평균을 목표에 맞춘다
        e = ev["e"]
        e_disc = np.where(ev["due"], np.nan, e)
        for s in range(n_sites):
            m = st.site == s
            cur = np.nanmean(e_disc[m]) if np.isfinite(e_disc[m]).any() else target[s]
            st.alpha[m] += 0.5 * (np.log(target[s]) - np.log(max(cur, 1e-4)))
    return dyn
