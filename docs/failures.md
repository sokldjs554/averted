# 실패와 한계 — 먼저 읽으세요

이 저장소의 주장은 "맞는다"가 아니라 **"언제 틀리는지 안다"** 다. 틀리는 경우와 못 잡는 경우를 숫자로 적는다 (숫자는 `docs/evaluation.md` 와 같은 산출물에서 채워진다).

## 1. 숨은 교란은 보정으로 없앨 수 없고, 감사도 약한 것은 놓친다

점검자가 기록에 없는 신호(소음·열 같은 촉)로 점검 대상을 정하면 어떤 보정 추정기도 틀린다. 스윕(γ = 그 신호의 강도):

| γ | 정답 | AIPW | 감사의 음성 대조 경고율 |
|---|---:|---:|---:|
| 0.3 | <!-- num:summary.hunch_sweep.g0_3.truth|pp -->0.8<!-- /num -->%p | <!-- num:summary.hunch_sweep.g0_3.aipw|pp -->-0.5<!-- /num -->%p | **<!-- num:summary.hunch_sweep.g0_3.nc_flag_rate|.0% -->0%<!-- /num -->** |
| 0.6 | <!-- num:summary.hunch_sweep.g0_6.truth|pp -->0.8<!-- /num -->%p | <!-- num:summary.hunch_sweep.g0_6.aipw|pp -->-1.3<!-- /num -->%p | <!-- num:summary.hunch_sweep.g0_6.nc_flag_rate|.0% -->60%<!-- /num --> |
| 1.0 | <!-- num:summary.hunch_sweep.g1_0.truth|pp -->0.7<!-- /num -->%p | <!-- num:summary.hunch_sweep.g1_0.aipw|pp -->-2.7<!-- /num -->%p | <!-- num:summary.hunch_sweep.g1_0.nc_flag_rate|.0% -->100%<!-- /num --> |

- γ=0.3 에서는 추정이 정답과 **부호까지 반대**인데 경고가 울리지 않는다. 음성 대조(점검 이전 고장에 '효과'가 나오는가)는 교란이 어느 정도 강해야 드러난다.
- 교란이 전혀 없는 세계(γ=0)에서도 경고율이 <!-- num:summary.hunch_sweep.g0_0.nc_flag_rate|.0% -->20%<!-- /num -->(5 시드)로 0 이 아니다. 오경보가 있다.
- 대응: 신호등과 별개로 **가정 의존도**(관측 변수 하나를 뺄 때 추정이 얼마나 움직이는가)를 표시한다. 그 변수만큼 강한 숨은 교란이 가능하면 결론이 뒤집힐 수 있다. 중요한 결정은 무작위 파일럿으로 확인한다.

## 2. 감사가 빨강일 때 학습한 정책은 무작위보다 나쁘다

hunch 세계(감사: <!-- num:summary.hunch.verdict|s -->red<!-- /num -->)에서 학습한 효과순은 점검 100번당 <!-- num:summary.hunch.per100.responsiveness|.2f -->0.03<!-- /num -->, 무작위 <!-- num:summary.hunch.per100.random|.2f -->0.69<!-- /num -->, 위험순 <!-- num:summary.hunch.per100.risk|.2f -->1.77<!-- /num --> 이다.
오염된 DR 점수가 효과 모형을 거꾸로 학습시킨다. 로그만으로 정책 가치를 추정하는 OPE 도 이 세계에서는 부호가 틀린다. **빨강이면 효과 추정을 정책에 쓰지 않는다.**

## 3. 데이터가 적으면 효과 이질성을 못 배운다

처음 보는 사이트에서의 정책 가치 (점검 100번당, 12개 사이트를 떼어 두고 평가):

| 학습에 쓴 사이트 수 | 효과순 (반응도) | 위험순 | 위험순 + 규칙 |
|---|---:|---:|---:|
| 4곳 | <!-- num:summary.curve.by_k.k4.responsiveness|.2f -->2.52<!-- /num --> | <!-- num:summary.curve.by_k.k4.risk|.2f -->2.52<!-- /num --> | <!-- num:summary.curve.by_k.k4.risk_rule|.2f -->2.89<!-- /num --> |
| 8곳 | <!-- num:summary.curve.by_k.k8.responsiveness|.2f -->2.83<!-- /num --> | <!-- num:summary.curve.by_k.k8.risk|.2f -->2.64<!-- /num --> | <!-- num:summary.curve.by_k.k8.risk_rule|.2f -->3.06<!-- /num --> |
| 16곳 | <!-- num:summary.curve.by_k.k16.responsiveness|.2f -->3.28<!-- /num --> | <!-- num:summary.curve.by_k.k16.risk|.2f -->2.70<!-- /num --> | <!-- num:summary.curve.by_k.k16.risk_rule|.2f -->3.15<!-- /num --> |
| 32곳 | <!-- num:summary.curve.by_k.k32.responsiveness|.2f -->3.48<!-- /num --> | <!-- num:summary.curve.by_k.k32.risk|.2f -->2.74<!-- /num --> | <!-- num:summary.curve.by_k.k32.risk_rule|.2f -->3.22<!-- /num --> |
| 48곳 | <!-- num:summary.curve.by_k.k48.responsiveness|.2f -->3.44<!-- /num --> | <!-- num:summary.curve.by_k.k48.risk|.2f -->2.72<!-- /num --> | <!-- num:summary.curve.by_k.k48.risk_rule|.2f -->3.19<!-- /num --> |

- **4~8곳에서는 단순 규칙이 학습한 효과순보다 낫다.** 16곳부터 학습한 효과순이 규칙까지 이긴다.
- 구조 없는 학습기는 더 늦게, 덜 따라온다. 60개 사이트(본 평가)에서 위험순 <!-- num:summary.base.per100.risk|.2f -->2.63<!-- /num --> 대비 DR-learner <!-- num:summary.base.per100.dr_gbm|.2f -->3.04<!-- /num -->, T-learner <!-- num:summary.base.per100.t_learner|.2f -->2.86<!-- /num -->, DragonNet <!-- num:summary.base.per100.dragonnet|.2f -->2.74<!-- /num -->, 구조를 준 반응도 모형 <!-- num:summary.base.per100.responsiveness|.2f -->3.42<!-- /num -->. 사이트가 적은 초기 실험(8~24곳)에서는 이 학습기들이 위험순을 못 이겼다.
- 이유는 신호 대 잡음비다. 처치율 약 9%, 4주 내 고장률 약 7% 라서 설비별 효과 추정의 잡음이 효과 크기보다 크다. CATE 추정기 16종을 벤치마크한 연구(Yu 외, ICLR 2025)도 비슷한 결과를 보고했다.
- 반응도 모형은 "효과 = 위험 × 반응도" 구조로 모수를 20개 안팎으로 줄여 이 문제를 완화하지만, 그래도 고객사를 풀링해야 이긴다.

## 4. 로그만으로 정책을 비교하는 OPE 는 이 규모에서도 빠듯하다

base 세계의 OPE 95% 구간은 약 ±1.2(점검 100번당)인데 정책 간 차이는 0.3~0.8 이다. 평균 절대 오차는 학습 <!-- num:summary.curve.k_min|d -->4<!-- /num -->곳에서 <!-- num:summary.curve.ope_err_min|.2f -->0.75<!-- /num -->, <!-- num:summary.curve.k_max|d -->48<!-- /num -->곳에서 <!-- num:summary.curve.ope_err_max|.2f -->0.35<!-- /num -->.
실제 로그에서 정책을 고를 때는 OPE 의 구간을 함께 보고, 구간이 겹치면 무작위 파일럿으로 가린다.

## 5. 단순 규칙이 이득의 상당 부분을 가져간다

"이미 수리 접수된 설비는 순찰에서 뺀다"는 규칙만으로 위험순이 +<!-- num:summary.base.lift_risk_rule_vs_risk|.0% -->18%<!-- /num --> 개선된다(학습 없음). 60개 사이트에서 학습한 효과순은 그 위에서 +<!-- num:summary.base.lift_resp_vs_risk_rule|.0% -->10%<!-- /num --> 를 더하고, 학습 4곳에서는 규칙이 더 낫다 (위 표).
도메인 규칙을 먼저 쓰고, 학습은 데이터가 쌓인 뒤에 더한다.

## 6. 설비 종류별 효과는 대부분 "정보 부족"

종류별 AIPW 효과 구간이 0 을 포함하거나 처치 표본이 150 미만이면 `informative=false` 로 표시한다(콘솔 감사 결과의 부분집단). 개별 설비 수준의 효과 구간은 군집 부트스트랩이고 외삽이면 '판단 보류'로 표시한다.

## 7. 효과가 작으면 파일럿이 크다

평균 효과 <!-- num:summary.base.aipw_averted|pp -->0.7<!-- /num -->%p 수준을 80% 검정력으로 검출하려면 한 고객사(설비 수백 대)의 파일럿으로는 부족하다. 설비 내 상관 때문에 기간을 늘려도 검정력이 포화되고, 필요한 설비 수가 수천 대로 올라간다 (`POST /v1/pilot/plan`).
효과가 큰 층(민원이 접수된 설비 등)만 대상으로 하면 규모가 크게 준다.

## 8. 식별이 안 되는 로그가 있다

점검의 대부분이 달력으로 정해진 사이트(법정 점검 위주)에서는 처치 변이가 없다. 법정 기한 행은 분석에서 빼고(`rows_excluded_due`), 남은 행이 부족하면 "겹침" 경고가 나온다. 그때의 답은 추정이 아니라 파일럿이다.

## 9. 시뮬레이터는 제 가정의 거울이다

- 위험순과 효과순의 격차는 세 메커니즘(종류별 발견율·수리 접수 지연·수명 한계)을 넣었기 때문에 생긴다. 발견이 아니다. 끈 세계(flat)에서는 격차가 <!-- num:summary.flat.lift_resp_vs_risk|.0% -->2%<!-- /num --> 다.
- 효과 크기(점검 1회 <!-- num:summary.base.truth_averted|pp -->0.8<!-- /num -->%p)는 "그럴듯한 값"이지 실측이 아니다.
- 반응도 모형의 구조는 시뮬레이터의 메커니즘과 잘 맞는다. 현실에서 구조가 틀리면 DR-learner·DragonNet 과 같은 기준으로 비교해 판단한다(같은 코드가 점수를 낸다).

## 10. 추정 대상의 한계

- "이번 주 한 번 더 점검"의 효과다. 점검 **주기를 바꾸는 프로그램**의 효과는 아니다.
- 점검을 한 가지 행위로 본다. 깊이·점검자 숙련도 차이는 모른다.
- 설비 간 간섭(한 설비의 점검이 다른 설비의 고장에 영향)은 없다고 가정한다.
- 결과는 4주 내 비계획 고장 여부다. 고장의 심각도·정지 시간은 다루지 않는다.
