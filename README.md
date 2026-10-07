# averted

**점검을 더 하면 고장이 줄까? 로그만 보면 거꾸로 나옵니다.**
점검한 설비가 안 한 설비보다 더 고장나 보이는 것은, 현장이 위험한 설비를 골라서 점검하기 때문입니다. 이 저장소는 그 착시를 걷어내 **점검 한 번이 막은 고장**을 추정하고,
한정된 점검 인력을 위험이 아니라 **효과** 기준으로 배분합니다. 그리고 그 추정을 **언제 믿으면 안 되는지**를 함께 알려 줍니다.

> 모든 데이터는 **합성(SYNTHETIC)** 입니다. 점검의 효과를 메커니즘으로 만든 시뮬레이터가 정답을 알기 때문에, 아래 숫자는 "현실의 효과"가 아니라 **추정 방법이 정답을 맞히는가**에 대한 검증입니다.

**라이브 데모**: <https://sokldjs554.github.io/averted/> (백엔드 없이 동작하는 정적 데모)

![demo](docs/images/demo.gif)

## 숫자 세 개

합성 세계 <!-- num:summary.base.n_sites -->60<!-- /num -->개 사이트 · 설비 <!-- num:summary.base.n_assets|,d -->7,444<!-- /num -->대 · 3년 · 점검 기록 <!-- num:summary.base.rows|,d -->1,161,264<!-- /num -->행.

| ① 로그만 보면 | ② 교란을 보정하면 | ③ 점검 100번당 막는 고장 |
|---|---|---|
| 점검한 주의 고장률이 안 한 주보다 **<!-- num:summary.base.naive_gap|pp -->4.9<!-- /num -->%p 높다** ("점검이 해롭다") | 점검 1회가 **<!-- num:summary.base.aipw_averted|pp -->0.7<!-- /num -->%p** 막는다<br>(95% 구간 <!-- num:summary.base.aipw_lo|pp -->0.5<!-- /num -->~<!-- num:summary.base.aipw_hi|pp -->0.9<!-- /num -->, **정답 <!-- num:summary.base.truth_averted|pp -->0.8<!-- /num -->**) | 위험순 <!-- num:summary.base.per100.risk|.2f -->2.63<!-- /num --> → **효과순 <!-- num:summary.base.per100.responsiveness|.2f -->3.42<!-- /num -->** (+<!-- num:summary.base.lift_resp_vs_risk|.0% -->30%<!-- /num -->)<br>무작위 <!-- num:summary.base.per100.random|.2f -->0.81<!-- /num --> · 상한 <!-- num:summary.base.per100.ceiling|.2f -->3.68<!-- /num --> |

①→② 는 같은 로그를 이중 강건 추정(AIPW)으로 보정한 결과이고, ③ 은 사이트·주마다 8곳을 고를 때 막는 고장의 기댓값입니다(정답은 시뮬레이터가 압니다).

## 틀리는 경우 — 먼저 읽으세요

이 프로젝트는 "맞는다"보다 **"언제 틀리는지 안다"** 를 주장합니다. 데모의 세계 ②③ 이 그 증거입니다.

- **숨은 교란.** 점검자가 기록에 없는 신호(소음·열)로 점검 대상을 정하면 보정해도 틀립니다. 같은 세계에서 점검 1회 효과가 정답 <!-- num:summary.hunch.truth_averted|pp -->0.7<!-- /num -->%p 인데 추정은 **<!-- num:summary.hunch.aipw_averted|pp -->-2.0<!-- /num -->%p** (부호까지 반대)입니다.
  로그 감사는 이것을 **빨강**으로 잡습니다 (점검 이전 고장에 '효과'가 나오는 음성 대조, z=<!-- num:summary.hunch.nc_z|.1f -->-13.3<!-- /num -->). 다만 **약한 숨은 교란은 놓칩니다** — [docs/failures.md](docs/failures.md).
- **감사가 빨강이면 학습한 정책을 쓰면 안 됩니다.** 오염된 신호로 학습한 효과순은 점검 100번당 <!-- num:summary.hunch.per100.responsiveness|.2f -->0.03<!-- /num --> 으로 무작위(<!-- num:summary.hunch.per100.random|.2f -->0.69<!-- /num -->)보다 나쁩니다. 위험순(<!-- num:summary.hunch.per100.risk|.2f -->1.77<!-- /num -->)이 더 안전합니다.
- **위험순이 충분한 세계도 있습니다.** 설비별 반응 차이가 없으면 효과순은 위험순과 사실상 같습니다(<!-- num:summary.flat.per100.responsiveness|.2f -->8.23<!-- /num --> vs <!-- num:summary.flat.per100.risk|.2f -->8.06<!-- /num -->). 이 도구는 그것도 알려 줍니다.
- **데이터가 적으면 못 배웁니다.** 처음 보는 사이트에서, 학습에 쓴 고객사가 <!-- num:summary.curve.k_min|d -->4<!-- /num -->곳이면 효과순은 위험순과 같고(+<!-- num:summary.curve.lift_min|.0% -->0%<!-- /num -->) 단순 규칙(수리 접수 제외, <!-- num:summary.curve.by_k.k4.risk_rule|.2f -->2.89<!-- /num -->)보다 못합니다 (<!-- num:summary.curve.by_k.k4.responsiveness|.2f -->2.52<!-- /num -->).
  <!-- num:summary.curve.by_k.k16.responsiveness|.2f -->3.28<!-- /num --> vs 규칙 <!-- num:summary.curve.by_k.k16.risk_rule|.2f -->3.15<!-- /num --> 로 **16곳부터 규칙도 이기고**, <!-- num:summary.curve.k_max|d -->48<!-- /num -->곳에서 위험순 대비 +<!-- num:summary.curve.lift_max|.0% -->26%<!-- /num --> 입니다. 고객사를 풀링하는 것이 이 접근의 전제입니다.

![trust](docs/images/console-trust-hunch.png)

## 왜 이 주제인가

예지보전("어느 설비가 위험한가")은 흔하고, 예측만으로는 "그래서 어디에 점검을 쓸까"에 답하지 못합니다. 위험한 설비 중에는 **이미 수리 접수가 된 설비**, **순찰로는 결함이 안 보이는 설비**, **교체해야 하는 설비**가 섞여 있어서
위험 순으로 점검하면 효과가 없는 곳에 인력을 씁니다. 시설관리 솔루션이 내세우는 "장애를 예측하고 최적의 운영 시나리오를 제시"에서 **두 번째 절반**이 이 저장소입니다. (조사와 판단: [docs/how-this-was-built.md](docs/how-this-was-built.md))
선행 연구는 해외에 있습니다([docs/prior-work.md](docs/prior-work.md)) — 이 저장소는 검증된 설계를 시설점검에 적용하고, 실제 로그에서 쓸 수 있게 만든 것입니다.

## 직접 구현한 것 (라이브러리 호출이 아님)

| 무엇 | 어디 | 어떻게 검증했나 |
|---|---|---|
| 두 세계 시뮬레이터 + 정답 효과(공통 난수·Rao–Blackwell) | `sim/` | 직접 시뮬레이션 빈도와 일치 (테스트) |
| 교차적합 AIPW + 설비 군집 강건 신뢰구간, DR 점수 | `causal/estimators.py` | 정답 복원 · **econml 과 일치**(테스트) · 몬테카를로 포함률 <!-- num:summary.coverage.base.aipw|.0% -->95%<!-- /num --> |
| 반응도 모형 (효과 = 위험 × 반응도, 군집 부트스트랩 구간) | `causal/responsiveness.py` | 학습곡선, 기준선 대비 |
| DragonNet (PyTorch) | `causal/dragonnet.py` | 같은 기준(점검 100번당)으로 비교 |
| 로그 감사: 겹침·균형·음성 대조·민감도·판정 | `audit.py`, `causal/diagnostics.py` | 숨은 교란 스윕으로 경고율 측정 |
| 무작위 파일럿 계획기 (겹치지 않는 창·설계 효과) | `causal/pilot.py` + 브라우저 포트 | 파이썬↔JS 일치 테스트 |

## 구성

```
src/averted/
  sim/        두 세계 시뮬레이터 — 손상·점검·수리·민원·점검 규칙, 정답(포크)
  causal/     추정기·진단·민감도·반응도 모형·DragonNet·정책 가치(OPE)·파일럿
  eval/       시나리오 평가·학습곡선·몬테카를로·숨은 교란 스윕·파일럿 데모
  api/        FastAPI — 산출물 조회, POST /v1/audit (내 로그 감사), POST /v1/pilot/plan
  console/    바닐라 JS 콘솔 (착시 · 누구에게 · 이번 주 점검표 · 믿어도 되나 · 내 로그로)
tests/        시뮬레이터 불변식 · 추정기(econml 일치) · API · JS 포트 일치
deploy/       Cloud Run · App Runner
```

## 실행

```bash
make install            # 개발 의존성 (CPU torch, econml 교차 검증 포함)
make test               # 단위 테스트
make serve              # http://localhost:8000/console/   (산출물은 artifacts/ 에 커밋돼 있다)
make pipeline           # 전체 재실험 → 정적 데모 → 숫자 채우기 (약 2시간, 4 vCPU)

curl -F file=@my_log.csv 'http://localhost:8000/v1/audit'      # 내 로그 감사 (스키마: GET /v1/schema)
docker compose up --build
```

## 문서

[설계](docs/design.md) · [시뮬레이터](docs/simulator.md) · [평가](docs/evaluation.md) · **[실패와 한계](docs/failures.md)** · [실제 로그에 적용하기](docs/real-data.md) · [선행 연구](docs/prior-work.md) · [만든 방식과 AI 사용 공개](docs/how-this-was-built.md)

## 공고의 요구 기술이 저장소 어디에 있나

| 공고 | 저장소 |
|---|---|
| Python 데이터 전처리·분석 (Pandas, NumPy) | `sim/` 생성기, `causal/data.py` (`LogSpec` 으로 실제 로그 열 매핑) |
| 회귀·분류 | 교란 모형(처치 확률 분류 · 결과 확률 분류 · 반응도 최소제곱) |
| 딥러닝 설계·성능 개선 (PyTorch) | `causal/dragonnet.py` — 같은 기준으로 트리·구조 모형과 비교하고 한계를 공개 |
| 분석 결과를 API/웹으로 (FastAPI) | `api/` — 조회·감사 업로드·파일럿 계획기, `console/` |
| 데이터 시각화 | 신뢰구간 점·산점도·정책 비교 (접근성 팔레트, 표 보기, 다크 모드) |
| 클라우드 (AWS, GCP) | `Dockerfile`, `deploy/gcp`, `deploy/aws` |
| 실제 서비스 운영 | `/health`·`/metrics`, 업로드 한도, CI(린트·테스트·숫자 일치·이미지 빌드) |
| 실증 프로젝트·고객 맞춤형 모델 | 로그 감사(고객 로그에 먼저 돌린다), 무작위 파일럿 계획기, 고객사 풀링 학습곡선 |

## 범위

실데이터 없음 · 효과 크기는 시뮬레이터의 가정이며 현실의 값이 아님 · 콘솔은 인증 없는 데모 · 점검 프로그램(주기 변경)의 효과는 추정 대상이 아님.
