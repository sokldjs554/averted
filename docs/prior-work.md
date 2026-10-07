# 선행 연구 — 내가 발명한 것이 아니라, 검증된 설계를 시설점검에 적용한 것이다

| 주제 | 출처 | 이 저장소에서의 쓰임 |
|---|---|---|
| 정비의 개별 효과를 관측 데이터에서 인과 ML 로 추정하고 정비 빈도를 최적화 | Vanderschueren 외, "Prescriptive maintenance with causal machine learning", *Int. J. Production Economics* 2023 ([arXiv 2206.01562](https://arxiv.org/abs/2206.01562)) — 산업 파트너의 유지보수 계약 4,000건 이상 | 문제 설정의 직접 선행. "예측이 아니라 처방"이라는 관점 |
| 무작위 배정된 안전 점검으로 이질적 효과를 추정하고, 효과가 큰 사업장에 점검을 몰면 예방 부상이 최대 2배 | Johnson·Levine·Toffel, *AEJ: Applied* 2023 ([AEA](https://www.aeaweb.org/articles/pdf/doi/10.1257/app.20200659)); 원 RCT: Levine·Toffel·Johnson, *Science* 2012 | "효과순 vs 위험순" 질문이 실제로 가치가 있다는 근거. 이 저장소가 실제 로그에서 무작위 파일럿을 권하는 이유 |
| 이중 강건(AIPW)·교차적합 | Chernozhukov 외, "Double/debiased machine learning", *Econometrics Journal* 2018; Robins 외 | `causal/estimators.py` |
| DR-learner | Kennedy, "Towards optimal doubly robust estimation of heterogeneous causal effects", *EJS* 2023 | `causal/cate.py` 의 비교 대상 |
| DragonNet | Shi·Blei·Veitch, NeurIPS 2019 | `causal/dragonnet.py` (직접 구현) |
| 순위 평가(RATE/AUTOC, Qini) | Yadlowsky 외, "Evaluating treatment prioritization rules via RATE" ([arXiv 2111.07966](https://arxiv.org/abs/2111.07966)) | 정답 없이 점수를 비교하는 길 — 이 저장소는 정책 가치(OPE)로 비교한다 |
| 정책 학습 | Athey·Wager, "Policy learning with observational data" ([arXiv 1702.02896](https://arxiv.org/abs/1702.02896)) | 정책 가치의 정의 |
| 숨은 교란 민감도 | Cinelli·Hazlett (omitted variable bias); Chernozhukov 외 "Long Story Short" ([arXiv 2112.13398](https://arxiv.org/abs/2112.13398)) | `causal/sensitivity.py` 의 벤치마크 아이디어 |
| CATE 추정기는 어렵다 | Yu 외, ICLR 2025 — CATE 추정기 16종 벤치마크에서 추정치의 대다수가 "효과 0" 예측보다 MSE 가 나빴다 | 구조 없는 효과 학습이 위험순을 못 이긴다는 이 저장소의 결과와 일치 |
| 합성 실험의 필요성 | Poinsot 외, ICML 2025 포지션 ([arXiv 2508.08883](https://arxiv.org/abs/2508.08883)) | 정답을 아는 시뮬레이터로 추정기를 검증하는 이유 |

위 항목 중 논문 본문을 직접 읽지 못한 것(arXiv 접속이 막힌 환경에서 검색 요약으로만 확인)이 있다. 인용 전에 원문을 확인할 것.
