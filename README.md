# averted

설비 점검이 고장을 얼마나 막았는지 점검 로그로 추정하고, 점검할 설비를 고르는 데 쓰는 분석 서비스.

점검 로그를 그대로 비교하면 점검한 설비가 점검하지 않은 설비보다 고장이 더 많다. 현장에서 위험한 설비를 골라 점검하기 때문에 생기는 착시다. 이 프로젝트는 그 영향을 빼고 점검 한 번의 효과를 계산한다. 추정을 믿어도 되는지 검사하는 기능도 있다.

## 데모

<https://sokldjs554.github.io/averted/> (서버 없이 열리는 정적 데모)

![demo](docs/images/demo.gif)

모든 데이터는 합성(SYNTHETIC)이다. 시뮬레이터가 점검의 실제 효과(정답)를 알고 있어서, 아래 숫자는 추정 방법이 정답을 맞히는지 확인한 결과다. 현실의 효과 크기는 아니다.

## 결과 요약

- 로그만 보면 점검한 설비의 4주 내 고장률은 <!-- num:scenarios.base.audit.data.outcome_rate_treated|.0% -->12%<!-- /num -->, 점검하지 않은 설비는 <!-- num:scenarios.base.audit.data.outcome_rate_control|.0% -->7%<!-- /num -->. 점검이 해로워 보임
- 위험한 설비를 골라 점검한 영향을 빼면 점검 100번에 고장이 약 <!-- num:summary.base.aipw_averted|pp -->0.7<!-- /num -->건 감소. 시뮬레이터가 아는 정답은 <!-- num:summary.base.truth_averted|pp -->0.8<!-- /num -->건
- 같은 횟수로 점검할 때 효과가 큰 설비부터 고르면, 위험한 설비부터 고를 때보다 고장을 <!-- num:summary.base.lift_resp_vs_risk|.0% -->30%<!-- /num --> 더 막음

## 틀리는 경우

추정이 틀리는 경우를 따로 시험했다. 데모 위쪽의 세계 선택에서 ②를 고르면 볼 수 있다.

- 점검하는 사람이 기록에 없는 신호(소음, 열 같은 현장 감각)로 대상을 고르면 보정해도 틀린다. 실제로는 점검 100번에 <!-- num:summary.hunch.truth_averted|pp -->0.7<!-- /num -->건을 막는데 추정은 <!-- num:summary.hunch.aipw_averted|pp -->-2.0<!-- /num -->건(오히려 늘어남)으로 나온다. 로그 감사가 이 경우를 빨강으로 표시한다. 약한 경우는 감사도 놓친다. 자세한 내용은 [docs/failures.md](docs/failures.md)
- 감사가 빨강일 때 학습한 점검 순서는 무작위보다도 나쁘다
- 설비마다 점검 효과가 같으면 효과순과 위험순에 차이가 없다. 이때는 위험순으로 충분하다고 알려 준다
- 학습에 쓴 고객사 데이터가 적으면 단순한 규칙(수리가 접수된 설비는 제외)이 학습한 모형보다 낫다

![trust](docs/images/console-trust-hunch.png)

## 직접 구현한 것

| 구현 | 위치 | 확인 방법 |
|---|---|---|
| 시뮬레이터 (점검한 세계와 안 한 세계를 같은 난수로 돌려 정답 생성) | `sim/` | 직접 돌려 센 결과와 일치하는지 테스트 |
| 점검 효과 추정기 (AIPW) | `causal/estimators.py` | 정답 복원 테스트, econml 결과와 일치 테스트, 95% 구간 포함률 <!-- num:summary.coverage.base.aipw|.0% -->95%<!-- /num --> |
| 설비별 효과 학습 (반응도 모형, DragonNet) | `causal/` | 점검 100번당 막는 고장으로 단순한 규칙과 비교 |
| 로그 감사 | `audit.py` | 기록에 없는 신호의 강도를 바꿔 가며 경고율 측정 |
| 무작위 파일럿 계획기 | `causal/pilot.py`, 브라우저용 포트 | 파이썬과 JS 결과 일치 테스트 |

AIPW는 점검 확률 모형과 고장 모형 중 하나만 맞아도 결과가 맞는 방법이다.
내 로그에 쓰려면 CSV 한 장을 `POST /v1/audit`에 올리면 된다. 자세한 방법은 [실제 로그에 적용하기](docs/real-data.md).

## 실행 방법

```bash
make install     # 개발용 패키지 설치
make test        # 테스트
make serve       # http://localhost:8000/console/  (실험 결과는 artifacts/ 에 들어 있음)
docker compose up --build
```

## 문서

[설계](docs/design.md) · [시뮬레이터](docs/simulator.md) · [평가](docs/evaluation.md) · [실패와 한계](docs/failures.md) · [실제 로그에 적용하기](docs/real-data.md) · [선행 연구](docs/prior-work.md) · [만든 방식과 AI 사용 공개](docs/how-this-was-built.md)

## 채용 공고와 대응

| 공고 | 저장소 |
|---|---|
| Python 데이터 전처리·분석 (Pandas, NumPy) | `sim/` 생성기, `causal/data.py` (`LogSpec`으로 실제 로그의 열 이름을 맞춤) |
| 회귀·분류 | 점검 확률(분류), 고장 확률(분류), 반응도(최소제곱) |
| 딥러닝 설계·성능 개선 (PyTorch) | `causal/dragonnet.py`. 트리·규칙과 같은 기준으로 비교하고 한계도 기록 |
| 분석 결과를 API/웹으로 (FastAPI) | `api/` (결과 조회, 감사 업로드, 파일럿 계획기), `console/` |
| 데이터 시각화 | 신뢰구간, 산점도, 정책 비교 (색약 고려 팔레트, 표 보기, 다크 모드) |
| 클라우드 (AWS, GCP) | `Dockerfile`, `deploy/gcp`, `deploy/aws` |
| 실제 서비스 운영 | `/health`, `/metrics`, 업로드 한도, CI(린트, 테스트, 숫자 일치, 이미지 빌드) |
| 실증 프로젝트, 고객 맞춤형 모델 | 고객 로그에 먼저 돌리는 감사, 파일럿 계획기, 고객사 데이터 수에 따른 성능 변화 |

## 범위와 한계

- 실제 데이터 없음
- 효과의 크기는 시뮬레이터의 가정
- 콘솔은 인증이 없는 데모
- 점검 주기를 바꾸는 것 같은 프로그램 전체의 효과는 추정하지 않음
