PY ?= python
ARTIFACTS ?= artifacts

.PHONY: help install pipeline scenarios pilot curve coverage hunch summary manifest numbers check-numbers demo demo-gif test lint fmt serve docker clean

help:
	@echo "make install       - 개발 의존성 설치 (CPU torch, econml 교차 검증 포함)"
	@echo "make pipeline      - 시나리오 3종 · 파일럿 · 몬테카를로 · 숨은 교란 스윕 · 학습곡선 → 정적 데모 → 숫자 채우기 (약 2시간, 4 vCPU)"
	@echo "make test          - 단위 테스트 (시뮬레이터 불변식 · econml 일치 · JS 포트 일치 · API)"
	@echo "make serve         - API + 콘솔 (http://localhost:8000/console/)"

install:
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.4"
	$(PY) -m pip install -e ".[dev,crosscheck]"

pipeline: scenarios pilot coverage hunch curve summary manifest demo numbers

scenarios:
	$(PY) scripts/run_all.py --stage scenarios
pilot:
	$(PY) scripts/run_all.py --stage pilot
curve:
	$(PY) scripts/run_all.py --stage curve
coverage:
	$(PY) scripts/run_all.py --stage coverage
hunch:
	$(PY) scripts/run_all.py --stage hunch
summary:
	$(PY) scripts/run_all.py --stage summary
manifest:
	$(PY) scripts/run_all.py --stage manifest

numbers:
	$(PY) scripts/fill_numbers.py --artifacts $(ARTIFACTS)
check-numbers:
	$(PY) scripts/fill_numbers.py --artifacts $(ARTIFACTS) --check

demo:
	$(PY) scripts/build_static_demo.py --out docs/demo --artifacts $(ARTIFACTS)

# 정적 데모를 로컬로 띄워 녹화한다 (Playwright + ffmpeg)
demo-gif:
	mkdir -p /tmp/averted-demo
	cd docs/demo && { $(PY) -m http.server 8020 >/dev/null 2>&1 & echo $$! > /tmp/averted-demo/server.pid; }
	sleep 2
	node scripts/record_demo.cjs http://localhost:8020 /tmp/averted-demo / > /tmp/averted-demo/video.txt 2>&1; \
	kill $$(cat /tmp/averted-demo/server.pid); \
	ffmpeg -y -loglevel error -ss 0.5 -i "$$(tail -1 /tmp/averted-demo/video.txt)" -vf "fps=5,scale=860:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=96:stats_mode=diff[p];[s1][p]paletteuse=dither=none:diff_mode=rectangle" docs/images/demo.gif; \
	ls -la docs/images/demo.gif

test:
	$(PY) -m pytest -q
lint:
	ruff check src tests scripts && ruff format --check src tests scripts
fmt:
	ruff check --fix src tests scripts && ruff format src tests scripts
serve:
	averted serve --port 8000
docker:
	docker compose up --build
clean:
	rm -rf $(ARTIFACTS)/scenarios $(ARTIFACTS)/*.json docs/demo
