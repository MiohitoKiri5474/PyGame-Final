import os, pygame, textwrap

os.environ['SDL_VIDEODRIVER'] = 'dummy'
pygame.init()
pygame.display.set_mode((1, 1))

# ── 1. GENERATE DYNAMIC EDITABLE HTML POSTER ─────────────────────────────────
html_content = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8" />
  <title>A1 遊戲展演海報 — 可直接點擊編輯修改版 (MEDIEVIL)</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@700;900&family=Noto+Serif+TC:wght@600;900&family=Plus+Jakarta+Sans:wght@500;700;800&display=swap" rel="stylesheet">
  <style>
    @page {
      size: 594mm 841mm; /* Standard ISO A1 Portrait */
      margin: 0;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: #0d0e15;
      font-family: 'Plus Jakarta Sans', 'Noto Serif TC', -apple-system, sans-serif;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 0;
      color: #fff;
    }

    /* Floating Toolbar */
    .toolbar {
      position: fixed;
      top: 15px;
      z-index: 1000;
      background: rgba(18, 20, 32, 0.95);
      border: 1px solid rgba(245, 197, 66, 0.5);
      padding: 10px 24px;
      border-radius: 50px;
      box-shadow: 0 10px 30px rgba(0,0,0,0.85);
      display: flex;
      align-items: center;
      gap: 15px;
      backdrop-filter: blur(10px);
    }

    .toolbar button {
      background: linear-gradient(135deg, #f5c542, #ff7b00);
      color: #0d0e15;
      font-weight: 800;
      border: none;
      padding: 8px 18px;
      border-radius: 20px;
      cursor: pointer;
      font-size: 14px;
      transition: all 0.2s;
    }

    .toolbar button:hover {
      transform: scale(1.05);
      box-shadow: 0 0 15px rgba(245, 197, 66, 0.6);
    }

    .toolbar .tip {
      font-size: 13px;
      color: #a0a6b8;
    }

    /* A1 Poster Container (Scaled to 594mm x 841mm ratio: 1200px x 1697px) */
    .poster-canvas {
      width: 1200px;
      height: 1697px;
      background: #080910;
      position: relative;
      overflow: hidden;
      box-shadow: 0 25px 70px rgba(0,0,0,0.95);
      border: 4px solid #f5c542;
      border-radius: 12px;
    }

    /* Dynamic Diagonal Background Split (Day Left-Top / Night Right-Bottom) */
    .bg-day {
      position: absolute;
      top: 0; left: 0; width: 100%; height: 50%;
      background: radial-gradient(circle at 20% 20%, #2b3d22 0%, #111a14 60%, #080910 100%);
    }

    .bg-night {
      position: absolute;
      bottom: 0; left: 0; width: 100%; height: 58%;
      background: radial-gradient(circle at 80% 80%, #2e183a 0%, #150d22 55%, #080910 100%);
      clip-path: polygon(0 16%, 100% 0, 100% 100%, 0 100%);
    }

    .inner-border {
      position: absolute;
      top: 20px; left: 20px; right: 20px; bottom: 20px;
      border: 2px solid rgba(245, 197, 66, 0.35);
      border-radius: 8px;
      pointer-events: none;
      z-index: 10;
    }

    /* ── Header ── */
    .header-area {
      position: relative;
      z-index: 20;
      text-align: center;
      padding-top: 45px;
    }

    .pill-badge {
      display: inline-block;
      background: rgba(245, 197, 66, 0.15);
      border: 1px solid rgba(245, 197, 66, 0.5);
      color: #ffe885;
      padding: 6px 22px;
      border-radius: 30px;
      font-size: 15px;
      font-weight: 700;
      letter-spacing: 2px;
      margin-bottom: 10px;
      outline: none;
    }

    .main-title {
      font-family: 'Cinzel', serif;
      font-size: 66px;
      font-weight: 900;
      color: #f5c542;
      letter-spacing: 6px;
      text-shadow: 0 4px 25px rgba(0,0,0,0.9), 0 0 30px rgba(245, 197, 66, 0.4);
      line-height: 1.1;
      outline: none;
    }

    .sub-title {
      font-family: 'Noto Serif TC', serif;
      font-size: 24px;
      font-weight: 700;
      color: #e0e4f0;
      letter-spacing: 4px;
      margin-top: 4px;
      outline: none;
    }

    .quote-ribbon {
      margin: 16px auto 0;
      max-width: 940px;
      background: rgba(10, 12, 20, 0.75);
      border-left: 4px solid #f5c542;
      border-right: 4px solid #f5c542;
      padding: 12px 25px;
      border-radius: 6px;
      font-size: 15px;
      line-height: 1.6;
      color: #c5cbd8;
      backdrop-filter: blur(8px);
      outline: none;
    }

    /* ── Lively Angled Polaroids ── */
    .screenshots-area {
      position: relative;
      z-index: 20;
      display: flex;
      justify-content: center;
      gap: 40px;
      margin-top: 30px;
      padding: 0 50px;
    }

    .polaroid-card {
      background: #fff;
      padding: 12px 12px 34px;
      border-radius: 8px;
      box-shadow: 0 18px 45px rgba(0,0,0,0.85);
      transition: transform 0.3s ease;
      position: relative;
      width: 500px;
    }

    .polaroid-card.day {
      transform: rotate(-2.5deg);
      border: 3px solid #68d391;
    }

    .polaroid-card.night {
      transform: rotate(2.5deg);
      border: 3px solid #e53e3e;
    }

    .polaroid-card:hover {
      transform: scale(1.03) rotate(0deg);
      z-index: 30;
    }

    .polaroid-img {
      width: 100%;
      height: 275px;
      object-fit: cover;
      border-radius: 4px;
      display: block;
    }

    .polaroid-caption {
      color: #1a202c;
      font-weight: 800;
      font-size: 17px;
      margin-top: 10px;
      text-align: center;
      outline: none;
    }

    .sticker-badge {
      position: absolute;
      top: -12px;
      right: -12px;
      background: #f5c542;
      color: #0d0e15;
      font-weight: 900;
      font-size: 13px;
      padding: 5px 12px;
      border-radius: 20px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.4);
      transform: rotate(6deg);
    }

    /* ── Heroes Stickers ── */
    .heroes-showcase {
      position: relative;
      z-index: 25;
      margin-top: 25px;
      display: flex;
      justify-content: space-around;
      padding: 0 60px;
    }

    .hero-sticker-card {
      display: flex;
      align-items: center;
      gap: 16px;
      background: rgba(18, 22, 36, 0.85);
      border: 1.5px solid rgba(245, 197, 66, 0.3);
      padding: 14px 20px;
      border-radius: 16px;
      backdrop-filter: blur(10px);
      width: 325px;
      box-shadow: 0 10px 25px rgba(0,0,0,0.6);
      transition: all 0.25s;
    }

    .hero-sticker-card:hover {
      border-color: #f5c542;
      transform: translateY(-4px);
    }

    .hero-avatar-box {
      width: 70px;
      height: 70px;
      background: rgba(255,255,255,0.06);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      border: 1px solid rgba(245, 197, 66, 0.4);
    }

    .hero-avatar-box img {
      width: 54px;
      height: 54px;
      object-fit: contain;
    }

    .hero-info-title {
      font-family: 'Cinzel', serif;
      font-size: 18px;
      font-weight: 800;
      color: #ffe885;
      outline: none;
    }

    .hero-info-tag {
      font-size: 12px;
      color: #56ccf2;
      font-weight: 700;
      margin-bottom: 3px;
      outline: none;
    }

    .hero-info-desc {
      font-size: 12.5px;
      color: #a0a6b8;
      line-height: 1.4;
      outline: none;
    }

    /* ── Split Features (Night Arcanum vs Day Wildlife) ── */
    .split-features {
      position: relative;
      z-index: 20;
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 30px;
      padding: 25px 60px 0;
    }

    .feature-panel {
      background: rgba(14, 17, 28, 0.85);
      border-radius: 16px;
      padding: 20px 24px;
      border: 1.5px solid rgba(255,255,255,0.1);
      box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    .panel-night { border-top: 4px solid #e63946; }
    .panel-day { border-top: 4px solid #2ec4b6; }

    .panel-head {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 20px;
      font-weight: 800;
      margin-bottom: 12px;
      color: #fff;
      outline: none;
    }

    .panel-desc {
      font-size: 13.5px;
      color: #c5cbd8;
      line-height: 1.6;
      margin-bottom: 15px;
      outline: none;
    }

    .sprite-ribbon {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      background: rgba(0,0,0,0.3);
      padding: 10px;
      border-radius: 10px;
    }

    .sprite-mini-card { text-align: center; flex: 1; }
    .sprite-mini-card img { width: 44px; height: 44px; object-fit: contain; display: block; margin: 0 auto 4px; }
    .sprite-mini-card span { font-size: 11.5px; font-weight: 700; color: #ffe885; display: block; outline: none; }

    /* ── Bottom Biomes & Infrastructure ── */
    .bottom-showcase {
      position: relative;
      z-index: 20;
      margin: 25px 60px 0;
      background: rgba(14, 17, 28, 0.85);
      border-radius: 16px;
      padding: 18px 24px;
      border: 1px solid rgba(245, 197, 66, 0.3);
    }

    .biomes-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 15px;
    }

    .biome-item {
      display: flex;
      align-items: center;
      gap: 10px;
      background: rgba(255,255,255,0.04);
      padding: 8px 12px;
      border-radius: 8px;
    }

    .biome-item img { width: 40px; height: 40px; object-fit: contain; }
    .biome-name { font-size: 13px; font-weight: 800; color: #ffe885; outline: none; }
    .biome-trait { font-size: 11px; color: #a0a6b8; outline: none; }

    .poster-footer {
      position: absolute;
      bottom: 25px;
      left: 0; right: 0;
      text-align: center;
      z-index: 20;
      font-size: 14px;
      font-weight: 800;
      color: #f5c542;
      letter-spacing: 2px;
      outline: none;
    }

    @media print {
      body { background: none; padding: 0; }
      .toolbar { display: none !important; }
      .poster-canvas { width: 100vw; height: 100vh; border: none; box-shadow: none; border-radius: 0; }
    }
  </style>
</head>
<body>

  <div class="toolbar">
    <span class="tip">💡 提示：點擊任何文字即可<b>直接編輯修改</b></span>
    <button onclick="window.print()">🖨️ 列印 / 另存 A1 PDF</button>
  </div>

  <div class="poster-canvas" id="posterArea">
    <div class="bg-day"></div>
    <div class="bg-night"></div>
    <div class="inner-border"></div>

    <div class="header-area">
      <div class="pill-badge" contenteditable="true">✦ 2026 年度暗黑奇幻像素殖民地生存策略 ✦</div>
      <h1 class="main-title" contenteditable="true">M E D I E V I L</h1>
      <div class="sub-title" contenteditable="true">艾瑟爾加德：邊境拓荒者</div>
      <div class="quote-ribbon" contenteditable="true">
        「白晝在未知的迷霧荒野中拓荒建設、採集資源、耕種農田、馴服野獸；<br>
        黑夜深淵魔物破曉襲擊之時，抵禦狂暴狼人、吸血鬼與劇毒殭屍的無盡圍攻。<strong>白晝拓荒寸土，黑夜寸步不讓！</strong>」
      </div>
    </div>

    <div class="screenshots-area">
      <div class="polaroid-card day">
        <span class="sticker-badge">☀️ 白晝拓荒</span>
        <img class="polaroid-img" src="assets/screenshot_day.png" alt="Day Gameplay">
        <div class="polaroid-caption" contenteditable="true">☀️ 白晝營地：農耕建設與生態開拓 (120s)</div>
      </div>
      <div class="polaroid-card night">
        <span class="sticker-badge" style="background:#e53e3e; color:#fff;">🌙 暗夜守城</span>
        <img class="polaroid-img" src="assets/screenshot_night.png" alt="Night Gameplay">
        <div class="polaroid-caption" contenteditable="true">🌙 暗夜防線：魔物夜襲與元素魔法交鋒 (60s)</div>
      </div>
    </div>

    <div class="heroes-showcase">
      <div class="hero-sticker-card">
        <div class="hero-avatar-box"><img src="assets/farmer.png" alt="Farmer"></div>
        <div>
          <div class="hero-info-title" contenteditable="true">拓荒農夫</div>
          <div class="hero-info-tag" contenteditable="true">經濟核心 · 馴化專家</div>
          <div class="hero-info-desc" contenteditable="true">工作神速、小麥耕作採收，享有 1.5 倍野生動物馴服成功率！</div>
        </div>
      </div>

      <div class="hero-sticker-card">
        <div class="hero-avatar-box"><img src="assets/knight.png" alt="Knight"></div>
        <div>
          <div class="hero-info-title" contenteditable="true">聖殿騎士</div>
          <div class="hero-info-tag" contenteditable="true">前線護衛 · 狩獵大師</div>
          <div class="hero-info-desc" contenteditable="true">身披重甲堅盾在前線抗怪，獵捕野獸享有 50% 爆擊與高額傷害！</div>
        </div>
      </div>

      <div class="hero-sticker-card">
        <div class="hero-avatar-box"><img src="assets/magician.png" alt="Magician"></div>
        <div>
          <div class="hero-info-title" contenteditable="true">元素法師</div>
          <div class="hero-info-tag" contenteditable="true">戰略砲台 · 元素掌控</div>
          <div class="hero-info-desc" contenteditable="true">詠唱火焰術範圍爆破、連鎖閃電穿透與冰凍霜結，夜間群攻核心！</div>
        </div>
      </div>
    </div>

    <div class="split-features">
      <div class="feature-panel panel-night">
        <div class="panel-head" contenteditable="true">🌙 暗夜魔物潮與元素魔法防禦</div>
        <div class="panel-desc" contenteditable="true">
          黑夜降臨巢穴將湧出嗜血魔物！防禦箭塔全自動遠程齊射，玩家可即時詠唱火焰、閃電與冰凍三大元素法術大範圍殲滅敵軍！
        </div>
        <div class="sprite-ribbon">
          <div class="sprite-mini-card">
            <img src="assets/werewolf.png" alt="Werewolf">
            <span contenteditable="true">狂暴狼人</span>
          </div>
          <div class="sprite-mini-card">
            <img src="assets/vampire.png" alt="Vampire">
            <span contenteditable="true">暗夜吸血鬼</span>
          </div>
          <div class="sprite-mini-card">
            <img src="assets/zombie.png" alt="Zombie">
            <span contenteditable="true">劇毒殭屍</span>
          </div>
          <div class="sprite-mini-card">
            <img src="assets/tower.png" alt="Tower">
            <span contenteditable="true">防禦箭塔</span>
          </div>
        </div>
      </div>

      <div class="feature-panel panel-day">
        <div class="panel-head" contenteditable="true">🌱 白晝生態馴化與畜欄經濟</div>
        <div class="panel-desc" contenteditable="true">
          探索邊境並馴服野生動物！圈養動物將為營地持續產出新鮮肉品，圈養駿馬更可賦予全體居民 +37.5% 移動加速！
        </div>
        <div class="sprite-ribbon">
          <div class="sprite-mini-card">
            <img src="assets/boar.png" alt="Boar">
            <span contenteditable="true">野豬(產肉)</span>
          </div>
          <div class="sprite-mini-card">
            <img src="assets/horse.png" alt="Horse">
            <span contenteditable="true">駿馬(加速)</span>
          </div>
          <div class="sprite-mini-card">
            <img src="assets/flying_squirrel.png" alt="Squirrel">
            <span contenteditable="true">飛鼠(寵物)</span>
          </div>
          <div class="sprite-mini-card">
            <img src="assets/animal_pen.png" alt="Pen">
            <span contenteditable="true">畜欄建築</span>
          </div>
        </div>
      </div>
    </div>

    <div class="bottom-showcase">
      <div class="biomes-grid">
        <div class="biome-item">
          <img src="assets/river.png" alt="River">
          <div>
            <div class="biome-name" contenteditable="true">水彩河流</div>
            <div class="biome-trait" contenteditable="true">自然緩速 50%</div>
          </div>
        </div>
        <div class="biome-item">
          <img src="assets/mountain.png" alt="Mountain">
          <div>
            <div class="biome-name" contenteditable="true">連綿山脈</div>
            <div class="biome-trait" contenteditable="true">泛洪全揭露障礙</div>
          </div>
        </div>
        <div class="biome-item">
          <img src="assets/swamp.png" alt="Swamp">
          <div>
            <div class="biome-name" contenteditable="true">幽暗泥沼</div>
            <div class="biome-trait" contenteditable="true">5.0s 受困倒數</div>
          </div>
        </div>
        <div class="biome-item">
          <img src="assets/scorched.png" alt="Scorched">
          <div>
            <div class="biome-name" contenteditable="true">熔岩焦土</div>
            <div class="biome-trait" contenteditable="true">持續高溫灼燒</div>
          </div>
        </div>
      </div>
    </div>

    <div class="poster-footer" contenteditable="true">
      第三組 出品 · 《MEDIEVIL (艾瑟爾加德)》 · Python 3.13 & Pygame 2.6 開發
    </div>
  </div>
</body>
</html>"""

with open('docs/a1_poster_editable.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print('Generated docs/a1_poster_editable.html successfully!')

# ── 2. GENERATE EDITABLE VECTOR SVG POSTER (For Illustrator/Figma/Inkscape) ──
svg_content = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 2480 3508" width="2480" height="3508">
  <defs>
    <radialGradient id="dayGrad" cx="20%" cy="20%" r="70%">
      <stop offset="0%" stop-color="#2a3d24" />
      <stop offset="60%" stop-color="#121c16" />
      <stop offset="100%" stop-color="#080910" />
    </radialGradient>
    <radialGradient id="nightGrad" cx="80%" cy="80%" r="70%">
      <stop offset="0%" stop-color="#2d1838" />
      <stop offset="50%" stop-color="#150d22" />
      <stop offset="100%" stop-color="#080910" />
    </radialGradient>
    <filter id="cardShadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="15" stdDeviation="25" flood-color="#000000" flood-opacity="0.8" />
    </filter>
  </defs>

  <!-- Background Base -->
  <rect width="2480" height="3508" fill="#080910" />
  
  <!-- Diagonal Day / Night Backgrounds -->
  <rect width="2480" height="1800" fill="url(#dayGrad)" />
  <polygon points="0,1700 2480,1200 2480,3508 0,3508" fill="url(#nightGrad)" />

  <!-- Gold Outer & Inner Borders -->
  <rect x="50" y="50" width="2380" height="3408" rx="28" fill="none" stroke="#f5c542" stroke-width="6" />
  <rect x="70" y="70" width="2340" height="3368" rx="20" fill="none" stroke="#f5c542" stroke-width="2" stroke-opacity="0.4" />

  <!-- ── Header Section ── -->
  <g id="header" transform="translate(1240, 140)" text-anchor="middle">
    <!-- Badge -->
    <rect x="-360" y="0" width="720" height="56" rx="28" fill="#1e1a2d" stroke="#f5c542" stroke-width="2" />
    <text x="0" y="38" font-family="'Plus Jakarta Sans', sans-serif" font-size="28" font-weight="bold" fill="#ffe885">✦ 2026 年度暗黑奇幻像素殖民地生存策略 ✦</text>

    <!-- Main Title -->
    <text x="0" y="150" font-family="'Cinzel', serif" font-size="110" font-weight="900" fill="#000" dx="4" dy="4">M E D I E V I L</text>
    <text x="0" y="150" font-family="'Cinzel', serif" font-size="110" font-weight="900" fill="#f5c542">M E D I E V I L</text>
    <text x="0" y="210" font-family="'Noto Serif TC', serif" font-size="40" font-weight="bold" fill="#e0e4f0">艾 瑟 爾 加 德 ： 邊 境 拓 荒 者</text>

    <!-- Lore Quote -->
    <rect x="-950" y="250" width="1900" height="110" rx="12" fill="#0a0c14" fill-opacity="0.85" stroke="#f5c542" stroke-width="2" />
    <text x="0" y="295" font-family="'Noto Serif TC', sans-serif" font-size="27" fill="#c5cbd8">「白晝在未知的迷霧荒野中拓荒建設、採集資源、耕種農田、馴服野獸；</text>
    <text x="0" y="335" font-family="'Noto Serif TC', sans-serif" font-size="27" fill="#ffe885" font-weight="bold">黑夜深淵魔物破曉襲擊之時，抵禦狂暴狼人、吸血鬼與劇毒殭屍的無盡圍攻。白晝拓荒寸土，黑夜寸步不讓！」</text>
  </g>

  <!-- ── Polaroids / Gameplay Screenshots ── -->
  <g id="screenshots">
    <!-- Day Screenshot Polaroid (Left, Angled -2.5 deg) -->
    <g transform="translate(160, 560) rotate(-2.5, 520, 310)">
      <rect x="0" y="0" width="1040" height="620" rx="12" fill="#ffffff" filter="url(#cardShadow)" />
      <image href="assets/screenshot_day.png" x="20" y="20" width="1000" height="520" preserveAspectRatio="xMidYMid slice" />
      <text x="520" y="585" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="30" font-weight="bold" fill="#1a202c">☀️ 白晝營地：農耕建設與生態開拓 (120s)</text>
      <!-- Day Badge -->
      <rect x="20" y="20" width="220" height="46" rx="8" fill="#152018" fill-opacity="0.9" stroke="#68d391" stroke-width="2" />
      <text x="130" y="52" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="22" font-weight="bold" fill="#68d391">☀️ 白晝拓荒建設</text>
    </g>

    <!-- Night Screenshot Polaroid (Right, Angled +2.5 deg) -->
    <g transform="translate(1280, 560) rotate(2.5, 520, 310)">
      <rect x="0" y="0" width="1040" height="620" rx="12" fill="#ffffff" filter="url(#cardShadow)" />
      <image href="assets/screenshot_night.png" x="20" y="20" width="1000" height="520" preserveAspectRatio="xMidYMid slice" />
      <text x="520" y="585" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="30" font-weight="bold" fill="#1a202c">🌙 暗夜防線：魔物夜襲與元素魔法交鋒 (60s)</text>
      <!-- Night Badge -->
      <rect x="20" y="20" width="220" height="46" rx="8" fill="#251218" fill-opacity="0.9" stroke="#e53e3e" stroke-width="2" />
      <text x="130" y="52" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="22" font-weight="bold" fill="#e53e3e">🌙 暗夜魔物守城</text>
    </g>
  </g>

  <!-- ── Hero Trio Stickers ── -->
  <g id="heroes" transform="translate(0, 1240)">
    <!-- Farmer -->
    <g transform="translate(160, 0)">
      <rect width="680" height="170" rx="20" fill="#121624" fill-opacity="0.9" stroke="#2ec4b6" stroke-width="2" filter="url(#cardShadow)" />
      <rect x="25" y="25" width="120" height="120" rx="16" fill="#1e2538" stroke="#f5c542" stroke-width="1" />
      <image href="assets/farmer.png" x="40" y="40" width="90" height="90" />
      <text x="175" y="65" font-family="'Noto Serif TC', serif" font-size="32" font-weight="bold" fill="#ffffff">拓荒農夫 (Farmer)</text>
      <text x="175" y="100" font-family="'Plus Jakarta Sans', sans-serif" font-size="22" font-weight="bold" fill="#2ec4b6">經濟核心 · 0.6x 工作神速 · 1.5x 馴服</text>
      <text x="175" y="135" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">負責小麥耕作與生態馴化，殖民地擴張的基石！</text>
    </g>

    <!-- Knight -->
    <g transform="translate(900, 0)">
      <rect width="680" height="170" rx="20" fill="#121624" fill-opacity="0.9" stroke="#f5c542" stroke-width="2" filter="url(#cardShadow)" />
      <rect x="25" y="25" width="120" height="120" rx="16" fill="#1e2538" stroke="#f5c542" stroke-width="1" />
      <image href="assets/knight.png" x="40" y="40" width="90" height="90" />
      <text x="175" y="65" font-family="'Noto Serif TC', serif" font-size="32" font-weight="bold" fill="#ffffff">聖殿騎士 (Knight)</text>
      <text x="175" y="100" font-family="'Plus Jakarta Sans', sans-serif" font-size="22" font-weight="bold" fill="#f5c542">前線堅守 · 狩獵 50% 爆擊 · 銅牆鐵壁</text>
      <text x="175" y="135" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">身披堅甲在前線格擋，阻擋夜間狼人與吸血鬼推進！</text>
    </g>

    <!-- Magician -->
    <g transform="translate(1640, 0)">
      <rect width="680" height="170" rx="20" fill="#121624" fill-opacity="0.9" stroke="#a855f7" stroke-width="2" filter="url(#cardShadow)" />
      <rect x="25" y="25" width="120" height="120" rx="16" fill="#1e2538" stroke="#f5c542" stroke-width="1" />
      <image href="assets/magician.png" x="40" y="40" width="90" height="90" />
      <text x="175" y="65" font-family="'Noto Serif TC', serif" font-size="32" font-weight="bold" fill="#ffffff">元素法師 (Magician)</text>
      <text x="175" y="100" font-family="'Plus Jakarta Sans', sans-serif" font-size="22" font-weight="bold" fill="#a855f7">戰略砲台 · 火焰 / 閃電 / 冰凍三大法術</text>
      <text x="175" y="135" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">詠唱火焰範圍爆破與冰凍霜結，夜間群攻核心！</text>
    </g>
  </g>

  <!-- ── Dual Feature Panels (Night Arcanum vs Day Wildlife) ── -->
  <g id="features" transform="translate(0, 1470)">
    <!-- Night Panel (Left) -->
    <g transform="translate(160, 0)">
      <rect width="1050" height="680" rx="24" fill="#0f111a" fill-opacity="0.9" stroke="#e63946" stroke-width="3" filter="url(#cardShadow)" />
      <rect x="0" y="0" width="1050" height="12" rx="6" fill="#e63946" />
      <text x="40" y="70" font-family="'Noto Serif TC', serif" font-size="38" font-weight="bold" fill="#ffffff">🌙 暗夜魔物潮與元素魔法防禦</text>
      <text x="40" y="130" font-family="'Noto Serif TC', sans-serif" font-size="26" fill="#c5cbd8">黑夜降臨巢穴將湧出嗜血魔物！防禦箭塔全自動遠程齊射，</text>
      <text x="40" y="175" font-family="'Noto Serif TC', sans-serif" font-size="26" fill="#c5cbd8">玩家可即時詠唱火焰、閃電與冰凍三大元素法術大範圍殲滅敵軍！</text>

      <!-- Monster Cards Grid -->
      <g transform="translate(40, 230)">
        <rect x="0" y="0" width="220" height="380" rx="16" fill="#181c2b" stroke="#e63946" stroke-width="2" />
        <image href="assets/werewolf.png" x="50" y="30" width="120" height="120" />
        <text x="110" y="195" text-anchor="middle" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">狂暴狼人</text>
        <text x="110" y="235" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="19" font-weight="bold" fill="#e63946">高速突襲</text>
        <text x="110" y="280" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">撕裂防禦石牆</text>
        <text x="110" y="315" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">需以冰凍術限制</text>
      </g>
      <g transform="translate(290, 230)">
        <rect x="0" y="0" width="220" height="380" rx="16" fill="#181c2b" stroke="#a855f7" stroke-width="2" />
        <image href="assets/vampire.png" x="50" y="30" width="120" height="120" />
        <text x="110" y="195" text-anchor="middle" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">暗夜吸血鬼</text>
        <text x="110" y="235" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="19" font-weight="bold" fill="#a855f7">生命偷取</text>
        <text x="110" y="280" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">敏捷夜行刺客</text>
        <text x="110" y="315" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">需閃電爆發集火</text>
      </g>
      <g transform="translate(540, 230)">
        <rect x="0" y="0" width="220" height="380" rx="16" fill="#181c2b" stroke="#888888" stroke-width="2" />
        <image href="assets/zombie.png" x="50" y="30" width="120" height="120" />
        <text x="110" y="195" text-anchor="middle" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">劇毒殭屍</text>
        <text x="110" y="235" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="19" font-weight="bold" fill="#888888">攻城肉盾</text>
        <text x="110" y="280" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">堅韌緩步推進</text>
        <text x="110" y="315" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">火焰術範圍灼燒</text>
      </g>
      <g transform="translate(790, 230)">
        <rect x="0" y="0" width="220" height="380" rx="16" fill="#181c2b" stroke="#f5c542" stroke-width="2" />
        <image href="assets/tower.png" x="50" y="30" width="120" height="120" />
        <text x="110" y="195" text-anchor="middle" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">防禦箭塔</text>
        <text x="110" y="235" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="19" font-weight="bold" fill="#f5c542">自動齊射</text>
        <text x="110" y="280" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">4格射程鎖敵</text>
        <text x="110" y="315" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">夜間無損輸出</text>
      </g>
    </g>

    <!-- Day Wildlife Panel (Right) -->
    <g transform="translate(1270, 0)">
      <rect width="1050" height="680" rx="24" fill="#0f111a" fill-opacity="0.9" stroke="#2ec4b6" stroke-width="3" filter="url(#cardShadow)" />
      <rect x="0" y="0" width="1050" height="12" rx="6" fill="#2ec4b6" />
      <text x="40" y="70" font-family="'Noto Serif TC', serif" font-size="38" font-weight="bold" fill="#ffffff">🌱 白晝生態馴化與畜欄經濟</text>
      <text x="40" y="130" font-family="'Noto Serif TC', sans-serif" font-size="26" fill="#c5cbd8">探索邊境並馴服野生動物！圈養動物將為營地持續產出新鮮肉品，</text>
      <text x="40" y="175" font-family="'Noto Serif TC', sans-serif" font-size="26" fill="#c5cbd8">圈養駿馬更可賦予全體居民 +37.5% 全域移動加速，繁榮開拓！</text>

      <!-- Wildlife Cards Grid -->
      <g transform="translate(40, 230)">
        <rect x="0" y="0" width="220" height="380" rx="16" fill="#181c2b" stroke="#2ec4b6" stroke-width="2" />
        <image href="assets/boar.png" x="50" y="30" width="120" height="120" />
        <text x="110" y="195" text-anchor="middle" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">野豬 (Boar)</text>
        <text x="110" y="235" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="19" font-weight="bold" fill="#2ec4b6">被動產肉</text>
        <text x="110" y="280" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">每 30 秒產肉品</text>
        <text x="110" y="315" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">溫和生態夥伴</text>
      </g>
      <g transform="translate(290, 230)">
        <rect x="0" y="0" width="220" height="380" rx="16" fill="#181c2b" stroke="#f5c542" stroke-width="2" />
        <image href="assets/horse.png" x="50" y="30" width="120" height="120" />
        <text x="110" y="195" text-anchor="middle" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">駿馬 (Horse)</text>
        <text x="110" y="235" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="19" font-weight="bold" fill="#f5c542">全域加速</text>
        <text x="110" y="280" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">+37.5% 移動加速</text>
        <text x="110" y="315" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">全體居民受惠</text>
      </g>
      <g transform="translate(540, 230)">
        <rect x="0" y="0" width="220" height="380" rx="16" fill="#181c2b" stroke="#56ccf2" stroke-width="2" />
        <image href="assets/flying_squirrel.png" x="50" y="30" width="120" height="120" />
        <text x="110" y="195" text-anchor="middle" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">飛鼠 (Squirrel)</text>
        <text x="110" y="235" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="19" font-weight="bold" fill="#56ccf2">寵物隨行</text>
        <text x="110" y="280" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">忠誠跟隨主人</text>
        <text x="110" y="315" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">可愛靈動伴侶</text>
      </g>
      <g transform="translate(790, 230)">
        <rect x="0" y="0" width="220" height="380" rx="16" fill="#181c2b" stroke="#e63946" stroke-width="2" />
        <image href="assets/bear.png" x="50" y="30" width="120" height="120" />
        <text x="110" y="195" text-anchor="middle" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">巨熊 (Bear)</text>
        <text x="110" y="235" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif" font-size="19" font-weight="bold" fill="#e63946">深山霸主</text>
        <text x="110" y="280" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">反擊狂暴野獸</text>
        <text x="110" y="315" text-anchor="middle" font-family="'Noto Serif TC', sans-serif" font-size="18" fill="#a0a6b8">狩獵獲5份生肉</text>
      </g>
    </g>
  </g>

  <!-- ── 16-Tile Biomes Showcase (Bottom) ── -->
  <g id="biomes" transform="translate(160, 2200)">
    <rect width="2160" height="1020" rx="24" fill="#0f111a" fill-opacity="0.9" stroke="#f5c542" stroke-width="2" filter="url(#cardShadow)" />
    <text x="50" y="75" font-family="'Noto Serif TC', serif" font-size="38" font-weight="bold" fill="#ffffff">🗺️ 16-Tile 四大多元地貌與環境危害系統</text>

    <!-- 4 Biome Cards -->
    <g transform="translate(50, 120)">
      <!-- River -->
      <g transform="translate(0, 0)">
        <rect width="485" height="400" rx="18" fill="#181c2b" stroke="#56ccf2" stroke-width="2" />
        <image href="assets/river.png" x="35" y="30" width="110" height="110" />
        <text x="170" y="80" font-family="'Noto Serif TC', serif" font-size="32" font-weight="bold" fill="#ffffff">水彩河流</text>
        <text x="170" y="120" font-family="'Plus Jakarta Sans', sans-serif" font-size="22" font-weight="bold" fill="#56ccf2">自然緩速 50%</text>
        <text x="35" y="200" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#c5cbd8">16-Tile 水彩核心無縫拼接，</text>
        <text x="35" y="240" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#c5cbd8">穿越時激起水花漣漪，</text>
        <text x="35" y="280" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#a0a6b8">是阻滯魔物的天然護城河！</text>
      </g>

      <!-- Mountain -->
      <g transform="translate(525, 0)">
        <rect width="485" height="400" rx="18" fill="#181c2b" stroke="#b8860b" stroke-width="2" />
        <image href="assets/mountain.png" x="35" y="30" width="110" height="110" />
        <text x="170" y="80" font-family="'Noto Serif TC', serif" font-size="32" font-weight="bold" fill="#ffffff">連綿山脈</text>
        <text x="170" y="120" font-family="'Plus Jakarta Sans', sans-serif" font-size="22" font-weight="bold" fill="#b8860b">泛洪全揭露障礙</text>
        <text x="35" y="200" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#c5cbd8">立體山脈群峰天然阻隔，</text>
        <text x="35" y="240" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#c5cbd8">探索山腳泛洪連通全揭露，</text>
        <text x="35" y="280" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#a0a6b8">群山深處不卡迷霧！</text>
      </g>

      <!-- Swamp -->
      <g transform="translate(1050, 0)">
        <rect width="485" height="400" rx="18" fill="#181c2b" stroke="#2ec4b6" stroke-width="2" />
        <image href="assets/swamp.png" x="35" y="30" width="110" height="110" />
        <text x="170" y="80" font-family="'Noto Serif TC', serif" font-size="32" font-weight="bold" fill="#ffffff">幽暗泥沼</text>
        <text x="170" y="120" font-family="'Plus Jakarta Sans', sans-serif" font-size="22" font-weight="bold" fill="#2ec4b6">5.0s 受困倒數</text>
        <text x="35" y="200" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#c5cbd8">泥濘邊緣自然銜接草地，</text>
        <text x="35" y="240" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#c5cbd8">踏入觸發受困掙扎波紋，</text>
        <text x="35" y="280" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#a0a6b8">限制軍隊機動調配！</text>
      </g>

      <!-- Scorched -->
      <g transform="translate(1575, 0)">
        <rect width="485" height="400" rx="18" fill="#181c2b" stroke="#ff7b00" stroke-width="2" />
        <image href="assets/scorched.png" x="35" y="30" width="110" height="110" />
        <text x="170" y="80" font-family="'Noto Serif TC', serif" font-size="32" font-weight="bold" fill="#ffffff">熔岩焦土</text>
        <text x="170" y="120" font-family="'Plus Jakarta Sans', sans-serif" font-size="22" font-weight="bold" fill="#ff7b00">高溫燃燒灼燒</text>
        <text x="35" y="200" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#c5cbd8">地熱高溫熔岩裂隙，</text>
        <text x="35" y="240" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#c5cbd8">踏入受到持續灼燒扣血，</text>
        <text x="35" y="280" font-family="'Noto Serif TC', sans-serif" font-size="24" fill="#a0a6b8">伴隨火焰餘燼動態特效！</text>
      </g>
    </g>

    <!-- Buildings Strip -->
    <g transform="translate(50, 560)">
      <rect width="2060" height="400" rx="18" fill="#141824" stroke="#f5c542" stroke-width="1.5" />
      <text x="40" y="55" font-family="'Noto Serif TC', serif" font-size="30" font-weight="bold" fill="#ffe885">🏰 五大殖民地防禦與生產建築藍圖</text>
      
      <g transform="translate(40, 90)">
        <!-- Wall -->
        <g transform="translate(0, 0)">
          <rect width="470" height="260" rx="14" fill="#1e2336" stroke="#a0a6b8" stroke-width="1" />
          <image href="assets/wall.png" x="30" y="25" width="80" height="80" />
          <text x="130" y="65" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">城牆 (Wall)</text>
          <text x="130" y="95" font-family="'Plus Jakarta Sans', sans-serif" font-size="18" fill="#f5c542">🪵 4 木材</text>
          <text x="30" y="160" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">阻擋魔物直線推進，</text>
          <text x="30" y="195" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">迫使敵人繞入箭塔射程！</text>
        </g>
        <!-- Tower -->
        <g transform="translate(505, 0)">
          <rect width="470" height="260" rx="14" fill="#1e2336" stroke="#f5c542" stroke-width="1" />
          <image href="assets/tower.png" x="30" y="25" width="80" height="80" />
          <text x="130" y="65" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">防禦塔 (Tower)</text>
          <text x="130" y="95" font-family="'Plus Jakarta Sans', sans-serif" font-size="18" fill="#f5c542">🪵 2 木材 + 🧱 3 石磚</text>
          <text x="30" y="160" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">夜間全自動遠程齊射，</text>
          <text x="30" y="195" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">4格射程鎖定最近魔物！</text>
        </g>
        <!-- House -->
        <g transform="translate(1010, 0)">
          <rect width="470" height="260" rx="14" fill="#1e2336" stroke="#56ccf2" stroke-width="1" />
          <image href="assets/house.png" x="30" y="25" width="80" height="80" />
          <text x="130" y="65" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">民房 (House)</text>
          <text x="130" y="95" font-family="'Plus Jakarta Sans', sans-serif" font-size="18" fill="#f5c542">🪵 4 木材 + 🧱 2 石磚</text>
          <text x="30" y="160" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">提供 +1 人口上限，</text>
          <text x="30" y="195" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">天亮誕生全新拓荒者！</text>
        </g>
        <!-- Farmland -->
        <g transform="translate(1515, 0)">
          <rect width="470" height="260" rx="14" fill="#1e2336" stroke="#2ec4b6" stroke-width="1" />
          <image href="assets/farmland.png" x="30" y="25" width="80" height="80" />
          <text x="130" y="65" font-family="'Noto Serif TC', serif" font-size="26" font-weight="bold" fill="#ffffff">農田 (Farmland)</text>
          <text x="130" y="95" font-family="'Plus Jakarta Sans', sans-serif" font-size="18" fill="#f5c542">🪵 2 木材 + 🌾 1 作物</text>
          <text x="30" y="160" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">自然成熟循環收成，</text>
          <text x="30" y="195" font-family="'Noto Serif TC', sans-serif" font-size="20" fill="#a0a6b8">為殖民地提供永續糧食！</text>
        </g>
      </g>
    </g>
  </g>

  <!-- ── Footer ── -->
  <g id="footer" transform="translate(1240, 3380)" text-anchor="middle">
    <rect x="-800" y="-35" width="1600" height="70" rx="16" fill="#101320" stroke="#f5c542" stroke-width="1" />
    <text x="0" y="12" font-family="'Noto Serif TC', serif" font-size="28" font-weight="bold" fill="#f5c542">第三組 出品 · 《MEDIEVIL (艾瑟爾加德)》 · Python 3.13 &amp; Pygame 2.6 開發</text>
  </g>
</svg>"""

with open('docs/a1_poster_editable.svg', 'w', encoding='utf-8') as f_svg:
    f_svg.write(svg_content)

# Copy SVG and HTML to project root so the user can easily find them right in the root folder
import shutil
shutil.copy('docs/a1_poster_editable.svg', 'a1_poster_editable.svg')
shutil.copy('docs/a1_poster_editable.html', 'a1_poster_editable.html')

print('Generated docs/a1_poster_editable.svg and a1_poster_editable.svg in project root successfully!')
