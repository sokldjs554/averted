# averted

**점검을 더 하면 고장이 줄까? 로그만 보면 거꾸로 나옵니다.**

점검한 설비가 안 한 설비보다 더 고장나 보이는 것은, 현장이 위험한 설비를 골라서 점검하기 때문입니다.
이 저장소는 그 착시를 걷어내 **점검 한 번이 막은 고장**을 추정하고, 한정된 점검 인력을 위험이 아니라 **효과** 기준으로 배분합니다.
그리고 그 추정을 **언제 믿으면 안 되는지**까지 함께 알려 줍니다.

**라이브 데모**: <https://sokldjs554.github.io/averted/> (백엔드 없이 동작하는 정적 데모)

![demo](docs/images/demo.gif)

> 모든 데이터는 **합성(SYNTHETIC)** 입니다. 점검의 효과를 메커니즘으로 만든 시뮬레이터가 정답을 알기 때문에, 숫자는 "현실의 효과"가 아니라 **추정 방법이 정답을 맞히는가**에 대한 검증입니다.

## 세 줄 요약

1. **로그만 보면** 점검한 주의 고장률이 더 높습니다 (<!-- num:summary.base.naive_gap|pp -->4.9<!-- /num -->%p). "점검이 해롭다"는 결론이 나옵니다.
2. **위험한 설비를 골라 점검한 것을 걷어내면** 점검 1회가 고장을 <!-- num:summary.base.aipw_averted|pp -->0.7<!-- /num -->%p 막습니다 (시뮬레이터가 아는 정답 <!-- num:summary.base.truth_averted|pp -->0.8<!-- /num -->%p).
3. **그래서** 같은 점검 횟수로 위험순보다 효과순이 <!-- num:summary.base.lift_resp_vs_risk|.0% -->30%<!-- /num --> 더 많은 고장을 막습니다.

## 틀리는 경우도 보여 줍니다

이 프로젝트는 "맞는다"보다 **"언제 틀리는지 안다"** 를 주장합니다. 데모 상단의 세계 선택에서 ② 를 고르면 직접 볼 수 있습니다.

- **기록에 없는 신호로 점검하면 보정해도 틀립니다.** 정답은 +<!-- num:summary.hunch.truth_averted|pp -->0.7<!-- /num -->%p 인데 추정은 **<!-- num:summary.hunch.aipw_averted|pp -->-2.0<!-- /num -->%p** — 부호까지 반대입니다. 로그 감사가 이것을 **빨강**으로 알립니다. 다만 약한 경우는 놓칩니다 ([docs/failures.md](docs/failures.md)).
- **감사가 빨강이면 학습한 정책을 쓰면 안 됩니다.** 오염된 신호로 배운 효과순은 무작위보다도 나쁩니다.
- **위험순이 충분한 세계도 있습니다.** 설비마다 반응이 같으면 효과순은 위험순과 같고, 이 도구는 그것도 알려 줍니다.
- **고객사 데이터가 적으면 못 배웁니다.** 학습에 쓴 사이트가 적으면 단순 규칙(수리 접수된 설비 제외)이 이깁니다.

![trust](docs/images/console-trust-hunch.png)

## 직접 구현한 것 (라이브러리 호출이 아님)

| 무엇 | 어디 | 어떻게 검증했나 |
|---|---|---|
| 두 세계 시뮬레이터 + 정답 효과 | `sim/` | 직접 시뮬레이션 빈도와 일치 (테스트) |
| 교차적합 AIPW(이중 강건) + 설비 군집 구간 | `causal/estimators.py` | 정답 복원 · **econml 과 일치**(테스트) · 몬테카를로 포함률 <!-- num:summary.coverage.base.aipw|.0% -->95%<!-- /num --> |
| 효과 학습 (반응도 모형 · DragonNet/PyTorch) | `causal/` | 같은 기준(점검 100번당 막는 고장)으로 규칙과 비교 |
| 로그 감사: 겹침·균형·음성 대조·민감도·판정 | `audit.py` | 숨은 교란 강도를 바꿔 가며 경고율 측정 |
| 무작위 파일럿 규모 계획기 | `causal/pilot.py` + 브라우저 포트 | 파이썬↔JS 일치 테스트 |

내 로그로 돌리려면 CSV 한 장을 `POST /v1/audit` 에 올리면 됩니다 ([실제 로그에 적용하기](docs/real-data.md)).

## 실행

```bash
make install     # 개발 의존성
make test        # 단위 테스트
make serve       # http://localhost:8000/console/   (산출물은 artifacts/ 에 커밋돼 있다)
docker compose up --build
```

## 문서

[설계](docs/design.md) · [시뮬레이터](docs/simulator.md) · [평가](docs/evaluation.md) · **[실패와 한계](docs/failures.md)** · [실제 로그에 적용하기](docs/real-data.md) · [선행 연구](docs/prior-work.md) · [만든 방식과 AI 사용 공개](docs/how-this-was-built.md)

## 공고의 요구 기술이 저장소 어디에 있나

| 공고 | 저장소 |
|---|---|
| Python 데이터 전처리·분석 (Pandas, NumPy) | `sim/` 생성기, `causal/data.py` (`LogSpec` 으로 실제 로그 열 매핑) |
| 회귀·분류 | 처치 확률(분류) · 결과 확률(분류) · 반응도(최소제곱) |
| 딥러닝 설계·성능 개선 (PyTorch) | `causal/dragonnet.py` — 트리·규칙과 같은 기준으로 비교하고 한계를 공개 |
| 분석 결과를 API/웹으로 (FastAPI) | `api/` (조회·감사 업로드·파일럿 계획기), `console/` |
| 데이터 시각화 | 신뢰구간·산점도·정책 비교 (접근성 팔레트, 표 보기, 다크 모드) |
| 클라우드 (AWS, GCP) | `Dockerfile`, `deploy/gcp`, `deploy/aws` |
| 실제 서비스 운영 | `/health`·`/metrics`, 업로드 한도, CI(린트·테스트·숫자 일치·이미지 빌드) |
| 실증 프로젝트·고객 맞춤형 모델 | 고객 로그에 먼저 돌리는 감사, 파일럿 계획기, 고객사 풀링 학습곡선 |

## 범위

실데이터 없음 · 효과 크기는 시뮬레이터의 가정이며 현실의 값이 아님 · 콘솔은 인증 없는 데모 · 점검 주기 변경 같은 프로그램의 효과는 추정 대상이 아님.
