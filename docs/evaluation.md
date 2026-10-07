# 평가

> 이 문서의 숫자는 모두 합성(SYNTHETIC) 데이터, 곧 시뮬레이터가 만든 세계에서 나왔습니다. `scripts/fill_numbers.py` 가 `artifacts/` 에서 숫자를 채우고, CI 가 문서와 산출물이 다른지 검사합니다.
> 시뮬레이터가 정답을 알고 있어서 추정 방법이 정답을 맞히는지 잴 수 있습니다. 현실의 효과 크기는 주장하지 않습니다 (`docs/simulator.md`).

합성 세계 세 개로 평가했습니다. 세계마다 사이트가 <!-- num:summary.base.n_sites|d -->60<!-- /num -->개, 설비가 <!-- num:summary.base.n_assets|,d -->7,444<!-- /num -->대이고, 3년치 로그가 <!-- num:summary.base.rows|,d -->1,161,264<!-- /num -->행입니다. 앞 104주로 학습하고 그 뒤 구간으로 평가했습니다.

| 세계 | 설정 | 무엇을 보려는가 |
|---|---|---|
| ① base | 점검 대상을 고른 이유가 모두 기록에 있음. 설비마다 점검에 반응하는 정도가 다름 | 보정이 통하는지, 효과순이 위험순을 이기는지 |
| ② hunch | 점검자가 기록에 없는 신호(세기 γ=1.0)를 보고 점검 대상을 정함 | 추정이 틀려야 하는 세계. 감사가 경고하는지 봄 |
| ③ flat | 설비 종류별로 달랐던 발견율, 수리 접수 지연, 수명 한계를 모두 껐음 | 위험순만으로 충분한 세계에서도 효과순이 손해를 보지 않는지 |

점검 여부와 고장에 함께 영향을 주는 요인을 교란이라 하고, 그중 기록에 없는 이유로 점검 대상을 고르는 것을 숨은 교란이라 합니다. ② hunch 가 그런 세계입니다.

## 1. 착시와 보정

점검 1회가 막은 고장(%p, 95% 구간)을 세 세계에서 비교했습니다. 같은 로그에 네 가지 방법을 적용해 정답과 견줬고, %p 는 고장률의 퍼센트포인트 차이입니다.

- 순진한 비교: 점검한 주와 안 한 주의 고장률을 그대로 비교함
- 회귀 보정: 기록된 변수를 넣은 회귀로 그 차이를 고침
- IPW(inverse probability weighting, 역확률 가중): 점검할 확률의 역수로 가중해 두 쪽의 조건을 맞춤
- AIPW(augmented IPW): IPW 와 회귀 보정을 합친 방법. 점검 확률 모형과 결과 모형 중 하나만 맞아도 추정이 맞아서 이중 강건 추정이라고도 함

감사 판정은 이 추정을 믿어도 되는지 따로 점검한 결과입니다.

| 세계 | 순진한 비교 | 회귀 보정 | IPW | AIPW | 정답 | 감사 판정 |
|---|---:|---:|---:|---:|---:|---|
| ① base | <!-- num:scenarios.base.audit.estimates.naive.averted|pp -->-4.9<!-- /num --> | <!-- num:scenarios.base.audit.estimates.regression.averted|pp -->0.6<!-- /num --> | <!-- num:scenarios.base.audit.estimates.ipw.averted|pp -->0.5<!-- /num --> | <!-- num:summary.base.aipw_averted|pp -->0.7<!-- /num --> (<!-- num:summary.base.aipw_lo|pp -->0.5<!-- /num -->~<!-- num:summary.base.aipw_hi|pp -->0.9<!-- /num -->) | <!-- num:summary.base.truth_averted|pp -->0.8<!-- /num --> | <!-- num:summary.base.verdict|s -->green<!-- /num --> · 가정 의존도 <!-- num:summary.base.assumption_dependence|s -->높음<!-- /num --> |
| ② hunch | <!-- num:scenarios.hunch.audit.estimates.naive.averted|pp -->-8.2<!-- /num --> | <!-- num:scenarios.hunch.audit.estimates.regression.averted|pp -->-2.2<!-- /num --> | <!-- num:scenarios.hunch.audit.estimates.ipw.averted|pp -->-2.3<!-- /num --> | <!-- num:summary.hunch.aipw_averted|pp -->-2.0<!-- /num --> (<!-- num:summary.hunch.aipw_lo|pp -->-2.3<!-- /num -->~<!-- num:summary.hunch.aipw_hi|pp -->-1.8<!-- /num -->) | <!-- num:summary.hunch.truth_averted|pp -->0.7<!-- /num --> | <!-- num:summary.hunch.verdict|s -->red<!-- /num --> (음성 대조 z=<!-- num:summary.hunch.nc_z|.1f -->-13.3<!-- /num -->) |
| ③ flat | <!-- num:scenarios.flat.audit.estimates.naive.averted|pp -->1.3<!-- /num --> | <!-- num:scenarios.flat.audit.estimates.regression.averted|pp -->2.0<!-- /num --> | <!-- num:scenarios.flat.audit.estimates.ipw.averted|pp -->2.0<!-- /num --> | <!-- num:summary.flat.aipw_averted|pp -->2.0<!-- /num --> (<!-- num:summary.flat.aipw_lo|pp -->1.9<!-- /num -->~<!-- num:summary.flat.aipw_hi|pp -->2.2<!-- /num -->) | <!-- num:summary.flat.truth_averted|pp -->2.0<!-- /num --> | <!-- num:summary.flat.verdict|s -->green<!-- /num --> · 가정 의존도 <!-- num:summary.flat.assumption_dependence|s -->낮음<!-- /num --> |

읽는 법: 순진한 비교는 (점검한 주의 고장률 - 안 한 주의 고장률)의 부호를 뒤집은 값이라 양수면 점검이 고장을 줄였다는 뜻입니다. base 에서 점검한 주의 고장률은 <!-- num:summary.base.outcome_rate_treated|.1% -->12.0%<!-- /num -->, 안 한 주는 <!-- num:summary.base.outcome_rate_control|.1% -->7.1%<!-- /num -->라서 로그만 보면 점검이 오히려 해로워 보입니다.

보정하면 base 에서는 부호가 돌아오고 95% 구간이 정답을 덮습니다. **hunch 에서는 보정해도 부호가 정답과 반대이고, 감사 판정은 red 입니다.**

red 의 근거는 음성 대조입니다. 점검이 원인일 수 없는 결과(점검 이전 구간의 고장)에도 '효과'가 나오는지 보는 검사로, 나오면 기록에 없는 이유로 점검 대상을 골랐다는 신호입니다. 표의 z 는 그 '효과'를 표준오차로 나눈 값입니다.

가정 의존도는 관측 변수 하나를 뺐을 때 추정이 움직이는 정도이고, 신호등과 따로 표시합니다.

## 2. 95% 구간 포함률

95% 구간이 정답을 덮은 비율을 몬테카를로로 쟀습니다. 같은 설정의 작은 세계(사이트 4개, 100주)를 설정마다 <!-- num:coverage.reps|d -->40<!-- /num -->번 새로 만들어 시험을 되풀이했고, 표의 숫자가 그 비율입니다. 95% 에 가까울수록 좋습니다.

| 추정 방법 | base | flat | hunch (γ=0.6) |
|---|---:|---:|---:|
| 순진한 비교 | <!-- num:summary.coverage.base.naive|.0% -->0%<!-- /num --> | <!-- num:summary.coverage.flat.naive|.0% -->45%<!-- /num --> | <!-- num:summary.coverage.hunch.naive|.0% -->0%<!-- /num --> |
| 회귀 보정 | <!-- num:summary.coverage.base.regression|.0% -->42%<!-- /num --> | <!-- num:summary.coverage.flat.regression|.0% -->42%<!-- /num --> | <!-- num:summary.coverage.hunch.regression|.0% -->2%<!-- /num --> |
| IPW | <!-- num:summary.coverage.base.ipw|.0% -->95%<!-- /num --> | <!-- num:summary.coverage.flat.ipw|.0% -->92%<!-- /num --> | <!-- num:summary.coverage.hunch.ipw|.0% -->12%<!-- /num --> |
| AIPW (설비별로 묶은 구간) | **<!-- num:summary.coverage.base.aipw|.0% -->95%<!-- /num -->** | <!-- num:summary.coverage.flat.aipw|.0% -->92%<!-- /num --> | <!-- num:summary.coverage.hunch.aipw|.0% -->15%<!-- /num --> |
| AIPW (행을 독립으로 본 구간) | <!-- num:summary.coverage.base.aipw_iid|.0% -->95%<!-- /num --> | <!-- num:summary.coverage.flat.aipw_iid|.0% -->92%<!-- /num --> | <!-- num:summary.coverage.hunch.aipw_iid|.0% -->20%<!-- /num --> |

- 숨은 교란이 없으면 AIPW 구간은 정답을 약 95% 덮습니다. 40번 반복해서 잰 비율이라 ±3.5%p 정도의 오차가 있습니다.
- 회귀 보정은 점추정이 맞아도 구간이 정답을 덜 덮습니다. 구간에 결과 모형(고장을 예측하는 모형)의 오차가 들어가지 않기 때문입니다. 이중 강건 추정을 쓰는 것도 이 때문입니다.
- 이 자료는 같은 설비의 여러 주 사이 상관(설비 내 상관)이 작아서 설비별로 묶은 구간과 행을 독립으로 본 구간이 거의 같습니다. 설비별로 묶는 것은 상관이 큰 실제 로그에 대비한 안전장치입니다.
- 기록에 없는 신호가 점검 대상 선택에 작용하는 hunch(γ=0.6)에서는 어떤 구간도 정답을 제대로 덮지 못합니다. 구간은 기록된 변수 밖의 요인을 모르기 때문입니다.

## 3. 기록에 없는 이유의 강도별 감사 결과

기록에 없는 이유의 강도, 곧 분석가가 볼 수 없는 신호의 세기 γ 를 단계적으로 올려 가며 감사가 틀린 추정을 잡아내는지 봤습니다(이렇게 값을 바꿔 훑는 것이 스윕). γ 마다 같은 세계(사이트 8개)를 시드(난수의 출발값) 5개로 돌렸습니다. AIPW 오차는 추정에서 정답을 뺀 값이고, 경고율은 시드 5개 중 감사의 음성 대조가 경고한 비율입니다.

| γ | 정답 | 순진한 비교 | AIPW | AIPW 오차 | 구간이 정답을 덮은 비율 | 감사의 음성 대조 경고율 |
|---|---:|---:|---:|---:|---:|---:|
| 0.0 | <!-- num:summary.hunch_sweep.g0_0.truth|pp -->0.8<!-- /num --> | <!-- num:summary.hunch_sweep.g0_0.naive|pp -->-4.7<!-- /num --> | <!-- num:summary.hunch_sweep.g0_0.aipw|pp -->0.7<!-- /num --> | <!-- num:summary.hunch_sweep.g0_0.bias|pp -->-0.1<!-- /num --> | <!-- num:summary.hunch_sweep.g0_0.coverage|.0% -->100%<!-- /num --> | <!-- num:summary.hunch_sweep.g0_0.nc_flag_rate|.0% -->20%<!-- /num --> |
| 0.3 | <!-- num:summary.hunch_sweep.g0_3.truth|pp -->0.8<!-- /num --> | <!-- num:summary.hunch_sweep.g0_3.naive|pp -->-6.3<!-- /num --> | <!-- num:summary.hunch_sweep.g0_3.aipw|pp -->-0.5<!-- /num --> | <!-- num:summary.hunch_sweep.g0_3.bias|pp -->-1.3<!-- /num --> | <!-- num:summary.hunch_sweep.g0_3.coverage|.0% -->0%<!-- /num --> | <!-- num:summary.hunch_sweep.g0_3.nc_flag_rate|.0% -->0%<!-- /num --> |
| 0.6 | <!-- num:summary.hunch_sweep.g0_6.truth|pp -->0.8<!-- /num --> | <!-- num:summary.hunch_sweep.g0_6.naive|pp -->-7.5<!-- /num --> | <!-- num:summary.hunch_sweep.g0_6.aipw|pp -->-1.3<!-- /num --> | <!-- num:summary.hunch_sweep.g0_6.bias|pp -->-2.0<!-- /num --> | <!-- num:summary.hunch_sweep.g0_6.coverage|.0% -->0%<!-- /num --> | <!-- num:summary.hunch_sweep.g0_6.nc_flag_rate|.0% -->60%<!-- /num --> |
| 1.0 | <!-- num:summary.hunch_sweep.g1_0.truth|pp -->0.7<!-- /num --> | <!-- num:summary.hunch_sweep.g1_0.naive|pp -->-8.5<!-- /num --> | <!-- num:summary.hunch_sweep.g1_0.aipw|pp -->-2.7<!-- /num --> | <!-- num:summary.hunch_sweep.g1_0.bias|pp -->-3.4<!-- /num --> | <!-- num:summary.hunch_sweep.g1_0.coverage|.0% -->0%<!-- /num --> | <!-- num:summary.hunch_sweep.g1_0.nc_flag_rate|.0% -->100%<!-- /num --> |
| 1.5 | <!-- num:summary.hunch_sweep.g1_5.truth|pp -->0.7<!-- /num --> | <!-- num:summary.hunch_sweep.g1_5.naive|pp -->-9.3<!-- /num --> | <!-- num:summary.hunch_sweep.g1_5.aipw|pp -->-3.6<!-- /num --> | <!-- num:summary.hunch_sweep.g1_5.bias|pp -->-4.3<!-- /num --> | <!-- num:summary.hunch_sweep.g1_5.coverage|.0% -->0%<!-- /num --> | <!-- num:summary.hunch_sweep.g1_5.nc_flag_rate|.0% -->100%<!-- /num --> |

- γ≥1.0 이면 감사가 항상 경고했습니다. γ=0.3 에서는 **경고하지 못했습니다.** 이 세계에서 AIPW 오차는 효과 자체(정답 <!-- num:summary.hunch_sweep.g0_3.truth|pp -->0.8<!-- /num -->%p)보다 큰데도 경고율이 <!-- num:summary.hunch_sweep.g0_3.nc_flag_rate|.0% -->0%<!-- /num --> 입니다.
- 신호가 전혀 없는 γ=0 에서도 경고율은 <!-- num:summary.hunch_sweep.g0_0.nc_flag_rate|.0% -->20%<!-- /num --> 입니다(시드 5개 기준). 오경보가 있습니다.
- 감사가 약한 신호를 놓치고 오경보도 내므로, 결정이 중요하면 무작위 파일럿을 권합니다 (§6).

## 4. 정책 비교

사이트·주마다 설비 8곳을 고를 때 점검 100번당 막는 고장 수로 정책(점검할 곳을 고르는 규칙)을 비교합니다.

평가 구간은 <!-- num:scenarios.base.policy.test_weeks.0|d -->104<!-- /num -->~<!-- num:scenarios.base.policy.test_weeks.1|d -->152<!-- /num -->주, 사이트·주 묶음은 <!-- num:scenarios.base.policy.n_groups|,d -->2,940<!-- /num -->개입니다. 괄호 안은 95% 구간이고, 사이트·주 묶음 단위로 다시 뽑는 방법(부트스트랩)으로 구했습니다.

'정답 기준'은 시뮬레이터가 아는 정답으로 채점한 값이고, '로그만으로 추정'은 정답 없이 로그만으로 추정한 값입니다. 후자를 OPE(off-policy evaluation)라 하며, 선택된 행의 AIPW 점수를 더해 구합니다.

비교한 정책은 다음과 같습니다.

- 무작위는 설비를 아무렇게나, 라운드로빈은 가장 오래 안 본 설비부터 고름
- 위험순은 고장이 날 것 같은 설비부터(보통의 예지보전), 효과순은 점검했을 때 고장이 더 많이 줄 것 같은 설비부터 고름
- 수리 접수 제외 규칙: 이미 수리 접수가 된 설비를 건너뛰는 단순 규칙
- 효과순에 쓰는 효과 추정은 네 가지임. 반응도 모형은 '점검 없이 고장날 확률 × 점검이 그 위험을 줄이는 정도'로 효과를 구조화한 모형(직접 구현). DR-learner 는 AIPW 점수를 목표로 트리 모형을 학습. T-learner 는 점검한 설비와 안 한 설비에 모형을 따로 맞춤. DragonNet(PyTorch)은 점검 확률과 결과를 신경망 하나로 함께 학습
- 상한과 오라클은 시뮬레이터만 아는 정보를 쓰는 비교 기준임. 상한은 정답 라벨로 학습한 효과 회귀로, 기록된 변수만으로 낼 수 있는 최대치. 오라클은 기록에 없는 숨은 손상까지 아는 효과순

### ① base (평범한 세계)

| 정책 | 정답 기준 | 로그만으로 추정 (OPE) |
|---|---:|---:|
| 무작위 | <!-- num:scenarios.base.policy.by_k.8.random.true_per100|.2f -->0.81<!-- /num --> (<!-- num:scenarios.base.policy.ci.random.true_lo|.2f -->0.79<!-- /num -->~<!-- num:scenarios.base.policy.ci.random.true_hi|.2f -->0.83<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.random.ope_per100|.2f -->1.72<!-- /num --> (<!-- num:scenarios.base.policy.ci.random.ope_lo|.1f -->0.6<!-- /num -->~<!-- num:scenarios.base.policy.ci.random.ope_hi|.1f -->2.7<!-- /num -->) |
| 라운드로빈 | <!-- num:scenarios.base.policy.by_k.8.round_robin.true_per100|.2f -->1.50<!-- /num --> (<!-- num:scenarios.base.policy.ci.round_robin.true_lo|.2f -->1.48<!-- /num -->~<!-- num:scenarios.base.policy.ci.round_robin.true_hi|.2f -->1.53<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.round_robin.ope_per100|.2f -->-0.04<!-- /num --> (<!-- num:scenarios.base.policy.ci.round_robin.ope_lo|.1f -->-1.9<!-- /num -->~<!-- num:scenarios.base.policy.ci.round_robin.ope_hi|.1f -->1.8<!-- /num -->) |
| 위험순 | <!-- num:scenarios.base.policy.by_k.8.risk.true_per100|.2f -->2.63<!-- /num --> (<!-- num:scenarios.base.policy.ci.risk.true_lo|.2f -->2.60<!-- /num -->~<!-- num:scenarios.base.policy.ci.risk.true_hi|.2f -->2.67<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.risk.ope_per100|.2f -->2.88<!-- /num --> (<!-- num:scenarios.base.policy.ci.risk.ope_lo|.1f -->1.6<!-- /num -->~<!-- num:scenarios.base.policy.ci.risk.ope_hi|.1f -->4.1<!-- /num -->) |
| 위험순 + 수리 접수 제외 규칙 | <!-- num:scenarios.base.policy.by_k.8.risk_rule.true_per100|.2f -->3.11<!-- /num --> (<!-- num:scenarios.base.policy.ci.risk_rule.true_lo|.2f -->3.08<!-- /num -->~<!-- num:scenarios.base.policy.ci.risk_rule.true_hi|.2f -->3.15<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.risk_rule.ope_per100|.2f -->3.55<!-- /num --> (<!-- num:scenarios.base.policy.ci.risk_rule.ope_lo|.1f -->2.4<!-- /num -->~<!-- num:scenarios.base.policy.ci.risk_rule.ope_hi|.1f -->4.8<!-- /num -->) |
| 효과순 (반응도 모형) | **<!-- num:scenarios.base.policy.by_k.8.responsiveness.true_per100|.2f -->3.42<!-- /num -->** (<!-- num:scenarios.base.policy.ci.responsiveness.true_lo|.2f -->3.38<!-- /num -->~<!-- num:scenarios.base.policy.ci.responsiveness.true_hi|.2f -->3.46<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.responsiveness.ope_per100|.2f -->3.44<!-- /num --> (<!-- num:scenarios.base.policy.ci.responsiveness.ope_lo|.1f -->2.3<!-- /num -->~<!-- num:scenarios.base.policy.ci.responsiveness.ope_hi|.1f -->4.8<!-- /num -->) |
| 효과순 + 수리 접수 제외 규칙 | <!-- num:scenarios.base.policy.by_k.8.responsiveness_rule.true_per100|.2f -->3.45<!-- /num --> (<!-- num:scenarios.base.policy.ci.responsiveness_rule.true_lo|.2f -->3.40<!-- /num -->~<!-- num:scenarios.base.policy.ci.responsiveness_rule.true_hi|.2f -->3.48<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.responsiveness_rule.ope_per100|.2f -->3.45<!-- /num --> (<!-- num:scenarios.base.policy.ci.responsiveness_rule.ope_lo|.1f -->2.3<!-- /num -->~<!-- num:scenarios.base.policy.ci.responsiveness_rule.ope_hi|.1f -->4.7<!-- /num -->) |
| 효과순 (DR-learner) | <!-- num:scenarios.base.policy.by_k.8.dr_gbm.true_per100|.2f -->3.04<!-- /num --> (<!-- num:scenarios.base.policy.ci.dr_gbm.true_lo|.2f -->3.00<!-- /num -->~<!-- num:scenarios.base.policy.ci.dr_gbm.true_hi|.2f -->3.07<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.dr_gbm.ope_per100|.2f -->3.81<!-- /num --> (<!-- num:scenarios.base.policy.ci.dr_gbm.ope_lo|.1f -->2.5<!-- /num -->~<!-- num:scenarios.base.policy.ci.dr_gbm.ope_hi|.1f -->5.2<!-- /num -->) |
| 효과순 (T-learner) | <!-- num:scenarios.base.policy.by_k.8.t_learner.true_per100|.2f -->2.86<!-- /num --> (<!-- num:scenarios.base.policy.ci.t_learner.true_lo|.2f -->2.83<!-- /num -->~<!-- num:scenarios.base.policy.ci.t_learner.true_hi|.2f -->2.90<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.t_learner.ope_per100|.2f -->2.16<!-- /num --> (<!-- num:scenarios.base.policy.ci.t_learner.ope_lo|.1f -->0.6<!-- /num -->~<!-- num:scenarios.base.policy.ci.t_learner.ope_hi|.1f -->3.6<!-- /num -->) |
| 효과순 (DragonNet) | <!-- num:scenarios.base.policy.by_k.8.dragonnet.true_per100|.2f -->2.74<!-- /num --> (<!-- num:scenarios.base.policy.ci.dragonnet.true_lo|.2f -->2.70<!-- /num -->~<!-- num:scenarios.base.policy.ci.dragonnet.true_hi|.2f -->2.77<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.dragonnet.ope_per100|.2f -->2.68<!-- /num --> (<!-- num:scenarios.base.policy.ci.dragonnet.ope_lo|.1f -->1.4<!-- /num -->~<!-- num:scenarios.base.policy.ci.dragonnet.ope_hi|.1f -->4.1<!-- /num -->) |
| 상한 | <!-- num:scenarios.base.policy.by_k.8.ceiling.true_per100|.2f -->3.68<!-- /num --> (<!-- num:scenarios.base.policy.ci.ceiling.true_lo|.2f -->3.64<!-- /num -->~<!-- num:scenarios.base.policy.ci.ceiling.true_hi|.2f -->3.71<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.ceiling.ope_per100|.2f -->3.82<!-- /num --> (<!-- num:scenarios.base.policy.ci.ceiling.ope_lo|.1f -->2.4<!-- /num -->~<!-- num:scenarios.base.policy.ci.ceiling.ope_hi|.1f -->5.1<!-- /num -->) |
| 오라클 | <!-- num:scenarios.base.policy.by_k.8.oracle.true_per100|.2f -->5.54<!-- /num --> (<!-- num:scenarios.base.policy.ci.oracle.true_lo|.2f -->5.51<!-- /num -->~<!-- num:scenarios.base.policy.ci.oracle.true_hi|.2f -->5.59<!-- /num -->) | <!-- num:scenarios.base.policy.by_k.8.oracle.ope_per100|.2f -->4.20<!-- /num --> (<!-- num:scenarios.base.policy.ci.oracle.ope_lo|.1f -->2.4<!-- /num -->~<!-- num:scenarios.base.policy.ci.oracle.ope_hi|.1f -->6.1<!-- /num -->) |

- 효과순(반응도 모형)은 위험순보다 막는 고장이 +<!-- num:summary.base.lift_resp_vs_risk|.0% -->30%<!-- /num --> 많고, 수리 접수 제외 규칙을 붙인 위험순보다도 +<!-- num:summary.base.lift_resp_vs_risk_rule|.0% -->10%<!-- /num --> 앞섭니다. 규칙만 붙여도 위험순에서 +<!-- num:summary.base.lift_risk_rule_vs_risk|.0% -->18%<!-- /num --> 가 나옵니다. 이득의 대부분은 이 단순 규칙이 가져갑니다.
- 학습한 효과순(반응도 모형)은 상한의 <!-- num:summary.base.ceiling_share|.0% -->93%<!-- /num --> 에 이릅니다. 오라클과의 차이는 숨은 손상을 모르는 데서 옵니다.
- OPE 는 효과순의 정답과 <!-- num:summary.base.ope_abs_err_resp|.2f -->0.02<!-- /num --> 차이입니다. 구간은 약 ±1.2 로 넓어서, 정책 사이의 차이(0.3~0.8)를 로그만으로 구별하기에는 이 규모에서도 빠듯합니다.

### ② hunch (함정 세계)

| 정책 | 정답 기준 | 로그만으로 추정 (OPE) |
|---|---:|---:|
| 무작위 | <!-- num:scenarios.hunch.policy.by_k.8.random.true_per100|.2f -->0.69<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.random.true_lo|.2f -->0.67<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.random.true_hi|.2f -->0.71<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.random.ope_per100|.2f -->-1.74<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.random.ope_lo|.1f -->-3.0<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.random.ope_hi|.1f -->-0.2<!-- /num -->) |
| 라운드로빈 | <!-- num:scenarios.hunch.policy.by_k.8.round_robin.true_per100|.2f -->0.97<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.round_robin.true_lo|.2f -->0.95<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.round_robin.true_hi|.2f -->0.99<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.round_robin.ope_per100|.2f -->-2.23<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.round_robin.ope_lo|.1f -->-4.1<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.round_robin.ope_hi|.1f -->-0.3<!-- /num -->) |
| 위험순 | <!-- num:scenarios.hunch.policy.by_k.8.risk.true_per100|.2f -->1.77<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.risk.true_lo|.2f -->1.74<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.risk.true_hi|.2f -->1.80<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.risk.ope_per100|.2f -->-7.13<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.risk.ope_lo|.1f -->-8.1<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.risk.ope_hi|.1f -->-6.0<!-- /num -->) |
| 위험순 + 수리 접수 제외 규칙 | <!-- num:scenarios.hunch.policy.by_k.8.risk_rule.true_per100|.2f -->2.35<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.risk_rule.true_lo|.2f -->2.31<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.risk_rule.true_hi|.2f -->2.38<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.risk_rule.ope_per100|.2f -->-5.51<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.risk_rule.ope_lo|.1f -->-6.7<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.risk_rule.ope_hi|.1f -->-4.4<!-- /num -->) |
| 효과순 (반응도 모형) | <!-- num:scenarios.hunch.policy.by_k.8.responsiveness.true_per100|.2f -->0.03<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.responsiveness.true_lo|.2f -->0.03<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.responsiveness.true_hi|.2f -->0.04<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.responsiveness.ope_per100|.2f -->-0.35<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.responsiveness.ope_lo|.1f -->-1.6<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.responsiveness.ope_hi|.1f -->0.8<!-- /num -->) |
| 효과순 + 수리 접수 제외 규칙 | <!-- num:scenarios.hunch.policy.by_k.8.responsiveness_rule.true_per100|.2f -->0.04<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.responsiveness_rule.true_lo|.2f -->0.03<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.responsiveness_rule.true_hi|.2f -->0.04<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.responsiveness_rule.ope_per100|.2f -->-0.33<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.responsiveness_rule.ope_lo|.1f -->-1.5<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.responsiveness_rule.ope_hi|.1f -->0.8<!-- /num -->) |
| 효과순 (DR-learner) | <!-- num:scenarios.hunch.policy.by_k.8.dr_gbm.true_per100|.2f -->0.27<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.dr_gbm.true_lo|.2f -->0.26<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.dr_gbm.true_hi|.2f -->0.28<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.dr_gbm.ope_per100|.2f -->0.75<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.dr_gbm.ope_lo|.1f -->-0.3<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.dr_gbm.ope_hi|.1f -->1.9<!-- /num -->) |
| 효과순 (T-learner) | <!-- num:scenarios.hunch.policy.by_k.8.t_learner.true_per100|.2f -->1.47<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.t_learner.true_lo|.2f -->1.45<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.t_learner.true_hi|.2f -->1.49<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.t_learner.ope_per100|.2f -->-0.67<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.t_learner.ope_lo|.1f -->-2.2<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.t_learner.ope_hi|.1f -->0.8<!-- /num -->) |
| 효과순 (DragonNet) | <!-- num:scenarios.hunch.policy.by_k.8.dragonnet.true_per100|.2f -->0.63<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.dragonnet.true_lo|.2f -->0.61<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.dragonnet.true_hi|.2f -->0.65<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.dragonnet.ope_per100|.2f -->-0.47<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.dragonnet.ope_lo|.1f -->-2.4<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.dragonnet.ope_hi|.1f -->1.1<!-- /num -->) |
| 상한 | <!-- num:scenarios.hunch.policy.by_k.8.ceiling.true_per100|.2f -->2.83<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.ceiling.true_lo|.2f -->2.80<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.ceiling.true_hi|.2f -->2.88<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.ceiling.ope_per100|.2f -->-3.35<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.ceiling.ope_lo|.1f -->-4.5<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.ceiling.ope_hi|.1f -->-2.2<!-- /num -->) |
| 오라클 | <!-- num:scenarios.hunch.policy.by_k.8.oracle.true_per100|.2f -->4.61<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.oracle.true_lo|.2f -->4.58<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.oracle.true_hi|.2f -->4.66<!-- /num -->) | <!-- num:scenarios.hunch.policy.by_k.8.oracle.ope_per100|.2f -->-10.02<!-- /num --> (<!-- num:scenarios.hunch.policy.ci.oracle.ope_lo|.1f -->-13.3<!-- /num -->~<!-- num:scenarios.hunch.policy.ci.oracle.ope_hi|.1f -->-6.9<!-- /num -->) |

기록에 없는 신호에 오염된 DR 점수(AIPW 에서 나온 점수)로 학습한 효과 모형은 **무작위보다 나쁩니다.** 위험순은 고장 예측이라 점검자의 치우침과 무관해서 영향이 작습니다. OPE 는 부호까지 틀립니다. 이 세계에서는 로그만으로 정책을 고르면 안 됩니다.

### ③ flat (설비마다 반응이 같은 세계)

| 정책 | 정답 기준 | 로그만으로 추정 (OPE) |
|---|---:|---:|
| 무작위 | <!-- num:scenarios.flat.policy.by_k.8.random.true_per100|.2f -->1.98<!-- /num --> (<!-- num:scenarios.flat.policy.ci.random.true_lo|.2f -->1.93<!-- /num -->~<!-- num:scenarios.flat.policy.ci.random.true_hi|.2f -->2.05<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.random.ope_per100|.2f -->2.62<!-- /num --> (<!-- num:scenarios.flat.policy.ci.random.ope_lo|.1f -->1.7<!-- /num -->~<!-- num:scenarios.flat.policy.ci.random.ope_hi|.1f -->3.4<!-- /num -->) |
| 라운드로빈 | <!-- num:scenarios.flat.policy.by_k.8.round_robin.true_per100|.2f -->3.66<!-- /num --> (<!-- num:scenarios.flat.policy.ci.round_robin.true_lo|.2f -->3.60<!-- /num -->~<!-- num:scenarios.flat.policy.ci.round_robin.true_hi|.2f -->3.74<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.round_robin.ope_per100|.2f -->4.00<!-- /num --> (<!-- num:scenarios.flat.policy.ci.round_robin.ope_lo|.1f -->2.9<!-- /num -->~<!-- num:scenarios.flat.policy.ci.round_robin.ope_hi|.1f -->5.0<!-- /num -->) |
| 위험순 | <!-- num:scenarios.flat.policy.by_k.8.risk.true_per100|.2f -->8.06<!-- /num --> (<!-- num:scenarios.flat.policy.ci.risk.true_lo|.2f -->7.95<!-- /num -->~<!-- num:scenarios.flat.policy.ci.risk.true_hi|.2f -->8.21<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.risk.ope_per100|.2f -->7.92<!-- /num --> (<!-- num:scenarios.flat.policy.ci.risk.ope_lo|.1f -->6.9<!-- /num -->~<!-- num:scenarios.flat.policy.ci.risk.ope_hi|.1f -->8.8<!-- /num -->) |
| 위험순 + 수리 접수 제외 규칙 | <!-- num:scenarios.flat.policy.by_k.8.risk_rule.true_per100|.2f -->8.06<!-- /num --> (<!-- num:scenarios.flat.policy.ci.risk_rule.true_lo|.2f -->7.95<!-- /num -->~<!-- num:scenarios.flat.policy.ci.risk_rule.true_hi|.2f -->8.21<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.risk_rule.ope_per100|.2f -->7.92<!-- /num --> (<!-- num:scenarios.flat.policy.ci.risk_rule.ope_lo|.1f -->6.9<!-- /num -->~<!-- num:scenarios.flat.policy.ci.risk_rule.ope_hi|.1f -->8.8<!-- /num -->) |
| 효과순 (반응도 모형) | <!-- num:scenarios.flat.policy.by_k.8.responsiveness.true_per100|.2f -->8.23<!-- /num --> (<!-- num:scenarios.flat.policy.ci.responsiveness.true_lo|.2f -->8.12<!-- /num -->~<!-- num:scenarios.flat.policy.ci.responsiveness.true_hi|.2f -->8.37<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.responsiveness.ope_per100|.2f -->7.98<!-- /num --> (<!-- num:scenarios.flat.policy.ci.responsiveness.ope_lo|.1f -->7.2<!-- /num -->~<!-- num:scenarios.flat.policy.ci.responsiveness.ope_hi|.1f -->8.9<!-- /num -->) |
| 효과순 + 수리 접수 제외 규칙 | <!-- num:scenarios.flat.policy.by_k.8.responsiveness_rule.true_per100|.2f -->8.23<!-- /num --> (<!-- num:scenarios.flat.policy.ci.responsiveness_rule.true_lo|.2f -->8.12<!-- /num -->~<!-- num:scenarios.flat.policy.ci.responsiveness_rule.true_hi|.2f -->8.37<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.responsiveness_rule.ope_per100|.2f -->7.98<!-- /num --> (<!-- num:scenarios.flat.policy.ci.responsiveness_rule.ope_lo|.1f -->7.2<!-- /num -->~<!-- num:scenarios.flat.policy.ci.responsiveness_rule.ope_hi|.1f -->8.9<!-- /num -->) |
| 효과순 (DR-learner) | <!-- num:scenarios.flat.policy.by_k.8.dr_gbm.true_per100|.2f -->8.14<!-- /num --> (<!-- num:scenarios.flat.policy.ci.dr_gbm.true_lo|.2f -->8.03<!-- /num -->~<!-- num:scenarios.flat.policy.ci.dr_gbm.true_hi|.2f -->8.27<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.dr_gbm.ope_per100|.2f -->7.62<!-- /num --> (<!-- num:scenarios.flat.policy.ci.dr_gbm.ope_lo|.1f -->6.7<!-- /num -->~<!-- num:scenarios.flat.policy.ci.dr_gbm.ope_hi|.1f -->8.6<!-- /num -->) |
| 효과순 (T-learner) | <!-- num:scenarios.flat.policy.by_k.8.t_learner.true_per100|.2f -->8.13<!-- /num --> (<!-- num:scenarios.flat.policy.ci.t_learner.true_lo|.2f -->8.02<!-- /num -->~<!-- num:scenarios.flat.policy.ci.t_learner.true_hi|.2f -->8.28<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.t_learner.ope_per100|.2f -->7.96<!-- /num --> (<!-- num:scenarios.flat.policy.ci.t_learner.ope_lo|.1f -->7.1<!-- /num -->~<!-- num:scenarios.flat.policy.ci.t_learner.ope_hi|.1f -->8.9<!-- /num -->) |
| 효과순 (DragonNet) | <!-- num:scenarios.flat.policy.by_k.8.dragonnet.true_per100|.2f -->7.20<!-- /num --> (<!-- num:scenarios.flat.policy.ci.dragonnet.true_lo|.2f -->7.10<!-- /num -->~<!-- num:scenarios.flat.policy.ci.dragonnet.true_hi|.2f -->7.32<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.dragonnet.ope_per100|.2f -->7.19<!-- /num --> (<!-- num:scenarios.flat.policy.ci.dragonnet.ope_lo|.1f -->6.4<!-- /num -->~<!-- num:scenarios.flat.policy.ci.dragonnet.ope_hi|.1f -->8.0<!-- /num -->) |
| 상한 | <!-- num:scenarios.flat.policy.by_k.8.ceiling.true_per100|.2f -->8.71<!-- /num --> (<!-- num:scenarios.flat.policy.ci.ceiling.true_lo|.2f -->8.59<!-- /num -->~<!-- num:scenarios.flat.policy.ci.ceiling.true_hi|.2f -->8.85<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.ceiling.ope_per100|.2f -->9.08<!-- /num --> (<!-- num:scenarios.flat.policy.ci.ceiling.ope_lo|.1f -->8.1<!-- /num -->~<!-- num:scenarios.flat.policy.ci.ceiling.ope_hi|.1f -->9.9<!-- /num -->) |
| 오라클 | <!-- num:scenarios.flat.policy.by_k.8.oracle.true_per100|.2f -->13.45<!-- /num --> (<!-- num:scenarios.flat.policy.ci.oracle.true_lo|.2f -->13.30<!-- /num -->~<!-- num:scenarios.flat.policy.ci.oracle.true_hi|.2f -->13.64<!-- /num -->) | <!-- num:scenarios.flat.policy.by_k.8.oracle.ope_per100|.2f -->12.45<!-- /num --> (<!-- num:scenarios.flat.policy.ci.oracle.ope_lo|.1f -->11.2<!-- /num -->~<!-- num:scenarios.flat.policy.ci.oracle.ope_hi|.1f -->13.8<!-- /num -->) |

설비마다 점검에 반응하는 정도가 같아서 위험순만으로 충분합니다. 효과순(반응도 모형)은 위험순과 견줘 손해도 이득도 거의 없습니다(+<!-- num:summary.flat.lift_resp_vs_risk|.0% -->2%<!-- /num -->).

## 5. 학습곡선

고객사 몇 곳의 로그를 합쳐(풀링) 학습해야, 처음 보는 사이트에서 효과순이 위험순을 이기는지 봅니다.
사이트가 60개인 세계에서 <!-- num:summary.curve.n_test_sites|d -->12<!-- /num -->곳은 끝까지 학습에 쓰지 않고 떼어 두어 신규 고객사 역할을 맡깁니다. 나머지에서 k 곳을 무작위로 골라 학습하고 떼어 둔 사이트에서 평가했습니다. k 마다 2~5번 반복해 평균을 냈습니다. 표준편차를 포함한 그래프와 표는 콘솔의 "점검 대상 고르기" 탭에서 볼 수 있습니다.

표의 숫자는 점검 100번당 막는 고장 수이고, 맨 오른쪽 열만 OPE 추정과 정답의 차이(절대 오차)입니다.

| 학습 사이트 수 | 효과순 | 위험순 | 위험순 + 규칙 | 효과순 + 규칙 | OPE 절대 오차 (효과순) |
|---|---:|---:|---:|---:|---:|
| 4곳 | <!-- num:summary.curve.by_k.k4.responsiveness|.2f -->2.52<!-- /num --> | <!-- num:summary.curve.by_k.k4.risk|.2f -->2.52<!-- /num --> | <!-- num:summary.curve.by_k.k4.risk_rule|.2f -->2.89<!-- /num --> | <!-- num:summary.curve.by_k.k4.responsiveness_rule|.2f -->2.60<!-- /num --> | <!-- num:summary.curve.by_k.k4.ope_err_responsiveness|.2f -->0.75<!-- /num --> |
| 8곳 | <!-- num:summary.curve.by_k.k8.responsiveness|.2f -->2.83<!-- /num --> | <!-- num:summary.curve.by_k.k8.risk|.2f -->2.64<!-- /num --> | <!-- num:summary.curve.by_k.k8.risk_rule|.2f -->3.06<!-- /num --> | <!-- num:summary.curve.by_k.k8.responsiveness_rule|.2f -->2.91<!-- /num --> | <!-- num:summary.curve.by_k.k8.ope_err_responsiveness|.2f -->0.91<!-- /num --> |
| 16곳 | <!-- num:summary.curve.by_k.k16.responsiveness|.2f -->3.28<!-- /num --> | <!-- num:summary.curve.by_k.k16.risk|.2f -->2.70<!-- /num --> | <!-- num:summary.curve.by_k.k16.risk_rule|.2f -->3.15<!-- /num --> | <!-- num:summary.curve.by_k.k16.responsiveness_rule|.2f -->3.30<!-- /num --> | <!-- num:summary.curve.by_k.k16.ope_err_responsiveness|.2f -->0.60<!-- /num --> |
| 32곳 | <!-- num:summary.curve.by_k.k32.responsiveness|.2f -->3.48<!-- /num --> | <!-- num:summary.curve.by_k.k32.risk|.2f -->2.74<!-- /num --> | <!-- num:summary.curve.by_k.k32.risk_rule|.2f -->3.22<!-- /num --> | <!-- num:summary.curve.by_k.k32.responsiveness_rule|.2f -->3.48<!-- /num --> | <!-- num:summary.curve.by_k.k32.ope_err_responsiveness|.2f -->0.38<!-- /num --> |
| 48곳 | <!-- num:summary.curve.by_k.k48.responsiveness|.2f -->3.44<!-- /num --> | <!-- num:summary.curve.by_k.k48.risk|.2f -->2.72<!-- /num --> | <!-- num:summary.curve.by_k.k48.risk_rule|.2f -->3.19<!-- /num --> | <!-- num:summary.curve.by_k.k48.responsiveness_rule|.2f -->3.45<!-- /num --> | <!-- num:summary.curve.by_k.k48.ope_err_responsiveness|.2f -->0.35<!-- /num --> |

- 가장 적게 학습한 <!-- num:summary.curve.k_min|d -->4<!-- /num -->곳에서는 효과순이 <!-- num:summary.curve.resp_min|.2f -->2.52<!-- /num -->, 위험순이 <!-- num:summary.curve.risk_min|.2f -->2.52<!-- /num --> 로 효과순이 앞선 정도는 <!-- num:summary.curve.lift_min|.0% -->0%<!-- /num --> 입니다.
- 가장 많이 학습한 <!-- num:summary.curve.k_max|d -->48<!-- /num -->곳에서는 효과순이 <!-- num:summary.curve.resp_max|.2f -->3.44<!-- /num -->, 위험순이 <!-- num:summary.curve.risk_max|.2f -->2.72<!-- /num --> 로 <!-- num:summary.curve.lift_max|.0% -->26%<!-- /num --> 앞섭니다. 위험순 + 규칙은 <!-- num:summary.curve.rule_max|.2f -->3.19<!-- /num --> 입니다.
- OPE 의 평균 절대 오차는 학습을 가장 적게 했을 때 <!-- num:summary.curve.ope_err_min|.2f -->0.75<!-- /num -->, 가장 많이 했을 때 <!-- num:summary.curve.ope_err_max|.2f -->0.35<!-- /num --> 입니다.

## 6. 무작위 파일럿

무작위 파일럿은 점검 여부를 동전 던지기로 정하는 시험입니다. 점검 대상을 고르는 이유가 결과에 섞이지 않아서, 관측 로그 추정이 맞는지 확인하는 기준이 됩니다. hunch 세계에서 설비의 40% 를 파일럿 설비로 지정하고, 동전 던지기 확률은 평소 점검 비율로 맞췄습니다. 서로 겹치지 않는 4주 구간(창)을 썼습니다.

| | 점검 1회가 막은 고장 |
|---|---:|
| 관측 로그 AIPW (파일럿 설비 제외) | <!-- num:summary.pilot.obs_averted|pp -->-1.8<!-- /num -->%p |
| 무작위 파일럿 평균 차이 | **<!-- num:summary.pilot.pilot_averted|pp -->0.6<!-- /num -->%p** (<!-- num:summary.pilot.pilot_lo|pp -->-0.0<!-- /num -->~<!-- num:summary.pilot.pilot_hi|pp -->1.2<!-- /num -->) |
| 정답 (파일럿 설비) | <!-- num:summary.pilot.truth|pp -->1.0<!-- /num -->%p |

파일럿 설비는 <!-- num:summary.pilot.n_assets|,d -->2,940<!-- /num -->대이고, 서로 독립인 창은 <!-- num:summary.pilot.n_windows|,d -->112,956<!-- /num -->개입니다. 파일럿 추정은 구간이 넓고, 평균적으로 정답에서 한쪽으로 치우치지 않는(무편향) 값이라 관측 추정이 어긋나는지 드러내 줍니다. 관측 추정이 파일럿과 어긋나는지 검사한 결과는 <!-- num:summary.pilot.contradicts|s -->True<!-- /num -->입니다(True면 어긋남).
평균 효과가 작으면 한 고객사의 파일럿만으로는 효과를 가려낼 수 없습니다. 필요한 규모는 파일럿 계획기가 알려 줍니다 (콘솔 "감사" 탭, `POST /v1/pilot/plan`).

## 7. 다시 돌려 보기

아래 두 명령으로 이 문서의 숫자를 다시 만들고 검사합니다.

```bash
make pipeline     # 시나리오 3종 → 파일럿 → 몬테카를로 → 스윕 → 학습곡선 → 요약 → 정적 데모 → 숫자 채우기
make check-numbers
```
