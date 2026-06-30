"""
generate_pages.py — JSON 데이터 → HTML 지역/분야 페이지 자동 생성
"""
import json
import os
from datetime import datetime
from pathlib import Path

DOCS = Path(__file__).parent.parent / 'docs'
DATA = Path(__file__).parent.parent / 'data'
KAKAO_KEY = os.environ.get('KAKAO_MAP_KEY', '')

REGIONS = ['서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종',
           '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']

REGION_EMOJI = {
    '서울': '🏙️', '경기': '🌆', '인천': '✈️', '부산': '🌊', '대구': '🍎',
    '광주': '🎨', '대전': '🔬', '울산': '🏭', '세종': '🏛️', '강원': '🏔️',
    '충북': '🌳', '충남': '🌾', '전북': '🌻', '전남': '🍵', '경북': '🍇',
    '경남': '🌸', '제주': '🍊'
}

REALMS = ['축제', '공연', '전시', '아동가족', '교육체험', '체육', '연극', '음악', '국악', '무용', '뮤지컬', '오페라']

REALM_EMOJI = {
    '축제': '🎭', '공연': '🎵', '전시': '🖼️', '아동가족': '👨‍👩‍👧',
    '교육체험': '🎓', '체육': '⚽', '연극': '🎭', '음악': '🎸',
    '국악': '🥁', '무용': '💃', '뮤지컬': '🎤', '오페라': '🎼'
}

REALM_SEO = {
    '축제': ('전국 축제 2026', '전국 축제 일정을 확인하세요.'),
    '공연': ('전국 공연 행사 2026', '전국 공연, 음악회, 콘서트 일정을 확인하세요.'),
    '전시': ('전국 전시 2026', '전국 미술관, 박물관 전시 일정을 확인하세요.'),
    '아동가족': ('전국 아동가족 행사 2026', '아이랑 갈만한 가족 문화행사를 확인하세요.'),
    '교육체험': ('전국 교육체험 행사 2026', '전국 교육·체험 프로그램 일정을 확인하세요.'),
    '체육': ('전국 체육 행사 2026', '전국 스포츠·체육 행사 일정을 확인하세요.'),
    '연극': ('전국 연극 공연 2026', '전국 연극 공연 일정을 확인하세요.'),
    '음악': ('전국 음악 공연 2026', '전국 음악회, 콘서트 일정을 확인하세요.'),
    '국악': ('전국 국악 공연 2026', '전국 국악 공연 일정을 확인하세요.'),
    '무용': ('전국 무용 공연 2026', '전국 무용, 발레 공연 일정을 확인하세요.'),
    '뮤지컬': ('전국 뮤지컬 2026', '전국 뮤지컬 공연 일정을 확인하세요.'),
    '오페라': ('전국 오페라 2026', '전국 오페라 공연 일정을 확인하세요.')
}


def load_json(path):
    if not path.exists():
        return []
    try:
        d = json.loads(path.read_text('utf-8'))
        return d.get('items', d) if isinstance(d, dict) else d
    except Exception:
        return []


def esc(s):
    return str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def fmt_date(d):
    s = str(d or '').replace('-', '').replace('/', '')
    if len(s) == 8:
        return f"{s[:4]}.{s[4:6]}.{s[6:8]}"
    return d or ''


def dday_badge(end, start=''):
    if not end:
        return ''
    from datetime import datetime
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        e_str = str(end).replace('-', '').replace('/', '')
        s_str = str(start or '').replace('-', '').replace('/', '')
        e = datetime(int(e_str[:4]), int(e_str[4:6]), int(e_str[6:8]))
        s = datetime(int(s_str[:4]), int(s_str[4:6]), int(s_str[6:8])) if s_str else e
        if s <= now <= e:
            return '<span class="badge badge-live">🟢 LIVE</span>'
        if now < s:
            n = (s - now).days
            if n <= 3: return f'<span class="badge badge-dday-urgent">D-{n}</span>'
            if n <= 7: return f'<span class="badge badge-dday-soon">D-{n}</span>'
            return f'<span class="badge badge-dday-normal">D-{n}</span>'
        return '<span class="badge badge-dday-future">종료</span>'
    except Exception:
        return ''


def free_badge(fee):
    if not fee or fee in ('무료', '0', '0원', '없음'):
        return '<span class="badge badge-free">🆓 무료</span>'
    return '<span class="badge badge-paid">💰 유료</span>'


def realm_badge(realm):
    cls_map = {'축제': 'festival', '공연': 'performance', '음악': 'performance',
               '연극': 'performance', '전시': 'exhibition', '무용': 'exhibition',
               '뮤지컬': 'exhibition', '오페라': 'exhibition', '아동가족': 'family',
               '교육체험': 'edu', '체육': 'sports'}
    cls = next((v for k, v in cls_map.items() if k in str(realm)), '')
    return f'<span class="badge badge-{cls}">{esc(realm)}</span>'


def event_card_html(ev, idx):
    import json as _json
    title = esc(ev.get('title') or ev.get('축제명') or ev.get('행사명') or '')
    place = esc(ev.get('place') or ev.get('개최장소') or ev.get('장소명') or '')
    start = ev.get('startDate') or ev.get('시작일자') or ev.get('축제시작일자') or ''
    end = ev.get('endDate') or ev.get('종료일자') or ev.get('축제종료일자') or ''
    fee = ev.get('fee') or ev.get('관람요금') or ev.get('요금') or ''
    realm = ev.get('realm') or ev.get('분야') or '행사'
    import base64 as _b64
    ev_b64 = _b64.b64encode(_json.dumps(ev, ensure_ascii=True).encode('ascii')).decode('ascii')
    return f'''<a href="#" onclick="event.preventDefault();try{{sessionStorage.setItem('wooafest_event',atob('{ev_b64}'));location.href='../event.html'}}catch(e){{}}" class="event-card">
  <div class="event-card-title">{title}</div>
  <div class="event-card-meta">
    {f'<span>📍 {place}</span>' if place else ''}
    {f'<span>📅 {fmt_date(start)}{" ~ " + fmt_date(end) if end else ""}</span>' if start else ''}
  </div>
  <div class="event-card-badges">
    {realm_badge(realm)}{free_badge(fee)}{dday_badge(end, start)}
  </div>
</a>'''


def header_html(active=''):
    return '''<header class="site-header">
  <div class="site-header-inner">
    <a href="/" class="site-logo"><span>🎪</span>우아축제</a>
    <nav class="header-nav">
      <a href="/calendar.html">문화캘린더</a>
      <a href="/지역/서울.html">지역별</a>
      <a href="/분야/축제.html">분야별</a>
    </nav>
  </div>
</header>'''


def footer_html():
    return '''<footer class="footer"><div class="footer-inner"><div class="footer-grid">
  <div class="footer-col"><h4>🎪 우아축제</h4><p>전국 문화행사 정보 허브</p><a href="https://wooahouse.com" target="_blank" style="margin-top:10px;display:inline-block;color:#10B981">wooahouse.com →</a></div>
  <div class="footer-col"><h4>분야별</h4><a href="/분야/축제.html">축제</a><a href="/분야/공연.html">공연</a><a href="/분야/전시.html">전시</a><a href="/분야/아동가족.html">아동가족</a></div>
  <div class="footer-col"><h4>지역별</h4><a href="/지역/서울.html">서울</a><a href="/지역/경기.html">경기</a><a href="/지역/부산.html">부산</a><a href="/지역/제주.html">제주</a></div>
  <div class="footer-col"><h4>정보</h4><a href="/about.html">서비스 소개</a><a href="/privacy.html">개인정보처리방침</a></div>
</div><div class="footer-bottom">&copy; 2026 WooaHouse. All rights reserved.</div></div></footer>'''


def generate_region_page(region):
    emoji = REGION_EMOJI.get(region, '📍')
    items = load_json(DATA / 'culture' / 'by_region' / f'{region}.json')

    # 전국 축제 JSON에서 해당 지역 필터링
    fest_items = load_json(DATA / 'festival.json')
    if isinstance(fest_items, dict):
        fest_items = fest_items.get('records', [])
    REGION_ALIAS = {
        '서울': ['서울특별시', '서울시'],
        '경기': ['경기도'],
        '인천': ['인천광역시', '인천시'],
        '부산': ['부산광역시', '부산시'],
        '대구': ['대구광역시', '대구시'],
        '광주': ['광주광역시', '광주시'],
        '대전': ['대전광역시', '대전시'],
        '울산': ['울산광역시', '울산시'],
        '세종': ['세종특별자치시', '세종시'],
        '강원': ['강원도', '강원특별자치도'],
        '충북': ['충청북도', '충북'],
        '충남': ['충청남도', '충남'],
        '전북': ['전라북도', '전북특별자치도', '전북'],
        '전남': ['전라남도', '전남'],
        '경북': ['경상북도', '경북'],
        '경남': ['경상남도', '경남'],
        '제주': ['제주특별자치도', '제주도'],
    }
    aliases = REGION_ALIAS.get(region, [region])
    for r in fest_items:
        loc = (r.get('소재지도로명주소') or r.get('소재지지번주소') or
               r.get('개최장소') or r.get('주소') or '')
        if any(a in loc for a in aliases):
            items.append({
                'title': r.get('축제명', ''),
                'place': r.get('개최장소', ''),
                'startDate': str(r.get('축제시작일자', '')).replace('-', ''),
                'endDate': str(r.get('축제종료일자', '')).replace('-', ''),
                'lat': str(r.get('위도', '')), 'lng': str(r.get('경도', '')),
                'address': r.get('소재지도로명주소', '') or r.get('소재지지번주소', ''),
                'homepage': r.get('홈페이지주소', ''), 'tel': r.get('전화번호', ''),
                'content': r.get('축제내용', ''),
                'realm': '축제', 'fee': '', 'seq': ''
            })

    today = datetime.now().strftime('%Y%m%d')
    items = [ev for ev in items if (ev.get('endDate') or '99991231') >= today]
    cards_html = ''.join(event_card_html(ev, i) for i, ev in enumerate(items[:30]))
    if not cards_html:
        cards_html = f'<div class="empty">현재 {region} 지역 행사 정보를 수집 중입니다.</div>'

    # description에 실제 행사명 최대 3개 포함
    sample_titles = [ev.get('title') or ev.get('축제명') or '' for ev in items[:5] if ev.get('title') or ev.get('축제명')]
    sample_titles = [t for t in sample_titles if t][:3]
    if sample_titles:
        title_str = ', '.join(sample_titles)
        desc = f"{title_str} 등 {region} 축제·공연·행사 일정을 한눈에 확인하세요. {region} 무료 축제, 아이랑 가볼만한 곳, 이번 주말 {region} 문화행사 총정리."
    else:
        desc = f"{region} 축제, 공연, 전시, 문화행사 일정을 한눈에 확인하세요. {region} 무료 축제, 아이랑 갈만한 가족 행사, 이번 주말 {region} 문화생활 총정리. 매일 업데이트."

    region_links = ''.join(
        f'<a href="{r}.html" class="region-link{" active" if r == region else ""}">{REGION_EMOJI.get(r, "")} {r}</a>'
        for r in REGIONS
    )

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{region} 축제·공연·행사 2026 총정리 — 이번 주말 {region} 문화생활 | 우아축제</title>
<meta name="description" content="{esc(desc)}">
<meta name="keywords" content="{region} 축제 2026, {region} 축제 일정, {region} 공연 행사, {region} 무료 축제, {region} 이번 주말 할거리, {region} 아이랑 갈만한 곳, {region} 문화행사 일정, {region} 전시회, {region} 공연 정보, {region} 문화생활, {region} 주말 나들이, {region} 체험 행사">
<link rel="canonical" href="https://wooafest.wooahouse.com/지역/{region}.html">
<meta property="og:title" content="{region} 축제·공연·행사 총정리 | 우아축제">
<meta property="og:site_name" content="우아축제">
<meta property="og:description" content="{region} 축제, 공연, 전시, 문화행사 정보 총정리.">
<link rel="stylesheet" href="../css/style.css">
<style>ins.adsbygoogle{{display:none!important}}</style>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9ZGENFSXWC"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-9ZGENFSXWC');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6464921081676309" crossorigin="anonymous"></script>
</head>
<body>
{header_html(region)}
<div class="ad-top"><ins class="adsbygoogle" style="display:inline-block;width:728px;height:90px" data-ad-client="ca-pub-6464921081676309" data-ad-slot="7080296704"></ins></div>

<section class="page-hero">
  <h1>{emoji} {region} 축제·공연·행사 총정리</h1>
  <p>{region} 지역에서 열리는 문화행사를 한눈에 확인하세요</p>
</section>

<div class="section">
  <div class="breadcrumb"><a href="/">홈</a><span>›</span>지역별<span>›</span>{region}</div>

  <div class="filter-bar">
    <button class="filter-btn active" onclick="setFilter('all',this)">전체</button>
    <button class="filter-btn" onclick="setFilter('축제',this)">🎭 축제</button>
    <button class="filter-btn" onclick="setFilter('공연',this)">🎵 공연</button>
    <button class="filter-btn" onclick="setFilter('전시',this)">🖼️ 전시</button>
    <button class="filter-btn" onclick="setFilter('아동가족',this)">👶 아이랑</button>
  </div>

  <div style="margin-bottom:16px;font-size:.85rem;color:var(--text-secondary)">
    {region} 지역 행사 {len(items)}건 ({datetime.now().strftime('%Y.%m.%d')} 기준)
  </div>

  <div class="event-grid" id="eventGrid">
    {cards_html}
  </div>
</div>

<div class="ad-middle"><ins class="adsbygoogle" style="display:inline-block;width:728px;height:90px" data-ad-client="ca-pub-6464921081676309" data-ad-slot="1419180025"></ins></div>

<div class="section" style="background:var(--primary-light);margin:0;padding:24px 20px">
  <div style="max-width:1200px;margin:0 auto">
    <h2 style="font-size:1rem;font-weight:700;margin-bottom:12px">다른 지역 행사 보기</h2>
    <div class="region-grid">{region_links}</div>
  </div>
</div>

<div class="section" style="padding-top:24px">
  <!-- 롱테일 SEO 텍스트 -->
  <div style="background:var(--primary-light);border-radius:12px;padding:20px;margin:24px 0;font-size:.85rem;color:var(--text-secondary);line-height:1.9">
    <strong style="color:var(--text-primary)">{region} 축제·공연·행사 정보</strong><br>
    {region} 지역에서 열리는 <strong>축제</strong>, <strong>공연</strong>, <strong>전시</strong>, <strong>문화행사</strong> 일정을 한눈에 확인하세요.
    이번 주말 {region} 나들이, 무료 행사, 아이랑 갈만한 {region} 가족 행사까지 매일 업데이트됩니다.
    {region} 봄축제·여름축제·가을축제·겨울축제 등 계절별 정기 축제와 공연 정보도 확인하세요.
  </div>
  <h2 class="section-title">분야별로 찾기</h2>
  <div class="domain-grid">
    <a href="../분야/축제.html" class="domain-card festival"><span class="icon">🎭</span><span class="name">축제</span></a>
    <a href="../분야/공연.html" class="domain-card performance"><span class="icon">🎵</span><span class="name">공연</span></a>
    <a href="../분야/전시.html" class="domain-card exhibition"><span class="icon">🖼️</span><span class="name">전시</span></a>
    <a href="../분야/아동가족.html" class="domain-card family"><span class="icon">👨‍👩‍👧</span><span class="name">아동가족</span></a>
    <a href="../분야/교육체험.html" class="domain-card"><span class="icon">🎓</span><span class="name">교육체험</span></a>
    <a href="../분야/체육.html" class="domain-card"><span class="icon">⚽</span><span class="name">체육</span></a>
  </div>
</div>

{footer_html()}
<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});(adsbygoogle=window.adsbygoogle||[]).push({{}});</script>
<script>
const allCards = Array.from(document.querySelectorAll('#eventGrid .event-card'));
function setFilter(realm, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  allCards.forEach(c=>{{
    const badge = c.querySelector('.event-card-badges')?.textContent||'';
    c.style.display = (realm==='all' || badge.includes(realm)) ? '' : 'none';
  }});
}}
</script>
</body>
</html>'''

    out = DOCS / '지역' / f'{region}.html'
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(f"  ✅ {out} ({len(items)}건)")


def generate_realm_page(realm):
    emoji = REALM_EMOJI.get(realm, '🎪')
    seo_title, seo_desc = REALM_SEO.get(realm, (f'전국 {realm} 2026', f'전국 {realm} 행사를 확인하세요.'))
    items = load_json(DATA / 'culture' / 'by_realm' / f'{realm}.json')

    if realm == '축제':
        fest_items = load_json(DATA / 'festival.json')
        if isinstance(fest_items, dict):
            fest_items = fest_items.get('records', [])
        for r in fest_items:
            items.append({
                'title': r.get('축제명', ''),
                'place': r.get('개최장소', ''),
                'startDate': str(r.get('축제시작일자', '')).replace('-', ''),
                'endDate': str(r.get('축제종료일자', '')).replace('-', ''),
                'lat': str(r.get('위도', '')), 'lng': str(r.get('경도', '')),
                'address': r.get('소재지도로명주소', '') or r.get('소재지지번주소', ''),
                'homepage': r.get('홈페이지주소', ''), 'tel': r.get('전화번호', ''),
                'content': r.get('축제내용', ''),
                'realm': '축제', 'fee': '', 'seq': ''
            })

    today = datetime.now().strftime('%Y%m%d')
    items = [ev for ev in items if (ev.get('endDate') or '99991231') >= today]
    cards_html = ''.join(event_card_html(ev, i) for i, ev in enumerate(items[:40]))
    if not cards_html:
        cards_html = f'<div class="empty">현재 {realm} 행사 정보를 수집 중입니다.</div>'

    # description에 실제 행사명 최대 3개 포함
    sample_titles = [ev.get('title') or ev.get('행사명') or ev.get('축제명') or '' for ev in items[:5]]
    sample_titles = [t for t in sample_titles if t][:3]
    if sample_titles:
        title_str = ', '.join(sample_titles)
        realm_desc = f"{title_str} 등 전국 {realm} 행사 일정을 한눈에 확인하세요. 무료 {realm}, 아이랑 갈만한 {realm}, 이번 주말 {realm} 일정 총정리."
    else:
        realm_desc = f"{seo_desc} 무료 {realm}, 아이랑 갈만한 {realm} 행사, 이번 주말 {realm} 일정 총정리. 매일 업데이트."

    region_links = ''.join(
        f'<a href="../지역/{r}.html" class="region-link">{REGION_EMOJI.get(r,"")} {r}</a>'
        for r in REGIONS
    )

    html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{seo_title} — 전국 {realm} 일정 총정리 | 우아축제</title>
<meta name="description" content="{esc(realm_desc)}">
<meta name="keywords" content="전국 {realm} 2026, {realm} 일정, {realm} 행사, 무료 {realm}, 이번 주말 {realm}, {realm} 정보, {realm} 스케줄, {realm} 공연 일정, {realm} 티켓, {realm} 예매">
<link rel="canonical" href="https://wooafest.wooahouse.com/분야/{realm}.html">
<meta property="og:title" content="{seo_title} | 우아축제">
<meta property="og:site_name" content="우아축제">
<link rel="stylesheet" href="../css/style.css">
<style>ins.adsbygoogle{{display:none!important}}</style>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9ZGENFSXWC"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-9ZGENFSXWC');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6464921081676309" crossorigin="anonymous"></script>
</head>
<body>
{header_html(realm)}
<div class="ad-top"><ins class="adsbygoogle" style="display:inline-block;width:728px;height:90px" data-ad-client="ca-pub-6464921081676309" data-ad-slot="7080296704"></ins></div>

<section class="page-hero">
  <h1>{emoji} {realm} 행사 총정리</h1>
  <p>전국 {realm} 행사 정보를 한눈에 확인하세요</p>
</section>

<div class="main-layout" style="padding:20px">
  <div class="main-content">
    <div class="breadcrumb"><a href="/">홈</a><span>›</span>분야별<span>›</span>{realm}</div>

    <div class="filter-bar">
      <button class="filter-btn active" onclick="setFilter('all',this)">전체</button>
      <button class="filter-btn" onclick="setFilter('무료',this)">🆓 무료</button>
      <button class="filter-btn" onclick="setFilter('LIVE',this)">🟢 진행중</button>
    </div>

    <div style="margin-bottom:16px;font-size:.85rem;color:var(--text-secondary)">
      전국 {realm} 행사 {len(items)}건 ({datetime.now().strftime('%Y.%m.%d')} 기준)
    </div>

    <div class="event-grid" id="eventGrid">{cards_html}</div>

    <div class="ad-middle"><ins class="adsbygoogle" style="display:inline-block;width:728px;height:90px" data-ad-client="ca-pub-6464921081676309" data-ad-slot="1419180025"></ins></div>

    <h2 style="font-size:1rem;font-weight:700;margin:24px 0 12px">지역별로 찾기</h2>
    <div class="region-grid">{region_links}</div>
  </div>
  <aside class="main-sidebar">
    <div class="sidebar-ad"><ins class="adsbygoogle" style="display:inline-block;width:300px;height:600px" data-ad-client="ca-pub-6464921081676309" data-ad-slot="6255378195"></ins></div>
  </aside>
</div>

{footer_html()}
<script>(adsbygoogle=window.adsbygoogle||[]).push({{}});(adsbygoogle=window.adsbygoogle||[]).push({{}});(adsbygoogle=window.adsbygoogle||[]).push({{}});</script>
<script>
const allCards = Array.from(document.querySelectorAll('#eventGrid .event-card'));
function setFilter(type, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  allCards.forEach(c=>{{
    const txt = c.textContent||'';
    c.style.display = (type==='all' || txt.includes(type)) ? '' : 'none';
  }});
}}
</script>
</body>
</html>'''

    out = DOCS / '분야' / f'{realm}.html'
    out.parent.mkdir(exist_ok=True)
    out.write_text(html, encoding='utf-8')
    print(f"  ✅ {out} ({len(items)}건)")


def get_region_from_address(address):
    REGION_ALIAS = {
        '서울': ['서울특별시', '서울시'],
        '경기': ['경기도'],
        '인천': ['인천광역시', '인천시'],
        '부산': ['부산광역시', '부산시'],
        '대구': ['대구광역시', '대구시'],
        '광주': ['광주광역시', '광주시'],
        '대전': ['대전광역시', '대전시'],
        '울산': ['울산광역시', '울산시'],
        '세종': ['세종특별자치시', '세종시'],
        '강원': ['강원도', '강원특별자치도'],
        '충북': ['충청북도'],
        '충남': ['충청남도'],
        '전북': ['전라북도', '전북특별자치도'],
        '전남': ['전라남도'],
        '경북': ['경상북도'],
        '경남': ['경상남도'],
        '제주': ['제주특별자치도', '제주도'],
    }
    for region, aliases in REGION_ALIAS.items():
        if any(a in address for a in aliases):
            return region
    return ''


def generate_festival_pages():
    fest_dir = DOCS / '축제'
    # 기존 페이지 초기화
    if fest_dir.exists():
        import shutil
        shutil.rmtree(fest_dir)
    fest_dir.mkdir(parents=True)

    fest_data = load_json(DATA / 'festival.json')
    if isinstance(fest_data, dict):
        records = fest_data.get('records', [])
    else:
        records = fest_data

    today = datetime.now()
    generated = 0
    sitemap_entries = []

    for r in records:
        name = r.get('축제명', '').strip()
        if not name:
            continue

        place = r.get('개최장소', '')
        address = r.get('소재지도로명주소') or r.get('소재지지번주소') or ''
        start = str(r.get('축제시작일자', '')).replace('-', '')
        end = str(r.get('축제종료일자', '')).replace('-', '')
        content = r.get('축제내용', '')
        tel = r.get('전화번호', '')
        homepage = r.get('홈페이지주소') or r.get('홈페이지', '')
        organizer = r.get('주최기관명', '')
        host = r.get('주관기관명', '')
        lat = r.get('위도', '')
        lng = r.get('경도', '')
        region = get_region_from_address(address)

        # 날짜 포맷
        start_fmt = fmt_date(start)
        end_fmt = fmt_date(end)

        # 월 추출 (키워드용)
        month_str = f"{start[4:6]}월" if len(start) >= 6 else ''
        year_str = start[:4] if len(start) >= 4 else str(today.year)

        # D-Day 배지
        dday = dday_badge(end, start)

        # SEO description — 구체적 정보 포함
        desc_parts = [f"{name}은 {start_fmt}~{end_fmt}"]
        if place:
            desc_parts.append(f"{place}에서 열립니다")
        if content:
            desc_parts.append(content[:60])
        desc = '. '.join(desc_parts) + f". {region} 축제 일정·장소·입장료 안내." if region else '. '.join(desc_parts) + " 일정·장소·입장료 안내."

        # keywords — 롱테일 집중
        kw_parts = [
            name,
            f"{name} {year_str}",
            f"{name} 일정",
            f"{name} 장소",
        ]
        if region:
            kw_parts += [f"{region} 축제", f"{region} {month_str} 축제", f"{region} 무료축제"]
        if month_str:
            kw_parts += [f"{month_str} 전국축제", f"{month_str} 축제 일정"]
        keywords = ', '.join(kw_parts)

        # ld+json Event 스키마
        ldjson = f'''{{
  "@context": "https://schema.org",
  "@type": "Event",
  "name": "{esc(name)}",
  "startDate": "{start[:4]}-{start[4:6]}-{start[6:8]}" if len(start)==8 else "",
  "endDate": "{end[:4]}-{end[4:6]}-{end[6:8]}" if len(end)==8 else "",
  "location": {{
    "@type": "Place",
    "name": "{esc(place)}",
    "address": "{esc(address)}"
  }},
  "organizer": {{
    "@type": "Organization",
    "name": "{esc(organizer or host)}"
  }},
  "description": "{esc(content[:200])}"
}}'''

        # 안전한 ld+json (f-string 중첩 문제 회피)
        start_iso = f"{start[:4]}-{start[4:6]}-{start[6:8]}" if len(start) == 8 else ''
        end_iso = f"{end[:4]}-{end[4:6]}-{end[6:8]}" if len(end) == 8 else ''
        ldjson = f'''{{"@context":"https://schema.org","@type":"Event","name":"{esc(name)}","startDate":"{start_iso}","endDate":"{end_iso}","location":{{"@type":"Place","name":"{esc(place)}","address":"{esc(address)}"}},"organizer":{{"@type":"Organization","name":"{esc(organizer or host)}"}},"description":"{esc(content[:200])}"}}'''

        import re
        slug = re.sub(r'[\\/:*?"<>|#%&]', '', name).strip().replace(' ', '_')
        url_path = f"https://wooafest.wooahouse.com/축제/{slug}.html"

        # 지역/분야 내부 링크
        region_link = f'<a href="../지역/{region}.html">{region} 축제 전체보기 →</a>' if region else ''

        html = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(name)} {year_str} — {esc(place)} | 우아축제</title>
<meta name="description" content="{esc(desc[:155])}">
<meta name="keywords" content="{esc(keywords)}">
<link rel="canonical" href="{url_path}">
<meta property="og:title" content="{esc(name)} {year_str} | 우아축제">
<meta property="og:description" content="{esc(desc[:100])}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url_path}">
<meta property="og:site_name" content="우아축제">
<script type="application/ld+json">{ldjson}</script>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9ZGENFSXWC"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}}gtag('js',new Date());gtag('config','G-9ZGENFSXWC');</script>
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6464921081676309" crossorigin="anonymous"></script>
<link rel="stylesheet" href="../css/style.css">
<style>ins.adsbygoogle{{display:none!important}}</style>
</head>
<body>
<header class="site-header">
  <div class="site-header-inner">
    <a href="/" class="site-logo"><span>🎪</span>우아축제</a>
    <nav class="header-nav">
      <a href="../calendar.html">문화캘린더</a>
      <a href="../지역/서울.html">지역별</a>
      <a href="../분야/축제.html">분야별</a>
    </nav>
  </div>
</header>

<div class="ad-top"><ins class="adsbygoogle" style="display:inline-block;width:728px;height:90px" data-ad-client="ca-pub-6464921081676309" data-ad-slot="7080296704"></ins></div>

<div class="main-layout" style="padding:20px">
  <div class="main-content">
    <div class="breadcrumb">
      <a href="/">홈</a><span>›</span>
      <a href="../분야/축제.html">축제</a><span>›</span>
      {f'<a href="../지역/{region}.html">{region}</a><span>›</span>' if region else ''}
      <span>{esc(name)}</span>
    </div>

    <div class="detail-card">
      <div class="detail-title">{esc(name)}</div>
      <div class="event-card-badges" style="margin-bottom:16px">
        <span class="badge badge-festival">축제</span>
        <span class="badge badge-free">🆓 무료</span>
        {dday}
      </div>
      <div class="detail-grid">
        <div class="detail-item"><span class="label">📅 기간</span><span class="value">{start_fmt}{'~'+end_fmt if end_fmt and end_fmt!=start_fmt else ''}</span></div>
        {f'<div class="detail-item"><span class="label">📍 장소</span><span class="value">{esc(place)}</span></div>' if place else ''}
        {f'<div class="detail-item"><span class="label">🗺️ 주소</span><span class="value">{esc(address)}</span></div>' if address else ''}
        {f'<div class="detail-item"><span class="label">🏢 주최</span><span class="value">{esc(organizer)}</span></div>' if organizer else ''}
        {f'<div class="detail-item"><span class="label">📋 주관</span><span class="value">{esc(host)}</span></div>' if host else ''}
        {f'<div class="detail-item"><span class="label">📞 문의</span><span class="value"><a href="tel:{esc(tel)}" style="color:var(--primary)">{esc(tel)}</a></span></div>' if tel else ''}
        {f'<div class="detail-item"><span class="label">🌐 홈페이지</span><span class="value"><a href="{esc(homepage)}" target="_blank" rel="noopener" style="color:var(--primary)">바로가기 →</a></span></div>' if homepage else ''}
      </div>
    </div>

    {f'<div class="detail-card"><h2 style="font-size:1rem;font-weight:700;margin-bottom:12px">축제 소개</h2><p style="line-height:1.8;color:var(--text-secondary)">{esc(content)}</p></div>' if content else ''}

    {'<div class="detail-card"><div style="text-align:center"><button onclick="openParking()" style="padding:10px 24px;background:#10B981;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:0.9rem;font-weight:600">🅿️ 근처 주차장 확인 →</button></div></div>' if (lat and lng) or address else ''}

    <div class="ad-middle"><ins class="adsbygoogle" style="display:inline-block;width:728px;height:90px" data-ad-client="ca-pub-6464921081676309" data-ad-slot="1419180025"></ins></div>

    <div class="detail-card" style="background:var(--primary-light)">
      <h2 style="font-size:1rem;font-weight:700;margin-bottom:12px">🔗 관련 페이지</h2>
      <div style="display:flex;flex-wrap:wrap;gap:8px">
        <a href="../분야/축제.html" class="region-link">🎭 전국 축제 전체보기</a>
        {f'<a href="../지역/{region}.html" class="region-link">{REGION_EMOJI.get(region,"")} {region} 축제 전체보기</a>' if region else ''}
        <a href="../calendar.html" class="region-link">📅 문화캘린더</a>
      </div>
    </div>
  </div>

  <aside class="main-sidebar">
    <div class="sidebar-ad"><ins class="adsbygoogle" style="display:inline-block;width:300px;height:600px" data-ad-client="ca-pub-6464921081676309" data-ad-slot="6255378195"></ins></div>
  </aside>
</div>

<footer class="footer"><div class="footer-inner"><div class="footer-grid">
  <div class="footer-col"><h4>🎪 우아축제</h4><p>전국 축제·공연·행사 정보 허브</p><a href="https://wooahouse.com" target="_blank" style="margin-top:10px;display:inline-block;color:#10B981">wooahouse.com →</a></div>
  <div class="footer-col"><h4>분야별</h4><a href="../분야/축제.html">축제</a><a href="../분야/공연.html">공연</a><a href="../분야/전시.html">전시</a><a href="../분야/아동가족.html">아동가족</a></div>
  <div class="footer-col"><h4>지역별</h4><a href="../지역/서울.html">서울</a><a href="../지역/경기.html">경기</a><a href="../지역/부산.html">부산</a><a href="../지역/제주.html">제주</a></div>
  <div class="footer-col"><h4>정보</h4><a href="../about.html">서비스 소개</a><a href="../privacy.html">개인정보처리방침</a></div>
</div><div class="footer-bottom">&copy; 2026 WooaHouse. All rights reserved.</div></div></footer>

<script>
{'function openParking(){window.open("https://wooaparking.wooahouse.com/?lat='+str(lat)+'&lng='+str(lng)+'","_blank")}' if lat and lng else ('function openParking(){window.open("https://wooaparking.wooahouse.com/?q='+esc(address).replace('"','')+'","_blank")}' if address else '')}
(adsbygoogle=window.adsbygoogle||[]).push({{}});
(adsbygoogle=window.adsbygoogle||[]).push({{}});
(adsbygoogle=window.adsbygoogle||[]).push({{}});
</script>
</body>
</html>'''

        fname = fest_dir / f"{slug}.html"
        fname.write_text(html, encoding='utf-8')
        sitemap_entries.append((url_path, 'monthly', '0.7'))
        generated += 1

    print(f"  ✅ 축제 개별 페이지 {generated}개 생성 완료")
    return sitemap_entries


def generate_sitemap(festival_urls=None):
    today = datetime.now().strftime('%Y-%m-%d')
    urls = [
        ('https://wooafest.wooahouse.com/', 'daily', '1.0'),
        ('https://wooafest.wooahouse.com/calendar.html', 'daily', '0.9'),
        ('https://wooafest.wooahouse.com/about.html', 'monthly', '0.5'),
        ('https://wooafest.wooahouse.com/privacy.html', 'monthly', '0.3'),
    ]
    for r in REGIONS:
        urls.append((f'https://wooafest.wooahouse.com/지역/{r}.html', 'weekly', '0.8'))
    for r in REALMS:
        urls.append((f'https://wooafest.wooahouse.com/분야/{r}.html', 'weekly', '0.8'))
    if festival_urls:
        urls.extend(festival_urls)

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, freq, pri in urls:
        xml_lines.append(f'  <url><loc>{loc}</loc><changefreq>{freq}</changefreq><priority>{pri}</priority><lastmod>{today}</lastmod></url>')
    xml_lines.append('</urlset>')

    sitemap = DOCS / 'sitemap.xml'
    sitemap.write_text('\n'.join(xml_lines), encoding='utf-8')
    print(f"  ✅ sitemap.xml ({len(urls)}개 URL)")


if __name__ == '__main__':
    print("🎪 wooafest 페이지 생성 시작")
    print(f"   시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    print("\n📄 지역별 페이지 생성...")
    for region in REGIONS:
        generate_region_page(region)

    print("\n📄 분야별 페이지 생성...")
    for realm in REALMS:
        generate_realm_page(realm)

    print("\n📄 축제 개별 페이지 생성...")
    festival_urls = generate_festival_pages()

    print("\n📄 sitemap.xml 갱신...")
    generate_sitemap(festival_urls)

    print("\n✅ 페이지 생성 완료!")
