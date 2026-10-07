# 평가 — 무엇을 어떻게 재고, 숫자는 무엇을 뜻하나

> 모든 숫자는 합성 세계에서 나왔고 `scripts/fill_numbers.py` 가 `artifacts/` 에서 채운다. CI 가 문서와 산출물의 불일치를 검사한다.
> 시뮬레이터가 정답을 알기 때문에 **추정 방법이 정답을 맞히는지** 를 잴 수 있다. 현실의 효과 크기에 대한 주장이 아니다 (`docs/simulator.md`).

세 개의 세계(각 <!-- num:summary.base.n_sites|d -->60<!-- /num -->개 사이트, 설비 <!-- num:summary.base.n_assets|,d -->7,444<!-- /num -->대, 3년, <!-- num:summary.base.rows|,d -->1,161,264<!-- /num -->행). 학습은 앞 104주, 평가는 뒤 구간이다.

| 세계 | 설정 | 무엇을 보려는가 |
|---|---|---|
| ① base | 기록된 변수로 교란이 모두 설명됨, 설비별 반응 차이 있음 | 보정이 통하는가, 효과순이 위험순을 이기는가 |
| ② hunch | 점검자가 기록에 없는 신호(γ=1.0)로 점검 대상을 정함 | **틀려야 하는 세계** — 감사가 경고하는가 |
| ③ flat | 종류별 발견율·수리 접수 지연·수명 한계가 없음 | 위험순이 충분한 세계에서 효과순이 손해를 보지 않는가 |

## 1. 착시와 보정 — 점검 1회가 막은 고장 (%p, 95% 구간)

| 세계 | 순진한 비교 | 회귀 보정 | IPW | **AIPW** | 정답 | 감사 판정 |
|---|---:|---:|---:|---:|---:|---|
| ① base | <!-- num:scenarios.base.audit.estimates.naive.averted|pp -->-4.9<!-- /num --> | <!-- num:scenarios.base.audit.estimates.regression.averted|pp -->0.6<!-- /num --> | <!-- num:scenarios.base.audit.estimates.ipw.averted|pp -->0.5<!-- /num --> | **<!-- num:summary.base.aipw_averted|pp -->0.7<!-- /num -->** (<!-- num:summary.base.aipw_lo|pp -->0.5<!-- /num -->~<!-- num:summary.base.aipw_hi|pp -->0.9<!-- /num -->) | <!-- num:summary.base.truth_averted|pp -->0.8<!-- /num --> | <!-- num:summary.base.verdict|s -->green<!-- /num --> · 가정 의존도 <!-- num:summary.base.assumption_dependence|s -->높음<!-- /num --> |
| ② hunch | <!-- num:scenarios.hunch.audit.estimates.naive.averted|pp -->-8.2<!-- /num --> | <!-- num:scenarios.hunch.audit.estimates.regression.averted|pp -->-2.2<!-- /num --> | <!-- num:scenarios.hunch.audit.estimates.ipw.averted|pp -->-2.3<!-- /num --> | **<!-- num:summary.hunch.aipw_averted|pp -->-2.0<!-- /num -->** (<!-- num:summary.hunch.aipw_lo|pp -->-2.3<!-- /num -->~<!-- num:summary.hunch.aipw_hi|pp -->-1.8<!-- /num -->) | <!-- num:summary.hunch.truth_averted|pp -->0.7<!-- /num --> | <!-- num:summary.hunch.verdict|s -->red<!-- /num --> (음성 대조 z=<!-- num:summary.hunch.nc_z|.1f -->-13.3<!-- /num -->) |
| ③ flat | <!-- num:scenarios.flat.audit.estimates.naive.averted|pp -->1.3<!-- /num --> | <!-- num:scenarios.flat.audit.estimates.regression.averted|pp -->2.0<!-- /num --> | <!-- num:scenarios.flat.audit.estimates.ipw.averted|pp -->2.0<!-- /num --> | **<!-- num:summary.flat.aipw_averted|pp -->2.0<!-- /num -->** (<!-- num:summary.flat.aipw_lo|pp -->1.9<!-- /num -->~<!-- num:summary.flat.aipw_hi|pp -->2.2<!-- /num -->) | <!-- num:summary.flat.truth_averted|pp -->2.0<!-- /num --> | <!-- num:summary.flat.verdict|s -->green<!-- /num --> · 가정 의존도 <!-- num:summary.flat.assumption_dependence|s -->낮음<!-- /num --> |

읽는 법: 순진한 비교는 점검한 주의 고장률에서 안 한 주를 뺀 값의 부호를 뒤집은 것(양수 = 점검이 고장을 줄임)이다. base 에서 점검한 주의 고장률이 <!-- num:summary.base.outcome_rate_treated|.1% -->12.0%<!-- /num -->, 안 한 주가 <!-- num:summary.base.outcome_rate_control|.1% -->7.1%<!-- /num --> 라서 로그만 보면 점검이 해롭다.
보정하면 부호가 돌아오고 구간이 정답을 덮는다. hunch 에서는 보정해도 정답과 부호가 반대이고, 감사가 빨강이다.

## 2. 95% 구간은 정말 95% 를 덮나 — 몬테카를로

같은 설정의 작은 세계(4개 사이트, 100주)를 <!-- num:coverage.reps|d -->40<!-- /num -->번씩 새로 만들어 구간이 정답을 덮은 비율을 쟀다.

| 추정 방법 | base | flat | hunch (γ=0.6) |
|---|---:|---:|---:|
| 순진한 비교 | <!-- num:summary.coverage.base.naive|.0% -->0%<!-- /num --> | <!-- num:summary.coverage.flat.naive|.0% -->45%<!-- /num --> | <!-- num:summary.coverage.hunch.naive|.0% -->0%<!-- /num --> |
| 회귀 보정 | <!-- num:summary.coverage.base.regression|.0% -->42%<!-- /num --> | <!-- num:summary.coverage.flat.regression|.0% -->42%<!-- /num --> | <!-- num:summary.coverage.hunch.regression|.0% -->2%<!-- /num --> |
| IPW | <!-- num:summary.coverage.base.ipw|.0% -->95%<!-- /num --> | <!-- num:summary.coverage.flat.ipw|.0% -->92%<!-- /num --> | <!-- num:summary.coverage.hunch.ipw|.0% -->12%<!-- /num --> |
| **AIPW (군집 구간)** | **<!-- num:summary.coverage.base.aipw|.0% -->95%<!-- /num -->** | **<!-- num:summary.coverage.flat.aipw|.0% -->92%<!-- /num -->** | <!-- num:summary.coverage.hunch.aipw|.0% -->15%<!-- /num --> |
| AIPW (행 독립 구간) | <!-- num:summary.coverage.base.aipw_iid|.0% -->95%<!-- /num --> | <!-- num:summary.coverage.flat.aipw_iid|.0% -->92%<!-- /num --> | <!-- num:summary.coverage.hunch.aipw_iid|.0% -->20%<!-- /num --> |

- 숨은 교란이 없으면 AIPW 구간이 약 95% 를 덮는다 (40번 반복의 포함률은 ±3.5%p 정도 흔들린다).
- 회귀 보정은 점추정은 맞아도 구간이 결과 모형의 오차를 반영하지 않아 덜 덮는다 — 이중 강건 추정을 쓰는 이유다.
- 이 자료는 설비 내 상관이 작아 군집 구간과 행 독립 구간의 차이가 거의 없다. 군집 보정은 상관이 큰 실제 로그를 위한 안전장치다.
- 숨은 교란(γ=0.6)에서는 어떤 구간도 덮지 못한다. 구간은 기록된 변수 밖의 교란을 모른다.

## 3. 숨은 교란 스윕 — 감사가 틀린 추정을 잡아내나

γ(분석가가 못 보는 신호의 강도)를 올리며 같은 세계를 5 시드씩 돌렸다 (8개 사이트).

| γ | 정답 | 순진한 비교 | AIPW | AIPW 오차 | 구간이 정답을 덮은 비율 | 감사의 음성 대조 경고율 |
|---|---:|---:|---:|---:|---:|---:|
| 0.0 | <!-- num:summary.hunch_sweep.g0_0.truth|pp -->0.8<!-- /num --> | <!-- num:summary.hunch_sweep.g0_0.naive|pp -->-4.7<!-- /num --> | <!-- num:summary.hunch_sweep.g0_0.aipw|pp -->0.7<!-- /num --> | <!-- num:summary.hunch_sweep.g0_0.bias|pp -->-0.1<!-- /num --> | <!-- num:summary.hunch_sweep.g0_0.coverage|.0% -->100%<!-- /num --> | <!-- num:summary.hunch_sweep.g0_0.nc_flag_rate|.0% -->20%<!-- /num --> |
| 0.3 | <!-- num:summary.hunch_sweep.g0_3.truth|pp -->0.8<!-- /num --> | <!-- num:summary.hunch_sweep.g0_3.naive|pp -->-6.3<!-- /num --> | <!-- num:summary.hunch_sweep.g0_3.aipw|pp -->-0.5<!-- /num --> | <!-- num:summary.hunch_sweep.g0_3.bias|pp -->-1.3<!-- /num --> | <!-- num:summary.hunch_sweep.g0_3.coverage|.0% -->0%<!-- /num --> | <!-- num:summary.hunch_sweep.g0_3.nc_flag_rate|.0% -->0%<!-- /num --> |
| 0.6 | <!-- num:summary.hunch_sweep.g0_6.truth|pp -->0.8<!-- /num --> | <!-- num:summary.hunch_sweep.g0_6.naive|pp -->-7.5<!-- /num --> | <!-- num:summary.hunch_sweep.g0_6.aipw|pp -->-1.3<!-- /num --> | <!-- num:summary.hunch_sweep.g0_6.bias|pp -->-2.0<!-- /num --> | <!-- num:summary.hunch_sweep.g0_6.coverage|.0% -->0%<!-- /num --> | <!-- num:summary.hunch_sweep.g0_6.nc_flag_rate|.0% -->60%<!-- /num --> |
| 1.0 | <!-- num:summary.hunch_sweep.g1_0.truth|pp -->0.7<!-- /num --> | <!-- num:summary.hunch_sweep.g1_0.naive|pp -->-8.5<!-- /num --> | <!-- num:summary.hunch_sweep.g1_0.aipw|pp -->-2.7<!-- /num --> | <!-- num:summary.hunch_sweep.g1_0.bias|pp -->-3.4<!-- /num --> | <!-- num:summary.hunch_sweep.g1_0.coverage|.0% -->0%<!-- /num --> | <!-- num:summary.hunch_sweep.g1_0.nc_flag_rate|.0% -->100%<!-- /num --> |
| 1.5 | <!-- num:summary.hunch_sweep.g1_5.truth|pp -->0.7<!-- /num --> | <!-- num:summary.hunch_sweep.g1_5.naive|pp -->-9.3<!-- /num --> | <!-- num:summary.hunch_sweep.g1_5.aipw|pp -->-3.6<!-- /num --> | <!-- num:summary.hunch_sweep.g1_5.bias|pp -->-4.3<!-- /num --> | <!-- num:summary.hunch_sweep.g1_5.coverage|.0% -->0%<!-- /num --> | <!-- num:summary.hunch_sweep.g1_5.nc_flag_rate|.0% -->100%<!-- /num --> |

- **강한 숨은 교란(γ≥1.0)은 항상 잡는다.** 약한 교란(γ=0.3)은 **못 잡는다** — 그 세계에서 AIPW 오차는 효과 자체(정답 <!-- num:summary.hunch_sweep.g0_3.truth|pp -->0.8<!-- /num -->%p)보다 큰데 경고율이 <!-- num:summary.hunch_sweep.g0_3.nc_flag_rate|.0% -->0%<!-- /num --> 이다.
- 교란이 없는 세계(γ=0)에서도 경고율이 <!-- num:summary.hunch_sweep.g0_0.nc_flag_rate|.0% -->20%<!-- /num --> 로 0 이 아니다(5 시드). 오경보가 있다.
- 그래서 신호등과 별개로 **가정 의존도**를 표시하고, 결정이 중요하면 무작위 파일럿을 권한다 (§6).

## 4. 정책 비교 — 사이트·주마다 8곳을 고를 때 점검 100번당 막는 고장

평가 구간 <!-- num:scenarios.base.policy.test_weeks.0|d -->104<!-- /num -->~<!-- num:scenarios.base.policy.test_weeks.1|d -->152<!-- /num -->주, 사이트·주 <!-- num:scenarios.base.policy.n_groups|,d -->2,940<!-- /num -->묶음. 괄호는 95% 구간(사이트·주 묶음 부트스트랩).
"OPE" 는 정답 없이 **로그만으로** 같은 정책의 가치를 추정한 값이다 (선택된 행의 AIPW 점수 합).

### ① base

| 정책 | 정답 기준 | 로그만으로 추정 (OPE) |
|---|---:|---:|
| 무작위 | **<!-- num:scenarios.base.policy.by_k.8.random.true_per100|.2f -->0.81<!-- /num -->** (<!-- num:scenarios.base.policy.ci.random.true_lo|.2f -->0.79<!-- /num -->~<!-- num:scenarios.base.policy.ci.random.true_hi|.2f -->0.83<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.random.ope_per100|.2f -->1.72<!-- /num --> (<!-- num:scenarios.base.policy.ci.random.ope_lo|.1f -->0.6<!-- /num -->~<!-- num:scenarios.base.policy.ci.random.ope_hi|.1f -->2.7<!-- /num -->) |
| 라운드로빈 (가장 오래 안 본 순) | **<!-- num:scenarios.base.policy.by_k.8.round_robin.true_per100|.2f -->1.50<!-- /num -->** (<!-- num:scenarios.base.policy.ci.round_robin.true_lo|.2f -->1.48<!-- /num -->~<!-- num:scenarios.base.policy.ci.round_robin.true_hi|.2f -->1.53<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.round_robin.ope_per100|.2f -->-0.04<!-- /num --> (<!-- num:scenarios.base.policy.ci.round_robin.ope_lo|.1f -->-1.9<!-- /num -->~<!-- num:scenarios.base.policy.ci.round_robin.ope_hi|.1f -->1.8<!-- /num -->) |
| 위험순 — 고장 예측 모형 (보통의 예지보전) | **<!-- num:scenarios.base.policy.by_k.8.risk.true_per100|.2f -->2.63<!-- /num -->** (<!-- num:scenarios.base.policy.ci.risk.true_lo|.2f -->2.60<!-- /num -->~<!-- num:scenarios.base.policy.ci.risk.true_hi|.2f -->2.67<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.risk.ope_per100|.2f -->2.88<!-- /num --> (<!-- num:scenarios.base.policy.ci.risk.ope_lo|.1f -->1.6<!-- /num -->~<!-- num:scenarios.base.policy.ci.risk.ope_hi|.1f -->4.1<!-- /num -->) |
| 위험순 + 수리 접수 제외 규칙 | **<!-- num:scenarios.base.policy.by_k.8.risk_rule.true_per100|.2f -->3.11<!-- /num -->** (<!-- num:scenarios.base.policy.ci.risk_rule.true_lo|.2f -->3.08<!-- /num -->~<!-- num:scenarios.base.policy.ci.risk_rule.true_hi|.2f -->3.15<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.risk_rule.ope_per100|.2f -->3.55<!-- /num --> (<!-- num:scenarios.base.policy.ci.risk_rule.ope_lo|.1f -->2.4<!-- /num -->~<!-- num:scenarios.base.policy.ci.risk_rule.ope_hi|.1f -->4.8<!-- /num -->) |
| 효과순 — 반응도 모형 (직접 구현) | **<!-- num:scenarios.base.policy.by_k.8.responsiveness.true_per100|.2f -->3.42<!-- /num -->** (<!-- num:scenarios.base.policy.ci.responsiveness.true_lo|.2f -->3.38<!-- /num -->~<!-- num:scenarios.base.policy.ci.responsiveness.true_hi|.2f -->3.46<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.responsiveness.ope_per100|.2f -->3.44<!-- /num --> (<!-- num:scenarios.base.policy.ci.responsiveness.ope_lo|.1f -->2.3<!-- /num -->~<!-- num:scenarios.base.policy.ci.responsiveness.ope_hi|.1f -->4.8<!-- /num -->) |
| 효과순 + 수리 접수 제외 규칙 | **<!-- num:scenarios.base.policy.by_k.8.responsiveness_rule.true_per100|.2f -->3.45<!-- /num -->** (<!-- num:scenarios.base.policy.ci.responsiveness_rule.true_lo|.2f -->3.40<!-- /num -->~<!-- num:scenarios.base.policy.ci.responsiveness_rule.true_hi|.2f -->3.48<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.responsiveness_rule.ope_per100|.2f -->3.45<!-- /num --> (<!-- num:scenarios.base.policy.ci.responsiveness_rule.ope_lo|.1f -->2.3<!-- /num -->~<!-- num:scenarios.base.policy.ci.responsiveness_rule.ope_hi|.1f -->4.7<!-- /num -->) |
| 효과순 — DR-learner (트리) | **<!-- num:scenarios.base.policy.by_k.8.dr_gbm.true_per100|.2f -->3.04<!-- /num -->** (<!-- num:scenarios.base.policy.ci.dr_gbm.true_lo|.2f -->3.00<!-- /num -->~<!-- num:scenarios.base.policy.ci.dr_gbm.true_hi|.2f -->3.07<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.dr_gbm.ope_per100|.2f -->3.81<!-- /num --> (<!-- num:scenarios.base.policy.ci.dr_gbm.ope_lo|.1f -->2.5<!-- /num -->~<!-- num:scenarios.base.policy.ci.dr_gbm.ope_hi|.1f -->5.2<!-- /num -->) |
| 효과순 — T-learner | **<!-- num:scenarios.base.policy.by_k.8.t_learner.true_per100|.2f -->2.86<!-- /num -->** (<!-- num:scenarios.base.policy.ci.t_learner.true_lo|.2f -->2.83<!-- /num -->~<!-- num:scenarios.base.policy.ci.t_learner.true_hi|.2f -->2.90<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.t_learner.ope_per100|.2f -->2.16<!-- /num --> (<!-- num:scenarios.base.policy.ci.t_learner.ope_lo|.1f -->0.6<!-- /num -->~<!-- num:scenarios.base.policy.ci.t_learner.ope_hi|.1f -->3.6<!-- /num -->) |
| 효과순 — DragonNet (PyTorch) | **<!-- num:scenarios.base.policy.by_k.8.dragonnet.true_per100|.2f -->2.74<!-- /num -->** (<!-- num:scenarios.base.policy.ci.dragonnet.true_lo|.2f -->2.70<!-- /num -->~<!-- num:scenarios.base.policy.ci.dragonnet.true_hi|.2f -->2.77<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.dragonnet.ope_per100|.2f -->2.68<!-- /num --> (<!-- num:scenarios.base.policy.ci.dragonnet.ope_lo|.1f -->1.4<!-- /num -->~<!-- num:scenarios.base.policy.ci.dragonnet.ope_hi|.1f -->4.1<!-- /num -->) |
| 상한 — 정답 라벨로 학습한 효과 회귀 (관측 변수의 한계) | **<!-- num:scenarios.base.policy.by_k.8.ceiling.true_per100|.2f -->3.68<!-- /num -->** (<!-- num:scenarios.base.policy.ci.ceiling.true_lo|.2f -->3.64<!-- /num -->~<!-- num:scenarios.base.policy.ci.ceiling.true_hi|.2f -->3.71<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.ceiling.ope_per100|.2f -->3.82<!-- /num --> (<!-- num:scenarios.base.policy.ci.ceiling.ope_lo|.1f -->2.4<!-- /num -->~<!-- num:scenarios.base.policy.ci.ceiling.ope_hi|.1f -->5.1<!-- /num -->) |
| 오라클 — 숨은 손상까지 아는 효과순 | **<!-- num:scenarios.base.policy.by_k.8.oracle.true_per100|.2f -->5.54<!-- /num -->** (<!-- num:scenarios.base.policy.ci.oracle.true_lo|.2f -->5.51<!-- /num -->~<!-- num:scenarios.base.policy.ci.oracle.true_hi|.2f -->5.59<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.oracle.ope_per100|.2f -->4.20<!-- /num --> (<!-- num:scenarios.base.policy.ci.oracle.ope_lo|.1f -->2.4<!-- /num -->~<!-- num:scenarios.base.policy.ci.oracle.ope_hi|.1f -->6.1<!-- /num -->) |

- **효과순이 위험순을 +<!-- num:summary.base.lift_resp_vs_risk|.0% -->30%<!-- /num --> 앞선다**, 단순 규칙(수리 접수 제외)을 더한 위험순과도 +<!-- num:summary.base.lift_resp_vs_risk_rule|.0% -->10%<!-- /num --> 차이다. 규칙만으로 위험순에서 +<!-- num:summary.base.lift_risk_rule_vs_risk|.0% -->18%<!-- /num --> 를 얻는다 — 규칙이 대부분의 이득을 이미 가져간다.
- 학습한 효과순은 상한(관측 변수로 도달 가능한 최대)의 <!-- num:summary.base.ceiling_share|.0% -->93%<!-- /num --> 에 도달한다. 오라클과의 차이는 숨은 손상을 모르는 대가다.
- **OPE 의 오차**: 효과순의 정답과 OPE 의 차이가 <!-- num:summary.base.ope_abs_err_resp|.2f -->0.02<!-- /num --> 이다. 구간은 넓어서(약 ±1.2) 정책 간 차이(0.3~0.8)를 로그만으로 구별하기에는 이 규모에서도 빠듯하다.

### ② hunch — 감사가 빨강일 때

| 정책 | 정답 기준 | 로그만으로 추정 (OPE) |
|---|---:|---:|
| 무작위 | **<!-- num:scenarios.hunch.policy.by_k.8.random.true_per100|.2f -->0.69<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.random.true_lo|.2f -->0.67<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.random.true_hi|.2f -->0.71<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.random.ope_per100|.2f -->-1.74<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.random.ope_lo|.1f -->-3.0<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.random.ope_hi|.1f -->-0.2<!-- /num -->) |
| 라운드로빈 (가장 오래 안 본 순) | **<!-- num:scenarios.hunch.policy.by_k.8.round_robin.true_per100|.2f -->0.97<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.round_robin.true_lo|.2f -->0.95<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.round_robin.true_hi|.2f -->0.99<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.round_robin.ope_per100|.2f -->-2.23<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.round_robin.ope_lo|.1f -->-4.1<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.round_robin.ope_hi|.1f -->-0.3<!-- /num -->) |
| 위험순 — 고장 예측 모형 (보통의 예지보전) | **<!-- num:scenarios.hunch.policy.by_k.8.risk.true_per100|.2f -->1.77<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.risk.true_lo|.2f -->1.74<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.risk.true_hi|.2f -->1.80<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.risk.ope_per100|.2f -->-7.13<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.risk.ope_lo|.1f -->-8.1<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.risk.ope_hi|.1f -->-6.0<!-- /num -->) |
| 위험순 + 수리 접수 제외 규칙 | **<!-- num:scenarios.hunch.policy.by_k.8.risk_rule.true_per100|.2f -->2.35<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.risk_rule.true_lo|.2f -->2.31<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.risk_rule.true_hi|.2f -->2.38<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.risk_rule.ope_per100|.2f -->-5.51<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.risk_rule.ope_lo|.1f -->-6.7<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.risk_rule.ope_hi|.1f -->-4.4<!-- /num -->) |
| 효과순 — 반응도 모형 (직접 구현) | **<!-- num:scenarios.hunch.policy.by_k.8.responsiveness.true_per100|.2f -->0.03<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.responsiveness.true_lo|.2f -->0.03<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.responsiveness.true_hi|.2f -->0.04<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.responsiveness.ope_per100|.2f -->-0.35<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.responsiveness.ope_lo|.1f -->-1.6<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.responsiveness.ope_hi|.1f -->0.8<!-- /num -->) |
| 효과순 + 수리 접수 제외 규칙 | **<!-- num:scenarios.hunch.policy.by_k.8.responsiveness_rule.true_per100|.2f -->0.04<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.responsiveness_rule.true_lo|.2f -->0.03<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.responsiveness_rule.true_hi|.2f -->0.04<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.responsiveness_rule.ope_per100|.2f -->-0.33<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.responsiveness_rule.ope_lo|.1f -->-1.5<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.responsiveness_rule.ope_hi|.1f -->0.8<!-- /num -->) |
| 효과순 — DR-learner (트리) | **<!-- num:scenarios.hunch.policy.by_k.8.dr_gbm.true_per100|.2f -->0.27<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.dr_gbm.true_lo|.2f -->0.26<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.dr_gbm.true_hi|.2f -->0.28<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.dr_gbm.ope_per100|.2f -->0.75<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.dr_gbm.ope_lo|.1f -->-0.3<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.dr_gbm.ope_hi|.1f -->1.9<!-- /num -->) |
| 효과순 — T-learner | **<!-- num:scenarios.hunch.policy.by_k.8.t_learner.true_per100|.2f -->1.47<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.t_learner.true_lo|.2f -->1.45<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.t_learner.true_hi|.2f -->1.49<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.t_learner.ope_per100|.2f -->-0.67<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.t_learner.ope_lo|.1f -->-2.2<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.t_learner.ope_hi|.1f -->0.8<!-- /num -->) |
| 효과순 — DragonNet (PyTorch) | **<!-- num:scenarios.hunch.policy.by_k.8.dragonnet.true_per100|.2f -->0.63<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.dragonnet.true_lo|.2f -->0.61<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.dragonnet.true_hi|.2f -->0.65<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.dragonnet.ope_per100|.2f -->-0.47<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.dragonnet.ope_lo|.1f -->-2.4<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.dragonnet.ope_hi|.1f -->1.1<!-- /num -->) |
| 상한 — 정답 라벨로 학습한 효과 회귀 (관측 변수의 한계) | **<!-- num:scenarios.hunch.policy.by_k.8.ceiling.true_per100|.2f -->2.83<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.ceiling.true_lo|.2f -->2.80<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.ceiling.true_hi|.2f -->2.88<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.ceiling.ope_per100|.2f -->-3.35<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.ceiling.ope_lo|.1f -->-4.5<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.ceiling.ope_hi|.1f -->-2.2<!-- /num -->) |
| 오라클 — 숨은 손상까지 아는 효과순 | **<!-- num:scenarios.hunch.policy.by_k.8.oracle.true_per100|.2f -->4.61<!-- /num -->** (<!-- num:scenarios.hunch.policy.ci.oracle.true_lo|.2f -->4.58<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.oracle.true_hi|.2f -->4.66<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.oracle.ope_per100|.2f -->-10.02<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.oracle.ope_lo|.1f -->-13.3<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.oracle.ope_hi|.1f -->-6.9<!-- /num -->) |

오염된 DR 점수로 학습한 효과 모형은 **무작위보다 나쁘다**. 위험순은 점검자의 편향과 무관한 고장 예측이라 영향이 작다. OPE 는 부호까지 틀려서 이 세계에서 로그만으로 정책을 고르면 안 된다.

### ③ flat

| 정책 | 정답 기준 | 로그만으로 추정 (OPE) |
|---|---:|---:|
| 무작위 | **<!-- num:scenarios.flat.policy.by_k.8.random.true_per100|.2f -->1.98<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.random.true_lo|.2f -->1.93<!-- /num -->~<!-- num:scenarios.flat.policy.ci.random.true_hi|.2f -->2.05<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.random.ope_per100|.2f -->2.62<!-- /num --> (<!-- num:scenarios.flat.policy.ci.random.ope_lo|.1f -->1.7<!-- /num -->~<!-- num:scenarios.flat.policy.ci.random.ope_hi|.1f -->3.4<!-- /num -->) |
| 라운드로빈 (가장 오래 안 본 순) | **<!-- num:scenarios.flat.policy.by_k.8.round_robin.true_per100|.2f -->3.66<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.round_robin.true_lo|.2f -->3.60<!-- /num -->~<!-- num:scenarios.flat.policy.ci.round_robin.true_hi|.2f -->3.74<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.round_robin.ope_per100|.2f -->4.00<!-- /num --> (<!-- num:scenarios.flat.policy.ci.round_robin.ope_lo|.1f -->2.9<!-- /num -->~<!-- num:scenarios.flat.policy.ci.round_robin.ope_hi|.1f -->5.0<!-- /num -->) |
| 위험순 — 고장 예측 모형 (보통의 예지보전) | **<!-- num:scenarios.flat.policy.by_k.8.risk.true_per100|.2f -->8.06<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.risk.true_lo|.2f -->7.95<!-- /num -->~<!-- num:scenarios.flat.policy.ci.risk.true_hi|.2f -->8.21<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.risk.ope_per100|.2f -->7.92<!-- /num --> (<!-- num:scenarios.flat.policy.ci.risk.ope_lo|.1f -->6.9<!-- /num -->~<!-- num:scenarios.flat.policy.ci.risk.ope_hi|.1f -->8.8<!-- /num -->) |
| 위험순 + 수리 접수 제외 규칙 | **<!-- num:scenarios.flat.policy.by_k.8.risk_rule.true_per100|.2f -->8.06<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.risk_rule.true_lo|.2f -->7.95<!-- /num -->~<!-- num:scenarios.flat.policy.ci.risk_rule.true_hi|.2f -->8.21<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.risk_rule.ope_per100|.2f -->7.92<!-- /num --> (<!-- num:scenarios.flat.policy.ci.risk_rule.ope_lo|.1f -->6.9<!-- /num -->~<!-- num:scenarios.flat.policy.ci.risk_rule.ope_hi|.1f -->8.8<!-- /num -->) |
| 효과순 — 반응도 모형 (직접 구현) | **<!-- num:scenarios.flat.policy.by_k.8.responsiveness.true_per100|.2f -->8.23<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.responsiveness.true_lo|.2f -->8.12<!-- /num -->~<!-- num:scenarios.flat.policy.ci.responsiveness.true_hi|.2f -->8.37<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.responsiveness.ope_per100|.2f -->7.98<!-- /num --> (<!-- num:scenarios.flat.policy.ci.responsiveness.ope_lo|.1f -->7.2<!-- /num -->~<!-- num:scenarios.flat.policy.ci.responsiveness.ope_hi|.1f -->8.9<!-- /num -->) |
| 효과순 + 수리 접수 제외 규칙 | **<!-- num:scenarios.flat.policy.by_k.8.responsiveness_rule.true_per100|.2f -->8.23<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.responsiveness_rule.true_lo|.2f -->8.12<!-- /num -->~<!-- num:scenarios.flat.policy.ci.responsiveness_rule.true_hi|.2f -->8.37<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.responsiveness_rule.ope_per100|.2f -->7.98<!-- /num --> (<!-- num:scenarios.flat.policy.ci.responsiveness_rule.ope_lo|.1f -->7.2<!-- /num -->~<!-- num:scenarios.flat.policy.ci.responsiveness_rule.ope_hi|.1f -->8.9<!-- /num -->) |
| 효과순 — DR-learner (트리) | **<!-- num:scenarios.flat.policy.by_k.8.dr_gbm.true_per100|.2f -->8.14<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.dr_gbm.true_lo|.2f -->8.03<!-- /num -->~<!-- num:scenarios.flat.policy.ci.dr_gbm.true_hi|.2f -->8.27<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.dr_gbm.ope_per100|.2f -->7.62<!-- /num --> (<!-- num:scenarios.flat.policy.ci.dr_gbm.ope_lo|.1f -->6.7<!-- /num -->~<!-- num:scenarios.flat.policy.ci.dr_gbm.ope_hi|.1f -->8.6<!-- /num -->) |
| 효과순 — T-learner | **<!-- num:scenarios.flat.policy.by_k.8.t_learner.true_per100|.2f -->8.13<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.t_learner.true_lo|.2f -->8.02<!-- /num -->~<!-- num:scenarios.flat.policy.ci.t_learner.true_hi|.2f -->8.28<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.t_learner.ope_per100|.2f -->7.96<!-- /num --> (<!-- num:scenarios.flat.policy.ci.t_learner.ope_lo|.1f -->7.1<!-- /num -->~<!-- num:scenarios.flat.policy.ci.t_learner.ope_hi|.1f -->8.9<!-- /num -->) |
| 효과순 — DragonNet (PyTorch) | **<!-- num:scenarios.flat.policy.by_k.8.dragonnet.true_per100|.2f -->7.20<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.dragonnet.true_lo|.2f -->7.10<!-- /num -->~<!-- num:scenarios.flat.policy.ci.dragonnet.true_hi|.2f -->7.32<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.dragonnet.ope_per100|.2f -->7.19<!-- /num --> (<!-- num:scenarios.flat.policy.ci.dragonnet.ope_lo|.1f -->6.4<!-- /num -->~<!-- num:scenarios.flat.policy.ci.dragonnet.ope_hi|.1f -->8.0<!-- /num -->) |
| 상한 — 정답 라벨로 학습한 효과 회귀 (관측 변수의 한계) | **<!-- num:scenarios.flat.policy.by_k.8.ceiling.true_per100|.2f -->8.71<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.ceiling.true_lo|.2f -->8.59<!-- /num -->~<!-- num:scenarios.flat.policy.ci.ceiling.true_hi|.2f -->8.85<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.ceiling.ope_per100|.2f -->9.08<!-- /num --> (<!-- num:scenarios.flat.policy.ci.ceiling.ope_lo|.1f -->8.1<!-- /num -->~<!-- num:scenarios.flat.policy.ci.ceiling.ope_hi|.1f -->9.9<!-- /num -->) |
| 오라클 — 숨은 손상까지 아는 효과순 | **<!-- num:scenarios.flat.policy.by_k.8.oracle.true_per100|.2f -->13.45<!-- /num -->** (<!-- num:scenarios.flat.policy.ci.oracle.true_lo|.2f -->13.30<!-- /num -->~<!-- num:scenarios.flat.policy.ci.oracle.true_hi|.2f -->13.64<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.oracle.ope_per100|.2f -->12.45<!-- /num --> (<!-- num:scenarios.flat.policy.ci.oracle.ope_lo|.1f -->11.2<!-- /num -->~<!-- num:scenarios.flat.policy.ci.oracle.ope_hi|.1f -->13.8<!-- /num -->) |

설비별 반응 차이가 없으므로 위험순이 충분하다. 효과순은 손해도 이득도 거의 없다(+<!-- num:summary.flat.lift_resp_vs_risk|.0% -->2%<!-- /num -->).

## 5. 학습곡선 — 고객사 몇 곳을 풀링해야 처음 보는 사이트에서 이기나

60개 사이트 세계에서 <!-- num:summary.curve.n_test_sites|d -->12<!-- /num -->곳을 끝까지 떼어 두고(신규 고객사), 나머지에서 k 곳을 무작위로 골라 학습했다. k 마다 2~5번 반복한 평균이다 (표준편차는 콘솔의 표 보기).

| 학습 사이트 수 | 효과순 | 위험순 | 위험순 + 규칙 | 효과순 + 규칙 | OPE 절대 오차 (효과순) |
|---|---:|---:|---:|---:|---:|
| 4곳 | <!-- num:summary.curve.by_k.k4.responsiveness|.2f -->2.52<!-- /num --> | <!-- num:summary.curve.by_k.k4.risk|.2f -->2.52<!-- /num --> | <!-- num:summary.curve.by_k.k4.risk_rule|.2f -->2.89<!-- /num --> | <!-- num:summary.curve.by_k.k4.responsiveness_rule|.2f -->2.60<!-- /num --> | <!-- num:summary.curve.by_k.k4.ope_err_responsiveness|.2f -->0.75<!-- /num --> |
| 8곳 | <!-- num:summary.curve.by_k.k8.responsiveness|.2f -->2.83<!-- /num --> | <!-- num:summary.curve.by_k.k8.risk|.2f -->2.64<!-- /num --> | <!-- num:summary.curve.by_k.k8.risk_rule|.2f -->3.06<!-- /num --> | <!-- num:summary.curve.by_k.k8.responsiveness_rule|.2f -->2.91<!-- /num --> | <!-- num:summary.curve.by_k.k8.ope_err_responsiveness|.2f -->0.91<!-- /num --> |
| 16곳 | <!-- num:summary.curve.by_k.k16.responsiveness|.2f -->3.28<!-- /num --> | <!-- num:summary.curve.by_k.k16.risk|.2f -->2.70<!-- /num --> | <!-- num:summary.curve.by_k.k16.risk_rule|.2f -->3.15<!-- /num --> | <!-- num:summary.curve.by_k.k16.responsiveness_rule|.2f -->3.30<!-- /num --> | <!-- num:summary.curve.by_k.k16.ope_err_responsiveness|.2f -->0.60<!-- /num --> |
| 32곳 | <!-- num:summary.curve.by_k.k32.responsiveness|.2f -->3.48<!-- /num --> | <!-- num:summary.curve.by_k.k32.risk|.2f -->2.74<!-- /num --> | <!-- num:summary.curve.by_k.k32.risk_rule|.2f -->3.22<!-- /num --> | <!-- num:summary.curve.by_k.k32.responsiveness_rule|.2f -->3.48<!-- /num --> | <!-- num:summary.curve.by_k.k32.ope_err_responsiveness|.2f -->0.38<!-- /num --> |
| 48곳 | <!-- num:summary.curve.by_k.k48.responsiveness|.2f -->3.44<!-- /num --> | <!-- num:summary.curve.by_k.k48.risk|.2f -->2.72<!-- /num --> | <!-- num:summary.curve.by_k.k48.risk_rule|.2f -->3.19<!-- /num --> | <!-- num:summary.curve.by_k.k48.responsiveness_rule|.2f -->3.45<!-- /num --> | <!-- num:summary.curve.by_k.k48.ope_err_responsiveness|.2f -->0.35<!-- /num --> |

(콘솔의 "누구에게" 탭에 그래프와 표가 있다)

- <!-- num:summary.curve.k_min|d -->4<!-- /num -->곳: 효과순 <!-- num:summary.curve.resp_min|.2f -->2.52<!-- /num --> vs 위험순 <!-- num:summary.curve.risk_min|.2f -->2.52<!-- /num --> (효과순 <!-- num:summary.curve.lift_min|.0% -->0%<!-- /num -->).
- <!-- num:summary.curve.k_max|d -->48<!-- /num -->곳: 효과순 <!-- num:summary.curve.resp_max|.2f -->3.44<!-- /num --> vs 위험순 <!-- num:summary.curve.risk_max|.2f -->2.72<!-- /num --> (효과순 <!-- num:summary.curve.lift_max|.0% -->26%<!-- /num -->), 위험순 + 규칙 <!-- num:summary.curve.rule_max|.2f -->3.19<!-- /num -->.
- OPE 의 평균 절대 오차 <!-- num:summary.curve.ope_err_min|.2f -->0.75<!-- /num --> → <!-- num:summary.curve.ope_err_max|.2f -->0.35<!-- /num -->.

## 6. 무작위 파일럿이 관측 추정을 시험한다

hunch 세계에서 설비의 40% 를 무작위 파일럿으로 지정했다 (평소 점검 비율로 동전 던지기, 겹치지 않는 4주 창).

| | 점검 1회가 막은 고장 |
|---|---:|
| 관측 로그 AIPW (파일럿 설비 제외) | <!-- num:summary.pilot.obs_averted|pp -->-1.8<!-- /num -->%p |
| **무작위 파일럿 평균 차이** | **<!-- num:summary.pilot.pilot_averted|pp -->0.6<!-- /num -->%p** (<!-- num:summary.pilot.pilot_lo|pp -->-0.0<!-- /num -->~<!-- num:summary.pilot.pilot_hi|pp -->1.2<!-- /num -->) |
| 정답 (파일럿 설비) | <!-- num:summary.pilot.truth|pp -->1.0<!-- /num -->%p |

파일럿 설비 <!-- num:summary.pilot.n_assets|,d -->2,940<!-- /num -->대, 독립 창 <!-- num:summary.pilot.n_windows|,d -->112,956<!-- /num -->개. 파일럿 구간은 넓지만 **무편향**이라 관측 추정과의 모순을 드러낸다(모순 여부: <!-- num:summary.pilot.contradicts|s -->True<!-- /num -->).
평균 효과가 작으면 한 고객사의 파일럿으로는 검출이 불가능하다 — 계획기가 필요한 규모를 알려 준다 (콘솔 "믿어도 되나" 탭, `POST /v1/pilot/plan`).

## 7. 재현

```bash
make pipeline     # 시나리오 3종 → 파일럿 → 몬테카를로 → 스윕 → 학습곡선 → 요약 → 정적 데모 → 숫자 채우기
make check-numbers
```
