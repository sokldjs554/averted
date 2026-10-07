/* 무작위 파일럿 계획기 — src/averted/causal/pilot.py 의 브라우저 포트 (정적 데모에서 백엔드 없이 계산한다).
 * 같은 식이 같은 값을 내는지는 tests/test_pilot_parity.py 가 node 로 확인한다. */
(function (root) {
  const Z_ALPHA = 1.959963984540054; // Φ⁻¹(0.975)
  const Z_POWER = 0.8416212335729143; // Φ⁻¹(0.8)

  function normCdf(x) {
    // Numerical Recipes erfc (상대 오차 < 1.2e-7)
    const z = Math.abs(x) / Math.SQRT2;
    const t = 1 / (1 + 0.5 * z);
    const r = t * Math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 + t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223 + t * 0.17087277)))))))));
    return x >= 0 ? 1 - 0.5 * r : 0.5 * r;
  }

  function seTwoProp(p0, p1, nT, nC, de) {
    const v = (p1 * (1 - p1)) / Math.max(nT, 1) + (p0 * (1 - p0)) / Math.max(nC, 1);
    return Math.sqrt(v * de);
  }

  function plan({ baseRate, avertedPp, nAssets, weeks, treatShare = 0.5, icc = 0.02, horizon = 4 }) {
    const windows = Math.max(Math.floor(weeks / horizon), 1);
    const nRows = nAssets * windows;
    const de = 1 + (windows - 1) * icc;
    const nT = nRows * treatShare, nC = nRows * (1 - treatShare);
    const p0 = baseRate, p1 = Math.max(baseRate - avertedPp / 100, 1e-6);
    const se = seTwoProp(p0, p1, nT, nC, de);
    const power = se > 0 ? normCdf(Math.abs(p0 - p1) / se - Z_ALPHA) : 0;
    const mde = (Z_ALPHA + Z_POWER) * seTwoProp(p0, p0, nT, nC, de);
    return { power, se, designEffect: de, nRows, minDetectablePp: mde * 100 };
  }

  function requiredWeeks(a, targetPower = 0.8, maxWeeks = 520) {
    for (let w = 4; w <= maxWeeks; w += 4) if (plan({ ...a, weeks: w }).power >= targetPower) return w;
    return null;
  }

  function requiredAssets(a, targetPower = 0.8, maxAssets = 200000) {
    if (plan({ ...a, nAssets: maxAssets }).power < targetPower) return null;
    let lo = 1, hi = maxAssets;
    while (lo < hi) {
      const mid = Math.floor((lo + hi) / 2);
      if (plan({ ...a, nAssets: mid }).power >= targetPower) hi = mid; else lo = mid + 1;
    }
    return lo;
  }

  const api = { plan, requiredWeeks, requiredAssets, normCdf };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.AvertedPilot = api;
})(typeof self !== "undefined" ? self : this);
