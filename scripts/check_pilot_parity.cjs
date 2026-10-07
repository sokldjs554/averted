// node scripts/check_pilot_parity.cjs cases.json  — 파이썬이 만든 케이스(입력과 기대값)를 JS 포트로 다시 계산해 비교한다.
const fs = require("node:fs");
const P = require("../src/averted/console/pilot.js");
const cases = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
let bad = 0, worst = 0;
for (const c of cases) {
  const a = { baseRate: c.base_rate, avertedPp: c.averted_pp, nAssets: c.n_assets, weeks: c.weeks, treatShare: c.treat_share, icc: c.icc };
  const got = P.plan(a);
  const dp = Math.abs(got.power - c.power);
  worst = Math.max(worst, dp);
  if (dp > 2e-6 || Math.abs(got.minDetectablePp - c.min_detectable_pp) > 1e-5 * Math.max(1, c.min_detectable_pp)) bad++;
  const { weeks, ...rest } = a;
  if (P.requiredWeeks(rest) !== c.required_weeks) bad++;
  if (P.requiredAssets({ ...rest, weeks: c.weeks }) !== c.required_assets) bad++;
}
console.log(JSON.stringify({ cases: cases.length, mismatches: bad, worst_power_diff: worst }));
process.exit(bad ? 1 : 0);
