// 데모 GIF 녹화 — `node scripts/record_demo.cjs http://localhost:8020 /tmp/demo /` 뒤 ffmpeg 로 GIF 변환 (Makefile: make demo-gif)
// 흐름: 착시(로그 vs 보정) → 틀리는 세계(감사가 빨강) → 누구에게(위험순 vs 효과순) → 이번 주 점검표(정답 보기) → 믿어도 되나(파일럿 계획기)
const { chromium } = require("playwright");
const { mkdirSync } = require("node:fs");

(async () => {
  const base = process.argv[2] || "http://localhost:8000";
  const out = process.argv[3] || "/tmp/demo";
  const pagePath = process.argv[4] || "/console/";
  mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined, args: ["--no-sandbox"] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 }, recordVideo: { dir: out, size: { width: 1280, height: 800 } }, colorScheme: "light" });
  const page = await ctx.newPage();
  const pause = (ms) => page.waitForTimeout(ms);
  const wait = (sel, t = 90000) => page.waitForSelector(sel, { timeout: t });
  const tab = async (name, ready) => { await page.click(`nav.tabs button[data-tab="${name}"]`); await wait(ready); await pause(500); };

  await page.goto(`${base}${pagePath}`, { waitUntil: "networkidle" });
  await wait("#hero .tile"); await wait("#ill-forest svg");
  await pause(3200);                                   // ① 로그만 보면 +4.8%p → ② 보정하면 0.9%p
  await page.mouse.wheel(0, 380); await pause(2400);   // 위험할수록 더 자주 점검한다
  await page.mouse.wheel(0, -380);
  await page.selectOption("#scn", "hunch"); await pause(2800);   // 틀리는 세계: 보정해도 음수
  await tab("trust", "#tr-verdict .badge"); await pause(3200);   // 감사가 빨강
  await page.selectOption("#scn", "base"); await pause(1200);
  await tab("who", "#who-policy svg"); await pause(3200);        // 점검 100번당 막는 고장
  await page.mouse.wheel(0, 260); await pause(1800);
  await page.click("#sc-truth"); await pause(1800);              // 산점도: 정답 효과로 전환
  await tab("plan", "#plan-cols .plan-list li"); await pause(2200);
  await page.check("#plan-truth"); await pause(3000);            // 정답 보기
  await tab("trust", "#tr-planner input"); await pause(800);
  await page.mouse.wheel(0, 900); await pause(2600);             // 파일럿 계획기
  const video = page.video();
  await ctx.close();
  const path = await video.path();
  await browser.close();
  console.log(path);
})().catch((e) => { console.error(e); process.exit(1); });
