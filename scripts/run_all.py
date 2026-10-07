"""모든 실험을 단계별로 돌려 artifacts/ 를 만든다.

    python scripts/run_all.py                 # 없는 산출물만 만든다
    python scripts/run_all.py --stage learning_curve --force
단계: scenarios · pilot · curve · coverage · hunch · manifest
README·문서의 숫자는 이 산출물에서 `scripts/fill_numbers.py` 가 채운다.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

ART = Path("artifacts")

SCENARIOS = {
    "base": ("평범한 세계 — 기록이 점검 이유를 다 설명한다", {}),
    "hunch": ("함정 세계 — 기록에 없는 신호로 점검한다", {"hunch": 1.0}),
    "flat": ("설비마다 반응이 같은 세계 — 위험순으로 충분하다", {"flat": True}),
}


def dump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=float))
    print(f"[run_all] wrote {path} ({path.stat().st_size / 1e3:.0f} KB)", flush=True)


def stage_scenarios(force: bool, n_sites: int) -> None:
    from averted.eval.protocol import run_scenario
    from averted.sim.world import WorldConfig

    for name, (title, kw) in SCENARIOS.items():
        out = ART / "scenarios" / f"{name}.json"
        if out.exists() and not force:
            print(f"[run_all] skip {out}")
            continue
        cfg = WorldConfig(seed=11, n_sites=n_sites, weeks=156, burn_in=78, **kw)
        run_scenario(cfg, name, title, out_dir=ART / "scenarios", truth_m=48)


def stage_pilot(force: bool, n_sites: int) -> None:
    out = ART / "pilot_demo.json"
    if out.exists() and not force:
        return
    from averted.eval.pilot_demo import pilot_demo

    dump(out, pilot_demo(n_sites=n_sites))


def stage_curve(force: bool) -> None:
    out = ART / "learning_curve.json"
    if out.exists() and not force:
        return
    from averted.eval.learning_curve import learning_curve, summarize

    res = learning_curve()
    res["summary"] = summarize(res)
    dump(out, res)


def stage_coverage(force: bool, reps: int) -> None:
    out = ART / "coverage.json"
    if out.exists() and not force:
        return
    from averted.eval.coverage import coverage, summarize

    rows = coverage(reps=reps)
    dump(out, {"reps": reps, "summary": summarize(rows), "rows": rows})


def stage_hunch(force: bool) -> None:
    out = ART / "hunch_sweep.json"
    if out.exists() and not force:
        return
    from averted.eval.hunch_sweep import hunch_sweep, summarize

    rows = hunch_sweep(gammas=(0.0, 0.3, 0.6, 1.0, 1.5), seeds=(1, 2, 3, 4, 5), n_sites=8, weeks=120)
    dump(out, {"summary": summarize(rows), "rows": rows})


def stage_summary() -> None:
    """문서·README 의 숫자 마커가 읽는 요약(파생 지표 포함). 시나리오·학습곡선·몬테카를로·스윕 산출물에서 계산한다."""
    out: dict = {}
    for name in SCENARIOS:
        p = ART / "scenarios" / f"{name}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text())
        a, k = d["audit"], str(d["policy"]["k"])
        v = d["policy"]["by_k"][k]
        t = {key: val["true_per100"] for key, val in v.items()}
        e = a["estimates"]
        out[name] = {
            "rows": d["world"]["rows"],
            "n_sites": d["world"]["n_sites"],
            "n_assets": d["world"]["n_assets"],
            "outcome_rate_treated": a["data"]["outcome_rate_treated"],
            "outcome_rate_control": a["data"]["outcome_rate_control"],
            "naive_gap": a["data"]["outcome_rate_treated"] - a["data"]["outcome_rate_control"],
            "naive_averted": e["naive"]["averted"],
            "aipw_averted": e["aipw"]["averted"],
            "aipw_lo": e["aipw"]["averted_lo"],
            "aipw_hi": e["aipw"]["averted_hi"],
            "truth_averted": a["truth"]["ate_averted"],
            "aipw_covers_truth": bool(
                e["aipw"]["averted_lo"] <= a["truth"]["ate_averted"] <= e["aipw"]["averted_hi"]
            ),
            "verdict": a["verdict"]["level"],
            "assumption_dependence": a["verdict"]["assumption_dependence"],
            "nc_z": (a.get("negative_control") or {}).get("z"),
            "per100": t,
            "lift_resp_vs_risk": t["responsiveness"] / t["risk"] - 1,
            "lift_resp_vs_risk_rule": t["responsiveness"] / t["risk_rule"] - 1,
            "lift_risk_rule_vs_risk": t["risk_rule"] / t["risk"] - 1,
            "ceiling_share": t["responsiveness"] / t["ceiling"],
            "ope_abs_err_resp": abs(v["responsiveness"]["ope_per100"] - v["responsiveness"]["true_per100"]),
            "resp_vs_random_x": t["responsiveness"] / t["random"],
        }
    curve = ART / "learning_curve.json"
    if curve.exists():
        c = json.loads(curve.read_text())["summary"]
        ks = sorted({r["k_sites"] for r in c})

        def at(k, pol, key="true_mean"):
            r = next((x for x in c if x["k_sites"] == k and x["policy"] == pol), None)
            return r[key] if r else None

        by_k = {}
        for k in ks:
            row = {r["policy"]: r["true_mean"] for r in c if r["k_sites"] == k}
            row["ope_err_responsiveness"] = at(k, "responsiveness", "ope_abs_err")
            by_k[f"k{k}"] = row
        out["curve"] = {
            "n_test_sites": json.loads(curve.read_text())["n_test_sites"],
            "by_k": by_k,
            "k_min": ks[0],
            "k_max": ks[-1],
            "resp_min": at(ks[0], "responsiveness"),
            "risk_min": at(ks[0], "risk"),
            "resp_max": at(ks[-1], "responsiveness"),
            "risk_max": at(ks[-1], "risk"),
            "rule_max": at(ks[-1], "risk_rule"),
            "lift_min": at(ks[0], "responsiveness") / at(ks[0], "risk") - 1,
            "lift_max": at(ks[-1], "responsiveness") / at(ks[-1], "risk") - 1,
            "ope_err_min": at(ks[0], "responsiveness", "ope_abs_err"),
            "ope_err_max": at(ks[-1], "responsiveness", "ope_abs_err"),
        }
    cov = ART / "coverage.json"
    if cov.exists():
        sm = json.loads(cov.read_text())["summary"]
        out["coverage"] = {
            kind: {est: v["coverage"] for est, v in d.items() if isinstance(v, dict) and "coverage" in v}
            for kind, d in sm.items()
        }
    hs = ART / "hunch_sweep.json"
    if hs.exists():
        sm = json.loads(hs.read_text())["summary"]
        out["hunch_sweep"] = {
            f"g{r['gamma']:.1f}".replace(".", "_"): {
                "bias": r["bias"],
                "nc_flag_rate": r["nc_flag_rate"],
                "coverage": r["coverage"],
                "naive": r["naive"],
                "aipw": r["aipw"],
                "truth": r["truth_averted"],
            }
            for r in sm
        }
    pd_ = ART / "pilot_demo.json"
    if pd_.exists():
        p = json.loads(pd_.read_text())
        out["pilot"] = {
            "pilot_averted": p["pilot_estimate"]["averted"],
            "pilot_lo": p["pilot_estimate"]["averted_lo"],
            "pilot_hi": p["pilot_estimate"]["averted_hi"],
            "obs_averted": p["observational_aipw"]["averted"],
            "truth": p["truth_pilot_averted"],
            "contradicts": p["observational_contradicts_pilot"],
            "n_assets": p["n_pilot_assets"],
            "n_windows": p["n_pilot_windows"],
        }
    dump(ART / "summary.json", out)


def stage_manifest() -> None:
    import averted

    sha = (
        subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
        or None
    )
    scen = []
    for name, (title, _) in SCENARIOS.items():
        p = ART / "scenarios" / f"{name}.json"
        if p.exists():
            d = json.loads(p.read_text())
            scen.append(
                {
                    "id": name,
                    "title": title,
                    "rows": d["world"]["rows"],
                    "n_sites": d["world"]["n_sites"],
                    "level": d["audit"]["verdict"]["level"],
                }
            )
    dump(
        ART / "manifest.json",
        {
            "version": averted.__version__,
            "git": sha,
            "python": platform.python_version(),
            "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "scenarios": scen,
        },
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--stage",
        choices=["scenarios", "pilot", "curve", "coverage", "hunch", "summary", "manifest", "all"],
        default="all",
    )
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--sites", type=int, default=60)
    ap.add_argument("--reps", type=int, default=40)
    a = ap.parse_args()
    t0 = time.time()
    run = lambda s: a.stage in (s, "all")  # noqa: E731
    if run("scenarios"):
        stage_scenarios(a.force, a.sites)
    if run("pilot"):
        stage_pilot(a.force, a.sites)
    if run("curve"):
        stage_curve(a.force)
    if run("coverage"):
        stage_coverage(a.force, a.reps)
    if run("hunch"):
        stage_hunch(a.force)
    if run("summary"):
        stage_summary()
    if run("manifest"):
        stage_manifest()
    print(f"[run_all] done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
