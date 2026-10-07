/* averted 콘솔 — 정적 데모(window.AVERTED_STATIC)와 라이브 API 가 같은 코드로 돈다. 서버가 준 문자열은 전부 textContent 로 넣는다. */
(function () {
  const C = window.AvertedCharts, P = window.AvertedPilot, el = C.el;
  const STATIC = !!window.AVERTED_STATIC;
  const $ = (id) => document.getElementById(id);
  const slug = (p) => p.replace(/^\/+/, "").replace(/\//g, "_");
  async function api(path, opts) {
    const r = await fetch(STATIC ? `api/${slug(path)}.json` : path, opts);
    if (!r.ok) { let m = r.statusText; try { m = (await r.json()).detail || m; } catch (_) {} throw new Error(`${r.status} ${m}`); }
    return r.json();
  }
  const pp = (v, d = 1) => (v < 0 && Math.abs(v * 100) >= 0.5 * Math.pow(10, -d) ? "−" : "") + Math.abs(v * 100).toFixed(d) + "%p";
  const spp = (v, d = 1) => (v >= 0 ? "+" : "−") + Math.abs(v * 100).toFixed(d) + "%p";
  const pc = (v, d = 1) => (v * 100).toFixed(d) + "%";
  const f2 = (v) => Number(v).toFixed(2);
  const GRADE = ["양호", "주의", "불량"];
  const S = { sid: null, d: null, curve: null, cov: null, hunch: null, pilot: null, schema: null, scatterY: "est" };

  function text(tag, cls, t) { const e = el(tag, cls ? { class: cls } : {}); e.textContent = t; return e; }
  function put(id, ...nodes) { const n = $(id); n.replaceChildren(...nodes); return n; }

  /* ------------------------------------------------------------------ 초기화 */
  async function init() {
    const saved = (() => { try { return localStorage.getItem("averted-theme"); } catch (_) { return null; } })();
    if (saved) document.documentElement.dataset.theme = saved;
    $("theme").addEventListener("click", () => {
      const dark = document.documentElement.dataset.theme === "dark" || (!document.documentElement.dataset.theme && matchMedia("(prefers-color-scheme: dark)").matches);
      const next = dark ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      try { localStorage.setItem("averted-theme", next); } catch (_) {}
      renderAll();
    });
    document.querySelectorAll("nav.tabs button").forEach((b) => b.addEventListener("click", () => showTab(b.dataset.tab)));
    // 접힌 영역은 폭이 0 이라 차트 폭을 못 재므로, 열릴 때 다시 그린다.
    document.querySelectorAll("details.more").forEach((d) => d.addEventListener("toggle", () => { if (d.open && S.d) renderAll(); }));
    const hash = location.hash.replace("#", "");
    if (hash) showTab(hash, false);
    let list;
    try { list = (await api("/v1/scenarios")).scenarios; } catch (e) { put("hero", text("div", "err", "산출물을 불러오지 못했다: " + e.message)); return; }
    const order = ["base", "hunch", "flat"];
    list.sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
    const names = { base: "① 평범한 세계 (기록이 점검 이유를 다 설명)", hunch: "② 함정 세계 (기록에 없는 신호로 점검)", flat: "③ 설비마다 반응이 같은 세계" };
    const sel = $("scn");
    sel.replaceChildren(...list.map((s) => { const o = el("option", { value: s.id }); o.textContent = names[s.id] || s.title; return o; }));
    sel.addEventListener("change", () => loadScenario(sel.value));
    const extras = await Promise.all(["learning_curve", "coverage", "hunch_sweep", "pilot_demo"].map((n) => api(`/v1/artifacts/${n}`).catch(() => null)));
    [S.curve, S.cov, S.hunch, S.pilot] = extras;
    api("/v1/schema").then((s) => { S.schema = s; renderBring(); }).catch(() => {});
    api("/version").then((v) => { const m = v.manifest; if (m) $("foot-meta").textContent = `v${v.version}${m.git ? " · " + m.git : ""} · 산출물 ${m.built_at}`; }).catch(() => {});
    await loadScenario(list[0].id);
  }

  function showTab(name, push = true) {
    document.querySelectorAll("nav.tabs button").forEach((b) => b.setAttribute("aria-selected", String(b.dataset.tab === name)));
    document.querySelectorAll("section.tab").forEach((s) => (s.hidden = s.id !== "tab-" + name));
    if (push) { try { history.replaceState(null, "", "#" + name); } catch (_) {} }
    if (S.d) renderAll();
  }
  const activeTab = () => (document.querySelector("nav.tabs button[aria-selected=true]") || {}).dataset.tab;

  async function loadScenario(id) {
    document.body.classList.add("loading");
    try { S.d = await api(`/v1/scenarios/${id}`); S.sid = id; } catch (e) { put("hero", text("div", "err", "시나리오를 불러오지 못했다: " + e.message)); document.body.classList.remove("loading"); return; }
    document.body.classList.remove("loading");
    initControls();
    renderAll();
  }

  function initControls() {
    const d = S.d, ks = d.policy.ks;
    const kSel = $("who-k");
    kSel.replaceChildren(...ks.map((k) => { const o = el("option", { value: k }); o.textContent = k; if (k === d.policy.k) o.selected = true; return o; }));
    kSel.onchange = renderWho;
    $("who-ope").onchange = renderWho;
    const sites = [...new Set(d.plans.map((p) => p.site))].sort((a, b) => a - b);
    $("plan-site").replaceChildren(...sites.map((s) => { const o = el("option", { value: s }); o.textContent = `사이트 ${s + 1}`; return o; }));
    const fillWeeks = () => {
      const ws = d.plans.filter((p) => p.site === +$("plan-site").value).map((p) => p.week).sort((a, b) => b - a);
      $("plan-week").replaceChildren(...ws.map((w) => { const o = el("option", { value: w }); o.textContent = `${w}주차`; return o; }));
    };
    fillWeeks();
    $("plan-k").replaceChildren(...[2, 4, 6, 8, 10, 12].map((k) => { const o = el("option", { value: k }); o.textContent = k; if (k === 8) o.selected = true; return o; }));
    $("plan-site").onchange = () => { fillWeeks(); renderPlan(); };
    $("plan-week").onchange = renderPlan;
    $("plan-k").onchange = renderPlan;
    $("plan-truth").onchange = renderPlan;
    $("sc-est").onclick = () => { S.scatterY = "est"; renderScatter(); };
    $("sc-truth").onclick = () => { S.scatterY = "truth"; renderScatter(); };
  }

  function renderAll() {
    if (!S.d) return;
    renderHero();
    const t = activeTab();
    if (t === "illusion") renderIllusion();
    else if (t === "who") renderWho();
    else if (t === "plan") renderPlan();
    else if (t === "trust") renderTrust();
    else if (t === "bring") renderBring();
  }

  /* ------------------------------------------------------------------ 상단 */
  function renderHero() {
    const d = S.d, a = d.audit, est = a.estimates, truth = a.truth, data = a.data, k = d.policy.k;
    const w = d.world;
    const desc = { base: "점검 여부를 정하는 이유가 전부 기록에 남아 있는 세계. 보정이 잘 통해야 한다.", hunch: "점검하는 사람이 기록에 없는 신호(소음, 열)를 보고 점검 대상을 고르는 세계. 보정이 틀려야 하고, 감사가 이를 알려야 한다.", flat: "설비 종류나 수리 접수 여부와 상관없이 점검 효과가 같은 세계. 위험순으로 충분해야 한다." };
    $("world-note").textContent = `합성 로그: ${w.n_sites}개 사이트, 설비 ${w.n_assets.toLocaleString("ko-KR")}대, ${Math.round(w.weeks / 52)}년치. ${desc[d.id] || ""}`;
    const naive = est.naive, ai = est.aipw, bad = a.verdict.level === "red";
    const t1v = naive.averted < 0 ? spp(-naive.averted) : "−" + pp(naive.averted);
    const t1s = naive.averted < 0 ? "점검한 설비가 더 고장난다. 점검이 해로워 보인다." : "점검이 고장을 줄이는 것으로 보인다.";
    const t2s = bad ? "감사 결과는 빨강. 보정해도 틀렸다(정답 " + pp(truth.ate_averted) + "). 이 추정은 믿으면 안 된다." : `점검 1회가 고장을 막는다 (정답 ${pp(truth.ate_averted)}).`;
    const pv = d.policy.by_k[String(k)];
    const lr = pv.responsiveness.true_per100, rk = pv.risk.true_per100;
    const lift = lr / rk - 1, worse = lr < rk, same = !worse && lift < 0.05;
    const t3v = (lift >= 0 ? "+" : "−") + Math.abs(lift * 100).toFixed(0) + "%";
    const t3s = worse ? "학습한 효과순이 위험순보다 나쁘다. 감사가 빨강이면 쓰지 않는다." : same ? "위험순과 차이가 없다. 이 세계에서는 위험순으로 충분하다." : "같은 점검 횟수로 위험순보다 고장을 더 많이 막는다.";
    put("hero",
      C.tile("① 로그만 보면", t1v, t1s, naive.averted < 0 ? "bad" : ""),
      C.tile("② 착시를 걷어내면", pp(ai.averted), t2s, bad ? "bad" : "good"),
      C.tile("③ 효과 기준으로 점검하면", t3v, t3s, worse ? "bad" : same ? "" : "good"));
  }

  /* ------------------------------------------------------------------ 착시 */
  function renderIllusion() {
    const d = S.d, a = d.audit, est = a.estimates, data = a.data, truth = a.truth;
    C.hbars($("ill-observed"), [
      { label: "점검한 주", value: data.outcome_rate_treated * 100, color: "var(--series-2)", sub: `전체의 ${pc(data.treated_share)}` },
      { label: "점검하지 않은 주", value: data.outcome_rate_control * 100, color: "var(--deemph)" },
    ], { fmt: (v) => v.toFixed(1) + "%", valueName: "4주 내 고장률", labelW: 130, label: "점검 여부별 4주 내 고장률" });
    $("ill-observed").appendChild(text("div", "sub", `점검한 주의 고장률이 ${pp(data.outcome_rate_treated - data.outcome_rate_control)} 더 높다. 로그만 보면 "점검이 고장을 늘린다"는 결론이 나온다.`));
    const all = [["naive", "그대로 비교", "var(--series-2)"], ["regression", "회귀 보정", "var(--series-1)"], ["ipw", "IPW 보정", "var(--series-1)"], ["aipw", "보정 (AIPW)", "var(--series-1)"]]
      .map(([k, label, color]) => ({ k, label, value: est[k].averted * 100, lo: est[k].averted_lo * 100, hi: est[k].averted_hi * 100, color }));
    const fopt = { fmt: (v) => (v >= 0 ? "" : "−") + Math.abs(v).toFixed(1), refs: [{ x: truth.ate_averted * 100, label: `정답 ${(truth.ate_averted * 100).toFixed(1)}` }] };
    C.forest($("ill-forest"), all.filter((r) => r.k === "naive" || r.k === "aipw"), { ...fopt, label: "그대로 비교한 값과 보정한 값의 점검 1회가 막은 고장(%p)" });
    C.forest($("ill-forest-all"), all, { ...fopt, label: "추정 방법별 점검 1회가 막은 고장(%p)" });
    const dec = d.profile.by_risk_decile;
    C.lineChart($("ill-why"), [
      { name: "점검한 비율", color: "var(--series-2)", markers: true, points: dec.map((r) => ({ x: r.decile + 1, y: r.visit * 100 })) },
      { name: "4주 내 고장률", color: "var(--text-secondary)", markers: true, points: dec.map((r) => ({ x: r.decile + 1, y: r.y * 100 })) },
    ], { height: 220, y0: 0, fmtY: (v) => v.toFixed(0) + "%", fmtX: (v) => String(v), xTicks: 9, label: "위험 십분위별 점검 비율과 고장률", table: { headers: ["위험 십분위", "점검한 비율", "4주 내 고장률"], rows: dec.map((r) => [r.decile + 1, pc(r.visit), pc(r.y)]) } });
    const note = $("ill-note"); note.className = "callout";
    const lines = [];
    if (d.id === "hunch") {
      lines.push(["b", "이 세계에서는 보정해도 틀린다. "], ["t", `점검하는 사람이 기록에 없는 신호를 보고 대상을 고르기 때문에, 기록된 변수로 보정해도 점검 1회의 효과가 ${pp(est.aipw.averted)}로 추정된다(정답 ${pp(truth.ate_averted)}). '감사' 탭에서 이 문제가 잡히는지 볼 수 있다.`]);
      note.classList.add("warn");
    } else if (d.id === "flat") {
      lines.push(["b", "설비마다 반응이 같은 세계. "], ["t", `점검 1회가 평균 ${pp(truth.ate_averted)} 막고, 설비 종류나 수리 접수 여부가 효과를 바꾸지 않는다. 이 세계에서는 위험순으로 충분하다. '점검 대상 고르기' 탭에서 확인할 수 있다.`]);
    } else {
      lines.push(["b", "착시가 사라진다. "], ["t", `로그를 그대로 비교하면 점검한 쪽이 ${pp(Math.abs(est.naive.averted))} 더 고장난다. 기록된 변수로 보정하면 점검 1회가 ${pp(est.aipw.averted)} 막는 것으로 나오고, 정답(${pp(truth.ate_averted)})이 95% 구간 안에 들어온다. 이 추정은 기록에 없는 이유로 점검 대상을 고르지 않았다는 가정 위에 있다.`]);
    }
    note.replaceChildren(...lines.map(([t, s]) => (t === "b" ? text("b", "", s) : document.createTextNode(s))));
  }

  /* ------------------------------------------------------------------ 누구에게 */
  const SHORT = { random: "무작위", round_robin: "돌아가며 (오래 안 본 순)", risk: "위험순", risk_rule: "위험순 + 수리 접수 제외", responsiveness: "효과순 (반응도 모형)", responsiveness_rule: "효과순 + 수리 접수 제외", dr_gbm: "효과순 (DR-learner)", t_learner: "효과순 (T-learner)", dragonnet: "효과순 (DragonNet)", ceiling: "상한 (기록된 변수로 낼 수 있는 최선)", oracle: "오라클 (손상 상태까지 앎)" };
  const POLICY_ORDER = [["random", "base"], ["round_robin", "base"], ["risk", "risk"], ["risk_rule", "risk"], ["responsiveness", "ours"], ["responsiveness_rule", "ours"], ["dr_gbm", "other"], ["t_learner", "other"], ["dragonnet", "other"], ["ceiling", "ref"], ["oracle", "ref"]];
  const FRONT_POLICIES = new Set(["random", "risk", "risk_rule", "responsiveness"]);
  function renderWho() {
    const d = S.d, k = +$("who-k").value, pv = d.policy.by_k[String(k)], ci = k === d.policy.k ? d.policy.ci : null;
    const showAll = $("who-ope").checked;
    const rows = POLICY_ORDER.filter(([key]) => pv[key] && (showAll || FRONT_POLICIES.has(key))).map(([key, tone]) => {
      const r = pv[key], c = ci && ci[key];
      return { label: SHORT[key] || d.policy.labels[key] || key, value: r.true_per100, lo: c ? c.true_lo : undefined, hi: c ? c.true_hi : undefined, ope: showAll ? r.ope_per100 : undefined, opeLo: c && showAll ? c.ope_lo : undefined, opeHi: c && showAll ? c.ope_hi : undefined, tone };
    });
    $("who-sub").textContent = `평가 구간은 ${d.policy.test_weeks[0]}~${d.policy.test_weeks[1]}주, 사이트·주 ${d.policy.n_groups.toLocaleString("ko-KR")}묶음, K=${k}.` + (ci ? " 막대 끝의 선은 95% 구간." : "") + (showAll ? "" : " 위 체크를 켜면 모든 정책이 보인다.");
    C.policyBars($("who-policy"), rows, { label: "정책별 점검 100번당 막는 고장" });
    renderScatter();
    renderCategory();
    renderCurve();
    renderCate();
  }

  function renderScatter() {
    const d = S.d, sc = d.scatter;
    $("sc-est").setAttribute("aria-pressed", String(S.scatterY === "est"));
    $("sc-truth").setAttribute("aria-pressed", String(S.scatterY === "truth"));
    const catKo = Object.fromEntries(d.profile.by_category.map((r) => [r.cat, r.ko]));
    const pts = sc.points.map((p) => {
      const kind = p.sel_risk && p.sel_effect ? "both" : p.sel_risk ? "risk" : p.sel_effect ? "effect" : "none";
      return { x: p.risk, y: S.scatterY === "est" ? p.est : p.truth, kind, title: `${catKo[p.cat] || p.cat}${p.open_wo ? " · 수리 접수" : ""}`, rows: [{ label: "위험", value: pc(p.risk) }, { label: "추정 효과", value: spp(p.est, 2) }, { label: "정답 효과", value: spp(p.truth, 2) }] };
    });
    C.scatter($("who-scatter"), pts, { fmtX: (v) => (v * 100).toFixed(0) + "%", fmtY: (v) => (v * 100).toFixed(0) + "%p", xlabel: "위험 (점검하지 않으면 4주 안에 고장날 확률)", ylabel: S.scatterY === "est" ? "추정한 점검 효과 (막는 고장)" : "정답 점검 효과 (막는 고장)", label: "위험 대 점검 효과 산점도", tableHeaders: ["설비", "위험", "효과", "선택"] });
  }

  function renderCategory() {
    const d = S.d, prof = d.profile;
    const rows = [...prof.by_category.map((r) => ({ name: r.ko, ...r })), ...prof.by_open_wo.map((r) => ({ name: r.open_wo ? "수리 접수됨" : "수리 접수 없음", ...r }))];
    const bar = (v, max, color) => { const w = el("span", { class: "pbar" }); const tr = el("span", { class: "bar-track" }); tr.style.width = "54px"; const b = el("span", { class: "bar" }); b.style.width = Math.max(2, Math.min(1, Math.abs(v) / max) * 54) + "px"; b.style.background = v < 0 ? "var(--critical)" : color || ""; tr.appendChild(b); w.appendChild(tr); w.appendChild(document.createTextNode(pp(v))); return w; };
    C.table($("who-cat"), [
      { h: "구분", nowrap: true, render: (r) => r.name },
      { h: "평균 위험", num: true, nowrap: true, render: (r) => bar(r.risk, 0.3, "var(--series-2)") },
      { h: "점검 비율", num: true, nowrap: true, render: (r) => pc(r.visit) },
      { h: "정답 효과", num: true, nowrap: true, render: (r) => bar(r.tau, 0.04) },
      { h: "추정 효과", num: true, nowrap: true, render: (r) => bar(r.est, 0.04) },
    ], rows);
  }

  function renderCurve() {
    const box = $("who-curve");
    if (!S.curve) { box.replaceChildren(text("div", "empty", "학습곡선 산출물 없음")); return; }
    const sm = S.curve.summary;
    const ks = [...new Set(sm.map((r) => r.k_sites))].sort((a, b) => a - b);
    const spec = [["responsiveness_rule", "효과순 + 규칙", "var(--series-1)", 2.2], ["responsiveness", "효과순", "var(--series-3)", 2], ["risk_rule", "위험순 + 규칙", "var(--series-2)", 2.2], ["risk", "위험순", "var(--text-secondary)", 2]];
    const series = spec.map(([key, name, color, w]) => ({ name, color, width: w, markers: true, points: ks.map((k, i) => { const r = sm.find((x) => x.k_sites === k && x.policy === key); return { x: i, y: r ? r.true_mean : null }; }) }));
    const fixed = S.curve.fixed || {};
    C.lineChart(box, series, { height: 230, y0: 0, fmtY: (v) => v.toFixed(1), fmtX: (v) => (ks[Math.round(v)] ?? "") + "곳", xTicks: ks.length - 1, label: "사이트 수별 정책 가치",
      table: { headers: ["학습 사이트 수", ...spec.map((s) => s[1]), "OPE 오차(효과순)"], rows: ks.map((k) => [k + "곳", ...spec.map(([key]) => { const r = sm.find((x) => x.k_sites === k && x.policy === key); return r ? `${r.true_mean.toFixed(2)} ± ${(r.true_sd || 0).toFixed(2)}` : "–"; }), (() => { const r = sm.find((x) => x.k_sites === k && x.policy === "responsiveness"); return r ? r.ope_abs_err.toFixed(2) : "–"; })()]) } });
    const first = sm.find((x) => x.k_sites === ks[0] && x.policy === "responsiveness"), last = sm.find((x) => x.k_sites === ks[ks.length - 1] && x.policy === "responsiveness");
    if (first && last) box.appendChild(text("div", "sub", `참고: 무작위 ${f2(fixed.random)}, 오라클 ${f2(fixed.oracle)}. 로그만으로 추정한 값(OPE)의 평균 오차는 ${ks[0]}곳일 때 ${first.ope_abs_err.toFixed(2)}, ${ks[ks.length - 1]}곳일 때 ${last.ope_abs_err.toFixed(2)}.`));
  }

  function renderCate() {
    const d = S.d, c = d.cate, pv = d.policy.by_k[String(d.policy.k)];
    const rows = [["responsiveness", "반응도 모형 (직접 구현)"], ["dr_gbm", "DR-learner (트리)"], ["t_learner", "T-learner"], ["dragonnet", "DragonNet (PyTorch)"], ["ceiling", "상한 (정답을 보고 학습)"], ["risk", "위험 예측 (점검 여부를 무시)"]];
    C.table($("who-cate"), [
      { h: "방법", render: (r) => r.name },
      { h: "정답과 순위가 비슷한 정도", num: true, render: (r) => f2(r.sp) },
      { h: "효과 오차 (PEHE, 작을수록 좋음)", num: true, render: (r) => (r.pehe == null ? "–" : r.pehe.toFixed(4)) },
      { h: `점검 100번당 (K=${d.policy.k})`, num: true, render: (r) => (r.v == null ? "–" : f2(r.v)) },
    ], rows.map(([k, name]) => ({ name, sp: c[k].spearman, pehe: c[k].pehe, v: pv[k] ? pv[k].true_per100 : null })));
    const meta = c.dragonnet_meta;
    $("who-cate").appendChild(text("div", "sub", `모든 설비의 효과가 같다고 가정했을 때의 PEHE는 ${c.constant_pehe.toFixed(4)}. 이보다 작아야 설비별 차이를 배운 것이다. DragonNet은 파라미터 ${meta.params.toLocaleString("ko-KR")}개, ${meta.epochs}에포크, CPU ${meta.seconds}초가 들었다.`));
  }

  /* ------------------------------------------------------------------ 이번 주 점검표 */
  function planItem(r, mode, shared, showTruth) {
    const li = el("li", shared ? { class: "shared" } : {});
    li.appendChild(text("span", "rk", String(r._pos)));
    const mid = el("div");
    mid.appendChild(text("div", "nm", `${r.cat_ko} #${r.asset}`));
    mid.appendChild(text("div", "zn", `연식 ${r.age}년, 직전 판정 ${GRADE[r.grade_last]}, 민원 ${r.cmp}, ${r.wsv}주 전 점검`));
    const tags = el("div", { class: "tags" });
    if (r.open_wo) tags.appendChild(C.badge("legal", "수리 접수됨"));
    if (r.low_support) tags.appendChild(C.badge("quiet", "비슷한 점검 사례가 적어 판단 보류"));
    if (shared) tags.appendChild(C.badge("good", "두 목록 공통"));
    mid.appendChild(tags);
    li.appendChild(mid);
    const v = el("div", { class: "vals" });
    if (mode === "effect") {
      v.appendChild(text("b", "", pp(r.averted)));
      v.appendChild(text("small", "", `90% ${pp(r.averted_lo)} ~ ${pp(r.averted_hi)}`));
      v.appendChild(text("small", "", `위험 ${pc(r.risk)}`));
    } else {
      v.appendChild(text("b", "", `위험 ${pc(r.risk)}`));
      v.appendChild(text("small", "", `추정 효과 ${pp(r.averted)}`));
    }
    if (showTruth) v.appendChild(text("small", "truth", `정답 효과 ${pp(r.truth)}`));
    li.appendChild(v);
    return li;
  }

  function renderPlan() {
    const d = S.d, site = +$("plan-site").value, week = +$("plan-week").value, k = +$("plan-k").value, showTruth = $("plan-truth").checked;
    const p = d.plans.find((x) => x.site === site && x.week === week);
    if (!p) { put("plan-cols", text("div", "empty", "이 사이트·주의 점검표 없음")); return; }
    const eff = p.by_effect.slice(0, k).map((r, i) => ({ ...r, _pos: i + 1 })), risk = p.by_risk.slice(0, k).map((r, i) => ({ ...r, _pos: i + 1 }));
    const inRisk = new Set(risk.map((r) => r.asset)), inEff = new Set(eff.map((r) => r.asset));
    const sum = (rows, key) => rows.reduce((s, r) => s + r[key], 0);
    const col = (title, sub, rows, mode, other, totalKey, totalLabel) => {
      const card = el("div", { class: "card" });
      card.appendChild(text("h2", "", title)); card.appendChild(text("div", "sub", sub));
      const ul = el("ul", { class: "plan-list" });
      rows.forEach((r) => ul.appendChild(planItem(r, mode, other.has(r.asset), showTruth)));
      card.appendChild(ul);
      const tot = el("div", { class: "plan-total" });
      tot.appendChild(document.createTextNode(totalLabel + " "));
      tot.appendChild(text("b", "", f2(totalKey === "truth" ? 100 * sum(rows, "truth") / rows.length : 100 * sum(rows, "averted") / rows.length)));
      tot.appendChild(document.createTextNode(" (점검 100번당)"));
      card.appendChild(tot);
      return card;
    };
    const key = showTruth ? "truth" : "averted", lab = showTruth ? "실제로 막는 고장(정답)" : "추정한 막는 고장";
    put("plan-cols", col(`위험순 상위 ${k}`, "고장 예측 모형의 위험이 높은 순서. 보통의 예지보전 방식", risk, "risk", inEff, key, lab), col(`효과순 상위 ${k}`, "점검이 막는 고장의 추정치가 큰 순서. 수리 접수된 설비는 효과가 거의 없다", eff, "effect", inRisk, key, lab));
    const overlap = eff.filter((r) => inRisk.has(r.asset)).length;
    $("plan-note").replaceChildren(text("b", "", "읽는 법: "), document.createTextNode(`두 목록에서 ${overlap}개가 겹친다. 효과의 90% 구간은 설비 단위로 다시 뽑아 계산했다. '비슷한 점검 사례가 적어 판단 보류' 표시가 붙은 설비는 로그에 비슷한 점검 기록이 적어서 추정이 로그 바깥을 짐작한 값이다. '정답 보기'를 켜면 두 목록의 실제 효과를 비교할 수 있다.`));
  }

  /* ------------------------------------------------------------------ 믿어도 되나 */
  function renderTrust() {
    const d = S.d, a = d.audit, v = a.verdict;
    const box = el("div");
    box.appendChild(C.verdictBadge(v.level));
    if (v.warnings.length) { const ul = el("ul", { class: "warnlist" }); v.warnings.forEach((w) => ul.appendChild(text("li", "", w))); box.appendChild(ul); }
    else box.appendChild(text("div", "sub", "비교할 상대, 균형, 점검 이전 고장, 구간 모두에서 데이터로 확인되는 문제가 없다."));
    const dep = el("dl", { class: "kv" });
    const add = (k, val) => { dep.appendChild(text("dt", "", k)); dep.appendChild(text("dd", "", val)); };
    add("가정에 기댄 정도", v.assumption_dependence || "–");
    if (a.tipping) add("효과를 0으로 만들 만큼의 숨은 편향", pp(a.tipping.bias_to_zero_point));
    if (a.negative_control) add("점검 이전 고장에서 보이는 '효과'", `${spp(-a.negative_control.effect, 2)} (z=${a.negative_control.z.toFixed(1)})`);
    add("분석에 쓴 행 / 법정 점검이라 뺀 행", `${a.data.rows_analyzed.toLocaleString("ko-KR")} / ${a.data.rows_excluded_due.toLocaleString("ko-KR")}`);
    box.appendChild(dep);
    box.appendChild(text("div", "sub", "신호등은 데이터로 확인되는 문제만 반영한다. '가정에 기댄 정도'는 기록에 없는 이유로 점검 대상을 고르지 않는다는 가정에 얼마나 기대는지를 나타낸다. 이 가정은 데이터로 검증할 수 없어서 신호등과 따로 표시한다."));
    put("tr-verdict", box);

    const ov = a.overlap, edges = ov.hist_edges;
    const centers = ov.hist_treated.map((_, i) => ((edges[i] + edges[i + 1]) / 2) * 100);
    const nT = ov.hist_treated.reduce((s, x) => s + x, 0) || 1, nC = ov.hist_control.reduce((s, x) => s + x, 0) || 1;
    const ovBox = $("tr-overlap");
    C.lineChart(ovBox, [
      { name: "점검하지 않은 주", color: "var(--deemph)", width: 2, points: centers.map((x, i) => ({ x, y: (ov.hist_control[i] / nC) * 100 })) },
      { name: "점검한 주", color: "var(--series-2)", width: 2, markers: true, points: centers.map((x, i) => ({ x, y: (ov.hist_treated[i] / nT) * 100 })) },
    ], { height: 200, y0: 0, fmtY: (y) => y.toFixed(0) + "%", fmtX: (x) => x.toFixed(0) + "%", xTicks: 5, label: "점검할 확률의 분포" });
    ovBox.appendChild(text("div", "sub", `점검할 확률이 1% 미만인 행은 ${pc(ov.share_below_1pct)}, 99% 초과인 행은 ${pc(ov.share_above_99pct)}. 가중치를 준 뒤 실제로 쓰이는 표본 비율은 점검한 쪽 ${pc(ov.ess_ratio_treated, 0)}, 안 한 쪽 ${pc(ov.ess_ratio_control, 0)}.`));

    const bal = [...a.balance].sort((x, y) => Math.abs(y.smd_raw) - Math.abs(x.smd_raw)).slice(0, 9);
    const scale = Math.max(0.3, ...bal.map((b) => Math.abs(b.smd_raw)));
    const bb = el("div");
    bb.appendChild(C.shapeLegend([{ shape: "rect", color: "var(--text-secondary)", fill: "var(--text-secondary)", label: "가중 전" }, { shape: "rect", color: "var(--series-1)", label: "가중 후" }, { shape: "rect", color: "var(--critical)", label: "기준 0.10" }]));
    bal.forEach((b) => {
      const row = el("div", { class: "smd-row" });
      row.appendChild(text("span", "", b.name));
      const tr = el("span", { class: "smd-track" });
      const i = el("i"); i.style.width = (Math.min(1, Math.abs(b.smd_raw) / scale) * 100) + "%"; tr.appendChild(i);
      const bw = el("b"); bw.style.width = (Math.min(1, Math.abs(b.smd_weighted) / scale) * 100) + "%"; tr.appendChild(bw);
      const s = el("s"); s.style.left = (0.1 / scale) * 100 + "%"; tr.appendChild(s);
      row.appendChild(tr);
      row.appendChild(text("span", "", `${Math.abs(b.smd_raw).toFixed(2)} → ${Math.abs(b.smd_weighted).toFixed(2)}`));
      bb.appendChild(row);
    });
    put("tr-balance", bb);

    const bn = el("div");
    (a.benchmarks || []).forEach((b) => {
      const row = el("div", { class: "bench-row" });
      row.appendChild(text("span", "", b.group));
      row.appendChild(text("b", "", `${pp(a.estimates.aipw.averted)} → ${pp(a.estimates.aipw.averted - b.shift)}`));
      bn.appendChild(row);
    });
    if (a.benchmarks && a.benchmarks.length) bn.insertBefore(text("div", "sub", "변수를 뺀 추정. 왼쪽 변수를 몰랐다면 추정이 이렇게 바뀐다."), bn.firstChild);
    if (a.tipping) bn.appendChild(text("div", "sub", `추정 효과 ${pp(a.estimates.aipw.averted)}와 비교하면 가장 큰 이동은 ${a.tipping.ratio.toFixed(1)}배다. ${a.tipping.ratio > 2 ? "기록된 가장 강한 변수 하나만큼 강한 숨은 요인이 있어도 결론이 뒤집힐 수 있다." : "변수 하나를 몰랐을 때의 이동이 효과보다 작다."}`));
    put("tr-bench", bn);

    renderHunch(); renderCoverage(); renderPilotDemo(); renderPlanner();
  }

  function renderHunch() {
    const box = $("tr-hunch");
    if (!S.hunch) { box.replaceChildren(text("div", "empty", "산출물 없음")); return; }
    const sm = S.hunch.summary;
    C.lineChart(box, [
      { name: "그대로 비교한 값의 오차", color: "var(--series-2)", markers: true, points: sm.map((r, i) => ({ x: i, y: (r.naive - r.truth_averted) * 100 })) },
      { name: "보정(AIPW)한 값의 오차", color: "var(--series-1)", markers: true, points: sm.map((r, i) => ({ x: i, y: (r.aipw - r.truth_averted) * 100 })) },
    ], { height: 210, y0: undefined, fmtY: (v) => v.toFixed(1) + "%p", fmtX: (v) => "γ=" + (sm[Math.round(v)] ? sm[Math.round(v)].gamma.toFixed(1) : ""), xTicks: sm.length - 1, refY: 0, label: "기록에 없는 이유의 강도별 추정 오차" });
    C.table(box.appendChild(el("div")), [
      { h: "γ", num: true, render: (r) => r.gamma.toFixed(1) },
      { h: "보정 오차", num: true, render: (r) => spp(r.aipw - r.truth_averted) },
      { h: "구간이 정답을 덮은 비율", num: true, render: (r) => pc(r.coverage, 0) },
      { h: "감사가 경고한 비율", num: true, render: (r) => pc(r.nc_flag_rate, 0) },
    ], sm);
    box.appendChild(text("div", "sub", "약한 경우(γ≈0.3)는 편향이 효과보다 큰데도 감사가 놓친다. 그래서 '가정에 기댄 정도'를 따로 표시한다. 결정이 중요하면 무작위 파일럿을 권한다."));
  }

  function renderCoverage() {
    const box = $("tr-cov");
    if (!S.cov) { box.replaceChildren(text("div", "empty", "산출물 없음")); return; }
    const sm = S.cov.summary, kinds = [["base", "숨은 요인 없음"], ["flat", "설비별 차이 없음"], ["hunch", "숨은 요인 γ=0.6"]];
    $("tr-cov-sub").textContent = `같은 설정의 세계를 ${S.cov.reps}번씩 새로 만들어 95% 구간이 정답을 덮은 비율을 셌다. 설비 단위로 계산한 구간(AIPW)과 행이 서로 독립이라고 가정한 구간(AIPW-독립)을 비교한다.`;
    const est = [["naive", "그대로 비교"], ["regression", "회귀"], ["ipw", "IPW"], ["aipw", "AIPW (설비 단위 구간)"], ["aipw_iid", "AIPW (행 독립 구간)"]];
    C.table(box, [{ h: "추정 방법", render: (r) => r.name }, ...kinds.map(([k, n]) => ({ h: n, num: true, render: (r) => (sm[k] ? pc(sm[k][r.key].coverage, 0) : "–") }))], est.map(([key, name]) => ({ key, name })));
    box.appendChild(text("div", "sub", "기록에 없는 요인이 없는 세계에서는 AIPW 구간이 약 95%를 덮는다. 회귀 보정은 결과 모형의 오차를 반영하지 않아 덜 덮고, 그대로 비교한 값은 거의 덮지 못한다. 이 합성 데이터는 같은 설비의 기록끼리 닮은 정도가 작아서 두 구간의 차이가 거의 없다. 설비 단위 구간은 기록끼리 많이 닮은 실제 로그를 위한 안전장치다. 기록에 없는 요인이 있는 세계에서는 어떤 구간도 정답을 덮지 못한다. 구간은 기록된 변수 밖의 요인을 알 수 없기 때문이다."));
  }

  function renderPilotDemo() {
    const box = $("tr-pilot"), pd = S.pilot;
    if (!pd) { box.replaceChildren(text("div", "empty", "산출물 없음")); return; }
    const o = pd.observational_aipw, p = pd.pilot_estimate;
    C.forest(box, [
      { label: "로그로 낸 AIPW", value: o.averted * 100, lo: o.averted_lo * 100, hi: o.averted_hi * 100, color: "var(--series-2)" },
      { label: "무작위 파일럿", value: p.averted * 100, lo: p.averted_lo * 100, hi: p.averted_hi * 100, color: "var(--series-1)" },
    ], { fmt: (v) => (v >= 0 ? "" : "−") + Math.abs(v).toFixed(1), refs: [{ x: pd.truth_pilot_averted * 100, label: `정답 ${(pd.truth_pilot_averted * 100).toFixed(1)}` }], label: "로그로 낸 추정과 파일럿 추정" });
    box.appendChild(text("div", "sub", `γ=${pd.config.hunch}. 설비의 ${(pd.config.pilot_share * 100).toFixed(0)}%(${pd.n_pilot_assets.toLocaleString("ko-KR")}대)를 평소 점검 비율(주 ${(pd.config.pilot_visit_rate * 100).toFixed(0)}%)로 무작위 배정했고, 겹치지 않는 4주 창이 ${pd.n_pilot_windows.toLocaleString("ko-KR")}개 나왔다.`));
    const verdict = text("div", pd.observational_contradicts_pilot ? "callout warn" : "callout", "");
    verdict.appendChild(text("b", "", pd.observational_contradicts_pilot ? "로그로 낸 추정이 파일럿과 어긋난다. " : "로그로 낸 추정이 파일럿과 어긋나지 않는다. "));
    verdict.appendChild(document.createTextNode(pd.observational_contradicts_pilot ? "로그로 낸 점검 효과 추정은 의사결정에 쓰지 않고 파일럿 결과를 따른다." : "다만 파일럿 구간이 넓으면 어긋남을 잡아낼 힘도 약하다."));
    if (pd.pilot_ci_includes_zero) verdict.appendChild(document.createTextNode(" 파일럿 구간이 0을 포함한다. 이 규모로는 평균 효과가 있는지 없는지 말할 수 없다는 뜻이다. 계획기가 필요한 규모를 알려 준다."));
    box.appendChild(verdict);
  }

  let plannerState = null;
  function renderPlanner() {
    const box = $("tr-planner");
    const a = S.d.audit;
    const defaults = { base: +(a.pilot.base_rate * 100).toFixed(1), eff: +Math.max(a.pilot.assumed_averted_pp, 0.25).toFixed(2), assets: 500, weeks: 52, share: 50, icc: 0.02 };
    if (!plannerState || plannerState.sid !== S.sid) plannerState = { sid: S.sid, ...defaults };
    const fields = [["base", "점검하지 않을 때 4주 내 고장률 (%)", 0.5, 60, 0.5], ["eff", "검출하려는 효과 (%p)", 0.1, 30, 0.1], ["assets", "파일럿 설비 수", 10, 100000, 10], ["weeks", "기간 (주)", 4, 520, 4], ["share", "점검 배정 비율 (%)", 5, 95, 5], ["icc", "같은 설비 기록 간 상관 (ICC)", 0, 0.5, 0.01]];
    const form = el("div", { class: "planner" });
    const out = el("div", { class: "planner-out" });
    const compute = () => {
      const s = plannerState;
      const a1 = { baseRate: s.base / 100, avertedPp: s.eff, nAssets: Math.round(s.assets), weeks: Math.round(s.weeks), treatShare: s.share / 100, icc: s.icc };
      const r = P.plan(a1);
      const wk = P.requiredWeeks({ baseRate: a1.baseRate, avertedPp: a1.avertedPp, nAssets: a1.nAssets, treatShare: a1.treatShare, icc: a1.icc });
      const na = P.requiredAssets({ baseRate: a1.baseRate, avertedPp: a1.avertedPp, weeks: a1.weeks, treatShare: a1.treatShare, icc: a1.icc });
      const cell = (l, v) => { const d1 = el("div"); d1.appendChild(text("div", "l", l)); d1.appendChild(text("div", "v", v)); return d1; };
      out.replaceChildren(cell("효과를 잡아낼 확률(검정력)", pc(r.power, 0)), cell("80% 확률로 잡아내는 최소 효과", r.minDetectablePp.toFixed(2) + "%p"), cell("이 설비 수로 필요한 기간", wk ? wk + "주" : "도달 불가"), cell("이 기간에 필요한 설비 수", na ? na.toLocaleString("ko-KR") + "대" : "도달 불가"), cell("독립 창 수", r.nRows.toLocaleString("ko-KR")));
    };
    fields.forEach(([key, label, min, max, step]) => {
      const lab = el("label"); lab.appendChild(text("span", "", label));
      const inp = el("input", { type: "number", min, max, step, value: plannerState[key] });
      inp.addEventListener("input", () => { const v = parseFloat(inp.value); if (!Number.isNaN(v)) { plannerState[key] = v; compute(); } });
      lab.appendChild(inp); form.appendChild(lab);
    });
    put("tr-planner", form, out, text("div", "sub", "기본값은 이 세계의 감사 결과(점검하지 않을 때의 고장률, AIPW 효과)다. 작은 효과는 설비 한 곳으로는 잡아낼 수 없다. 효과가 큰 층(민원이 접수된 설비 등)만 대상으로 하면 필요한 규모가 크게 줄어든다."));
    compute();
  }

  /* ------------------------------------------------------------------ 내 로그로 */
  function renderBring() {
    const sc = S.schema;
    if (sc) C.table($("bring-schema"), [{ h: "열", render: (r) => r.column }, { h: "형식", render: (r) => r.type }, { h: "의미", render: (r) => r.meaning }], sc.columns);
    const run = el("div", { class: "upload" });
    run.appendChild(text("div", "sub", STATIC ? "정적 데모에서는 업로드가 꺼져 있다. 로컬에서 서버를 띄우면 같은 화면에서 CSV를 올릴 수 있다." : `CSV를 올리면 감사를 돌린다 (최대 ${sc ? sc.max_rows.toLocaleString("ko-KR") : "400,000"}행, 저장하지 않는다).`));
    const code = el("pre", { class: "code" });
    code.textContent = ["pip install -e .", "averted serve                         # http://localhost:8000", "curl -F file=@my_log.csv 'http://localhost:8000/v1/audit'", "", "# 열 이름이 다르면 (Python)", "from averted.causal.data import LogSpec", "from averted.audit import run_audit", "spec = LogSpec(unit='설비ID', time='주', treatment='점검', outcome='고장', site='건물')", "report = run_audit(df, spec=spec)"].join("\n");
    run.appendChild(code);
    if (!STATIC) {
      const file = el("input", { type: "file", accept: ".csv" });
      const btn = el("button", { class: "btn primary", type: "button" }); btn.textContent = "감사 실행";
      const sample = el("a", { href: "/v1/sample.csv", class: "btn" }); sample.textContent = "샘플 CSV 받기";
      const res = el("div");
      btn.addEventListener("click", async () => {
        if (!file.files[0]) { res.textContent = "CSV 파일을 먼저 골라야 한다."; return; }
        res.textContent = "계산 중. 몇 분 걸릴 수 있다.";
        const fd = new FormData(); fd.append("file", file.files[0]);
        try {
          const rep = await api("/v1/audit?folds=3", { method: "POST", body: fd });
          const box = el("div");
          box.appendChild(C.verdictBadge(rep.verdict.level));
          const ul = el("ul", { class: "warnlist" }); rep.verdict.warnings.forEach((w) => ul.appendChild(text("li", "", w))); box.appendChild(ul);
          const fr = el("div"); box.appendChild(fr);
          C.forest(fr, ["naive", "regression", "ipw", "aipw"].map((k) => ({ label: { naive: "그대로 비교", regression: "회귀", ipw: "IPW", aipw: "AIPW" }[k], value: rep.estimates[k].averted * 100, lo: rep.estimates[k].averted_lo * 100, hi: rep.estimates[k].averted_hi * 100, color: k === "naive" ? "var(--series-2)" : "var(--series-1)" })), { fmt: (v) => (v >= 0 ? "" : "−") + Math.abs(v).toFixed(1), label: "내 로그의 추정" });
          res.replaceChildren(box);
        } catch (e) { res.replaceChildren(text("div", "err", e.message)); }
      });
      run.appendChild(file); run.appendChild(btn); run.appendChild(sample); run.appendChild(res);
    }
    put("bring-run", run);
  }

  window.addEventListener("resize", (() => { let t; return () => { clearTimeout(t); t = setTimeout(() => S.d && renderAll(), 200); }; })());
  init();
})();
