// wooafest calendar.js

let calYear = new Date().getFullYear();
let calMonth = new Date().getMonth(); // 0-indexed
let calEvents = [];

const REALM_COLOR = {
  '축제': 'festival', '공연': 'performance', '음악': 'performance', '연극': 'performance',
  '전시': 'exhibition', '무용': 'exhibition', '뮤지컬': 'exhibition',
  '아동가족': 'family', '교육체험': 'edu', '체육': 'sports'
};

function getColorClass(realm) {
  for (const [key, cls] of Object.entries(REALM_COLOR)) {
    if (realm && realm.includes(key)) return cls;
  }
  return 'performance';
}

function renderCalendar() {
  const titleEl = document.getElementById('calTitle');
  if (titleEl) titleEl.textContent = `${calYear}년 ${calMonth+1}월`;

  const grid = document.getElementById('calGrid');
  if (!grid) return;

  const firstDay = new Date(calYear, calMonth, 1).getDay();
  const daysInMonth = new Date(calYear, calMonth+1, 0).getDate();
  const daysInPrev = new Date(calYear, calMonth, 0).getDate();
  const today = new Date(); today.setHours(0,0,0,0);

  let html = '';
  let dayCount = 0;
  const totalCells = Math.ceil((firstDay + daysInMonth) / 7) * 7;

  for (let i = 0; i < totalCells; i++) {
    let date, month, year, isOther = false;
    if (i < firstDay) {
      date = daysInPrev - firstDay + i + 1;
      month = calMonth === 0 ? 11 : calMonth - 1;
      year = calMonth === 0 ? calYear - 1 : calYear;
      isOther = true;
    } else if (i >= firstDay + daysInMonth) {
      date = i - firstDay - daysInMonth + 1;
      month = calMonth === 11 ? 0 : calMonth + 1;
      year = calMonth === 11 ? calYear + 1 : calYear;
      isOther = true;
    } else {
      date = i - firstDay + 1;
      month = calMonth;
      year = calYear;
    }

    const dateStr = `${year}${String(month+1).padStart(2,'0')}${String(date).padStart(2,'0')}`;
    const d = new Date(year, month, date);
    const isToday = d.getTime() === today.getTime();

    const dayEvents = calEvents.filter(ev => {
      const s = (ev.startDate || ev['시작일자'] || ev['축제시작일자'] || '').toString().replace(/\D/g,'');
      const e = (ev.endDate || ev['종료일자'] || ev['축제종료일자'] || '').toString().replace(/\D/g,'');
      if (!s) return false;
      // 단기 행사(7일 이하): 기간 내 모든 날 표시
      // 장기 행사(8일 이상): 시작일에만 표시
      const duration = e && s ? (new Date(e.slice(0,4),e.slice(4,6)-1,e.slice(6,8)) - new Date(s.slice(0,4),s.slice(4,6)-1,s.slice(6,8))) / 86400000 : 0;
      if (duration > 7) return s === dateStr;
      return s <= dateStr && e >= dateStr;
    });

    const dotsHtml = dayEvents.slice(0,3).map(ev => {
      const realm = ev.realm || ev['분야'] || '';
      const cls = getColorClass(realm);
      const title = ev.title || ev['행사명'] || ev['축제명'] || '';
      return `<div class="cal-event-dot ${cls}">${escHtml(title)}</div>`;
    }).join('');

    const moreHtml = dayEvents.length > 3 ? `<div style="font-size:.65rem;color:#9CA3AF">+${dayEvents.length-3}개</div>` : '';

    html += `<div class="cal-day ${isOther?'other-month':''} ${isToday?'today':''}" onclick="showDayEvents('${dateStr}')">
      <div class="cal-day-num">${date}</div>
      ${dotsHtml}${moreHtml}
    </div>`;
  }
  grid.innerHTML = html;

  renderMonthEventList();
}

function showDayEvents(dateStr) {
  const events = calEvents.filter(ev => {
    const s = (ev.startDate || ev['시작일자'] || ev['축제시작일자'] || '').toString().replace(/\D/g,'');
    const e = (ev.endDate || ev['종료일자'] || ev['축제종료일자'] || '').toString().replace(/\D/g,'');
    return s <= dateStr && e >= dateStr;
  });

  const modal = document.getElementById('dayModal');
  const title = document.getElementById('dayModalTitle');
  const list = document.getElementById('dayModalList');
  if (!modal || !title || !list) return;

  const y = dateStr.slice(0,4), m = dateStr.slice(4,6), d = dateStr.slice(6,8);
  title.textContent = `${y}년 ${m}월 ${d}일 행사 (${events.length}건)`;

  if (events.length === 0) {
    list.innerHTML = '<div class="empty">이 날짜에 행사가 없습니다.</div>';
  } else {
    list.innerHTML = events.map(ev => {
      const title2 = ev.title || ev['행사명'] || ev['축제명'] || '';
      const place = ev.place || ev['개최장소'] || ev['장소명'] || '';
      const realm = ev.realm || ev['분야'] || '';
      const cls = getColorClass(realm);
      return `<div class="cal-event-dot ${cls}" style="padding:8px 10px;margin-bottom:6px;border-radius:8px;font-size:.85rem">
        <strong>${escHtml(title2)}</strong>${place ? `<br><span style="font-size:.78rem">${escHtml(place)}</span>` : ''}
      </div>`;
    }).join('');
  }

  modal.classList.add('open');
}

function renderMonthEventList() {
  const ym = `${calYear}${String(calMonth+1).padStart(2,'0')}`;
  const events = calEvents.filter(ev => {
    const s = (ev.startDate || ev['시작일자'] || ev['축제시작일자'] || '').toString().replace(/\D/g,'');
    const e = (ev.endDate || ev['종료일자'] || ev['축제종료일자'] || '').toString().replace(/\D/g,'');
    return s.slice(0,6) === ym || e.slice(0,6) === ym || (s.slice(0,6) < ym && e.slice(0,6) > ym);
  });

  const el = document.getElementById('monthEventList');
  if (!el) return;
  if (events.length === 0) { el.innerHTML = '<div class="empty">이번 달 행사가 없습니다.</div>'; return; }
  el.innerHTML = `<p style="color:var(--text-secondary);font-size:.85rem;margin-bottom:12px">${calYear}년 ${calMonth+1}월 행사 ${events.length}건</p>` +
    `<div class="event-grid">${events.slice(0,12).map(renderEventCardCal).join('')}</div>`;
}

function renderEventCardCal(ev) {
  const title = ev.title || ev['행사명'] || ev['축제명'] || '';
  const place = ev.place || ev['개최장소'] || ev['장소명'] || '';
  const start = ev.startDate || ev['시작일자'] || ev['축제시작일자'] || '';
  const end = ev.endDate || ev['종료일자'] || ev['축제종료일자'] || '';
  const realm = ev.realm || ev['분야'] || '';
  const cls = getColorClass(realm);
  return `<div class="event-card">
    <div class="event-card-title">${escHtml(title)}</div>
    <div class="event-card-meta">
      ${place ? `<span>📍 ${escHtml(place)}</span>` : ''}
      ${start ? `<span>📅 ${formatDate(start)} ~ ${formatDate(end)}</span>` : ''}
    </div>
    <div class="event-card-badges"><span class="badge badge-${cls}">${realm}</span></div>
  </div>`;
}

function prevMonth() {
  calMonth--; if (calMonth < 0) { calMonth = 11; calYear--; }
  renderCalendar();
}
function nextMonth() {
  calMonth++; if (calMonth > 11) { calMonth = 0; calYear++; }
  renderCalendar();
}

function formatDate(d) {
  const s = String(d).replace(/\D/g,'');
  if (s.length === 8) return `${s.slice(0,4)}.${s.slice(4,6)}.${s.slice(6,8)}`;
  return d;
}
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

async function loadCalData() {
  try {
    const [monthRes, festRes] = await Promise.all([
      fetch('../data/culture/this_month.json').catch(() => null),
      fetch('../data/festival.json').catch(() => null)
    ]);

    if (monthRes && monthRes.ok) {
      const d = await monthRes.json();
      calEvents = d.items || d || [];
    }
    if (festRes && festRes.ok) {
      const d = await festRes.json();
      const records = d.records || d || [];
      const mapped = records.map(r => ({
        title: r['축제명'] || '', place: r['개최장소'] || '',
        startDate: (r['축제시작일자'] || '').replace(/-/g,''),
        endDate: (r['축제종료일자'] || '').replace(/-/g,''),
        realm: '축제'
      }));
      calEvents = [...calEvents, ...mapped];
    }
  } catch(e) { console.error(e); }
  renderCalendar();
}

document.addEventListener('DOMContentLoaded', () => {
  loadCalData();
  document.getElementById('prevMonth')?.addEventListener('click', prevMonth);
  document.getElementById('nextMonth')?.addEventListener('click', nextMonth);
  document.querySelector('.modal-close')?.addEventListener('click', () => {
    document.getElementById('dayModal')?.classList.remove('open');
  });
  document.getElementById('dayModal')?.addEventListener('click', e => {
    if (e.target === e.currentTarget) e.currentTarget.classList.remove('open');
  });
});
