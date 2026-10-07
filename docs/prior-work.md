# 선행 연구

이 저장소의 방법은 이미 검증된 설계를 설비 점검에 맞춰 쓴 것입니다.

| 주제 | 출처 | 이 저장소에서의 쓰임 |
|---|---|---|
| 정비의 개별 효과를 관측 데이터에서 인과 기계학습(인과 ML)으로 추정하고, 정비 빈도를 최적화 | Vanderschueren 외, "Prescriptive maintenance with causal machine learning", *Int. J. Production Economics* 2023 ([arXiv 2206.01562](https://arxiv.org/abs/2206.01562)). 자료는 산업 파트너의 유지보수 계약 4,000건 이상 | 문제 설정이 가장 가까운 선행 연구. 처방적 정비(prescriptive maintenance)의 관점을 따름 |
| 무작위로 배정한 안전 점검으로 사업장마다 다른 효과를 추정하고, 효과가 큰 사업장에 점검을 몰면 예방되는 부상이 최대 2배 | Johnson·Levine·Toffel, *AEJ: Applied* 2023 ([AEA](https://www.aeaweb.org/articles/pdf/doi/10.1257/app.20200659)); 원 무작위 대조 시험(RCT): Levine·Toffel·Johnson, *Science* 2012 | 효과순과 위험순을 따로 비교해 볼 근거. 실제 로그에서 무작위 파일럿을 권하는 이유로도 쓰임 |
| 이중 강건(AIPW, 두 모형 중 하나만 맞아도 효과 추정이 맞는 방법)·교차적합(모형을 맞춘 데이터와 점수를 매기는 데이터를 나누는 방법) | Chernozhukov 외, "Double/debiased machine learning", *Econometrics Journal* 2018; Robins 외 | `causal/estimators.py` |
| DR-learner(이중 강건 점수로 설비별 효과를 배우는 방법) | Kennedy, "Towards optimal doubly robust estimation of heterogeneous causal effects", *EJS* 2023 | `causal/cate.py` 에 있는 비교 대상 |
| DragonNet(점검 확률과 결과를 한 신경망에서 함께 학습해 효과를 추정하는 방법) | Shi·Blei·Veitch, NeurIPS 2019 | `causal/dragonnet.py` (직접 구현) |
| 점검 우선순위가 좋은지 재는 순위 평가(RATE/AUTOC, Qini) | Yadlowsky 외, "Evaluating treatment prioritization rules via RATE" ([arXiv 2111.07966](https://arxiv.org/abs/2111.07966)) | 정답 없이 점수를 비교하는 방법. 이 저장소는 정책 가치(OPE, 로그만으로 추정한 정책의 가치)로 비교함 |
| 정책 학습(점검 규칙을 데이터에서 배우기) | Athey·Wager, "Policy learning with observational data" ([arXiv 1702.02896](https://arxiv.org/abs/1702.02896)) | 정책 가치의 정의에 씀 |
| 숨은 교란(기록에 없는 요인)이 결론을 얼마나 흔드는지 보는 민감도 분석 | Cinelli·Hazlett (omitted variable bias); Chernozhukov 외 "Long Story Short" ([arXiv 2112.13398](https://arxiv.org/abs/2112.13398)) | `causal/sensitivity.py` 의 벤치마크 아이디어의 바탕. 기록된 변수 하나를 기준으로 숨은 요인이 얼마나 셀 수 있는지 가늠함 |
| CATE(설비 조건별 효과) 추정의 어려움 | Yu 외, ICLR 2025. CATE 추정기 16종을 비교한 벤치마크에서, 추정치의 대다수가 "효과 0" 이라고 예측한 경우보다 MSE(평균 제곱 오차)가 나빴음 | 구조를 주지 않은 효과 학습이 위험순을 이기지 못한 이 저장소의 결과와 일치함 |
| 합성 실험의 필요성 | Poinsot 외, ICML 2025 포지션 논문 ([arXiv 2508.08883](https://arxiv.org/abs/2508.08883)) | 정답을 아는 시뮬레이터로 추정기를 검증하는 근거 |

표의 논문 가운데 본문을 직접 읽지 못한 것이 있습니다. arXiv 에 접속할 수 없는 환경이어서 검색 요약으로만 확인했으니, 인용하기 전에 원문을 확인하세요.
