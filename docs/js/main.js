// wooafest main.js

const REGIONS = ['서울','경기','인천','부산','대구','광주','대전','울산','세종','강원','충북','충남','전북','전남','경북','경남','제주'];
const REALMS = ['축제','공연','전시','아동가족','교육체험','체육','연극','음악','국악','무용','뮤지컬','오페라'];

const REALM_BADGE = {
  '축제': 'festival', '공연': 'performance', '음악': 'performance', '연극': 'performance',
  '전시': 'exhibition', '무용': 'exhibition', '뮤지컬': 'exhibition', '오페라': 'exhibition',
  '아동가족': 'family', '교육체험': 'edu', '체육': 'sports', '국악': 'performance'
};

let allEvents = [];
let currentFilter = 'weekend';
let currentRealm = 'all';

function parseDate(d) {
  if (!d) return null;
  const s = String(d).replace(/\D/g, '');
  if (s.length === 8) return new Date(`${s.slice(0,4)}-${s.slice(4,6)}-${s.slice(6,8)}`);
  return new Date(d);
}

function getDDay(endDate, startDate) {
  const now = new Date();
  now.setHours(0,0,0,0);
  const end = parseDate(endDate);
  const start = parseDate(startDate);
  if (!end || isNaN(end)) return '';
  const effectiveStart = (start && !isNaN(start)) ? start : end;
  if (now >= effectiveStart && now <= end) return 'LIVE';
  if (now < effectiveStart) {
    const diff = Math.ceil((effectiveStart - now) / 86400000);
    return `D-${diff}`;
  }
  return '종료';
}

function getDDayBadge(endDate, startDate) {
  const label = getDDay(endDate, startDate);
  if (label === 'LIVE') return `<span class="badge badge-live">🟢 LIVE</span>`;
  if (label === '종료') return `<span class="badge badge-dday-future">종료</span>`;
  const n = parseInt(label.replace('D-',''));
  if (n <= 3) return `<span class="badge badge-dday-urgent">${label}</span>`;
  if (n <= 7) return `<span class="badge badge-dday-soon">${label}</span>`;
  if (n <= 30) return `<span class="badge badge-dday-normal">${label}</span>`;
  return `<span class="badge badge-dday-future">${label}</span>`;
}

function getFreeBadge(fee) {
  if (!fee || fee === '무료' || fee === '0' || fee === '0원' || String(fee).trim() === '') {
    return `<span class="badge badge-free">🆓 무료</span>`;
  }
  return `<span class="badge badge-paid">💰 유료</span>`;
}

function getRealmBadge(realm) {
  const cls = REALM_BADGE[realm] || '';
  return `<span class="badge badge-${cls}">${realm}</span>`;
}

function goToEvent(idx) {
  const ev = allEvents[idx];
  if (!ev) return;
  sessionStorage.setItem('wooafest_event', JSON.stringify(ev));
  location.href = 'event.html';
}

function renderEventCard(ev, idx) {
  const title = ev.title || ev['행사명'] || ev['축제명'] || '행사명 없음';
  const place = ev.place || ev['개최장소'] || ev['장소명'] || '';
  const start = ev.startDate || ev['시작일자'] || ev['축제시작일자'] || '';
  const end = ev.endDate || ev['종료일자'] || ev['축제종료일자'] || '';
  const fee = ev.fee || ev['관람요금'] || ev['요금'] || '';
  const realm = ev.realm || ev['분야'] || '행사';

  return `<a href="#" onclick="event.preventDefault();goToEvent(${idx})" class="event-card">
    <div class="event-card-title">${escHtml(title)}</div>
    <div class="event-card-meta">
      ${place ? `<span>📍 ${escHtml(place)}</span>` : ''}
      ${start ? `<span>📅 ${formatDate(start)}${end ? ` ~ ${formatDate(end)}` : ''}</span>` : ''}
    </div>
    <div class="event-card-badges">
      ${getRealmBadge(realm)}
      ${getFreeBadge(fee)}
      ${end ? getDDayBadge(end, start) : ''}
    </div>
  </a>`;
}

function formatDate(d) {
  if (!d) return '';
  const s = String(d).replace(/\D/g, '');
  if (s.length === 8) return `${s.slice(0,4)}.${s.slice(4,6)}.${s.slice(6,8)}`;
  return d;
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function isThisWeekend(startDate, endDate) {
  const now = new Date();
  const day = now.getDay();
  const sat = new Date(now); sat.setDate(now.getDate() + (6 - day) % 7);
  const sun = new Date(sat); sun.setDate(sat.getDate() + 1);
  sat.setHours(0,0,0,0); sun.setHours(23,59,59,999);
  const start = new Date(String(startDate).replace(/(\d{4})(\d{2})(\d{2})/,'$1-$2-$3'));
  const end = new Date(String(endDate).replace(/(\d{4})(\d{2})(\d{2})/,'$1-$2-$3'));
  return start <= sun && end >= sat;
}

function isThisMonth(startDate, endDate) {
  const now = new Date();
  const s = String(startDate).replace(/\D/g,'');
  const e = String(endDate).replace(/\D/g,'');
  const ym = `${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}`;
  return s.slice(0,6) === ym || e.slice(0,6) === ym || (s.slice(0,6) < ym && e.slice(0,6) > ym);
}

function isFree(ev) {
  const fee = ev.fee || ev['관람요금'] || ev['요금'] || '';
  return !fee || fee === '무료' || fee === '0' || fee === '0원' || String(fee).trim() === '';
}

function isKids(ev) {
  const realm = ev.realm || ev['분야'] || '';
  const age = ev.age || ev['입장연령'] || ev['관람연령'] || '';
  return realm.includes('아동') || realm.includes('가족') || String(age).includes('전체') || String(age).includes('0세');
}

function filterEvents(type, btn) {
  currentFilter = type;
  document.querySelectorAll('.quick-tab').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderWeekEvents();
}

function setRealmFilter(realm, btn) {
  currentRealm = realm;
  document.querySelectorAll('#realmFilter .filter-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  renderWeekEvents();
}

function renderWeekEvents() {
  let events = [...allEvents];

  // Apply quick filter
  if (currentFilter === 'weekend') {
    events = events.filter(ev => {
      const s = ev.startDate || ev['시작일자'] || ev['축제시작일자'] || '';
      const e = ev.endDate || ev['종료일자'] || ev['축제종료일자'] || '';
      return isThisWeekend(s, e);
    });
  } else if (currentFilter === 'month') {
    events = events.filter(ev => {
      const s = ev.startDate || ev['시작일자'] || ev['축제시작일자'] || '';
      const e = ev.endDate || ev['종료일자'] || ev['축제종료일자'] || '';
      return isThisMonth(s, e);
    });
  } else if (currentFilter === 'free') {
    events = events.filter(isFree);
  } else if (currentFilter === 'kids') {
    events = events.filter(isKids);
  }

  // Apply realm filter
  if (currentRealm !== 'all') {
    events = events.filter(ev => {
      const realm = ev.realm || ev['분야'] || '';
      return realm.includes(currentRealm);
    });
  }

  const container = document.getElementById('weekEvents');
  if (!container) return;
  if (events.length === 0) {
    container.innerHTML = '<div class="empty">해당 조건의 행사가 없습니다.</div>';
    return;
  }
  container.innerHTML = events.slice(0, 12).map(ev => renderEventCard(ev, allEvents.indexOf(ev))).join('');
}

function renderDeadlineEvents() {
  const now = new Date(); now.setHours(0,0,0,0);
  const upcoming = allEvents
    .filter(ev => {
      const e = ev.endDate || ev['종료일자'] || ev['축제종료일자'] || '';
      const s = ev.startDate || ev['시작일자'] || ev['축제시작일자'] || '';
      if (!e) return false;
      const end = new Date(String(e).replace(/(\d{4})(\d{2})(\d{2})/,'$1-$2-$3'));
      const start = new Date(String(s).replace(/(\d{4})(\d{2})(\d{2})/,'$1-$2-$3'));
      return end >= now && start <= new Date(now.getTime() + 30*86400000);
    })
    .sort((a,b) => {
      const ae = (a.endDate || a['종료일자'] || a['축제종료일자'] || '').toString().replace(/\D/g,'');
      const be = (b.endDate || b['종료일자'] || b['축제종료일자'] || '').toString().replace(/\D/g,'');
      return ae.localeCompare(be);
    })
    .slice(0, 6);

  const container = document.getElementById('deadlineEvents');
  if (!container) return;
  if (upcoming.length === 0) {
    container.innerHTML = '<div class="empty">마감 임박 행사가 없습니다.</div>';
    return;
  }
  container.innerHTML = upcoming.map(ev => renderEventCard(ev, allEvents.indexOf(ev))).join('');
}

function doSearch() {
  const q = document.getElementById('searchInput')?.value.trim();
  if (q) location.href = `search.html?q=${encodeURIComponent(q)}`;
}

async function loadData() {
  try {
    // 이번주 API 데이터
    const weekRes = await fetch('data/culture/this_week.json').catch(() => null);
    if (weekRes && weekRes.ok) {
      const weekData = await weekRes.json();
      allEvents = weekData.items || weekData || [];
    }

    // 전국문화축제 JSON 병합
    const festRes = await fetch('data/festival.json').catch(() => null);
    if (festRes && festRes.ok) {
      const festData = await festRes.json();
      const records = festData.records || festData || [];
      const mapped = records.map(r => ({
        title: r['축제명'] || r['festivalNm'] || '',
        place: r['개최장소'] || r['address'] || '',
        startDate: (r['축제시작일자'] || r['startDate'] || '').replace(/-/g,''),
        endDate: (r['축제종료일자'] || r['endDate'] || '').replace(/-/g,''),
        fee: '',
        realm: '축제',
        lat: r['위도'] || r['lat'] || '',
        lng: r['경도'] || r['lng'] || '',
        tel: r['전화번호'] || r['tel'] || '',
        homepage: r['홈페이지주소'] || r['홈페이지'] || r['homepage'] || '',
        content: r['축제내용'] || r['content'] || '',
        address: r['소재지도로명주소'] || r['소재지지번주소'] || '',
        organizer: r['주최기관명'] || '',
        host: r['주관기관명'] || '',
        sponsor: r['후원기관명'] || ''
      }));
      allEvents = [...allEvents, ...mapped];
    }

    renderDeadlineEvents();
    renderWeekEvents();
  } catch(e) {
    console.error('데이터 로드 실패:', e);
    document.getElementById('deadlineEvents').innerHTML = '<div class="empty">데이터를 불러올 수 없습니다.</div>';
    document.getElementById('weekEvents').innerHTML = '<div class="empty">데이터를 불러올 수 없습니다.</div>';
  }
}

document.addEventListener('DOMContentLoaded', loadData);
