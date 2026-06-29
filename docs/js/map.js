// wooafest map.js — 카카오맵 연동

let kakaoMap = null;
let markers = [];

function initMap(containerId, lat, lng, level) {
  if (typeof kakao === 'undefined') return;
  const container = document.getElementById(containerId);
  if (!container) return;
  const opts = {
    center: new kakao.maps.LatLng(lat || 37.5665, lng || 126.9780),
    level: level || 5
  };
  kakaoMap = new kakao.maps.Map(container, opts);

  // 지도 타입 컨트롤
  const mapTypeControl = new kakao.maps.MapTypeControl();
  kakaoMap.addControl(mapTypeControl, kakao.maps.ControlPosition.TOPRIGHT);

  // 줌 컨트롤
  const zoomControl = new kakao.maps.ZoomControl();
  kakaoMap.addControl(zoomControl, kakao.maps.ControlPosition.RIGHT);

  return kakaoMap;
}

function addMarker(lat, lng, title, color) {
  if (!kakaoMap) return;
  const position = new kakao.maps.LatLng(lat, lng);
  const marker = new kakao.maps.Marker({ map: kakaoMap, position, title });
  markers.push(marker);

  if (title) {
    const infowindow = new kakao.maps.InfoWindow({
      content: `<div style="padding:6px 10px;font-size:13px;font-weight:600">${title}</div>`,
      removable: true
    });
    kakao.maps.event.addListener(marker, 'click', () => {
      infowindow.open(kakaoMap, marker);
    });
  }
  return marker;
}

function clearMarkers() {
  markers.forEach(m => m.setMap(null));
  markers = [];
}

function moveToLocation(lat, lng) {
  if (!kakaoMap) return;
  const pos = new kakao.maps.LatLng(lat, lng);
  kakaoMap.setCenter(pos);
}

function openKakaoNavi(lat, lng, name) {
  const url = `https://map.kakao.com/link/to/${encodeURIComponent(name)},${lat},${lng}`;
  window.open(url, '_blank');
}

function initEventDetailMap(lat, lng, title) {
  if (!lat || !lng) return;
  const map = initMap('map', parseFloat(lat), parseFloat(lng), 4);
  if (map) addMarker(parseFloat(lat), parseFloat(lng), title);
}

function initRegionMap(events) {
  if (!events || !events.length) return;
  const map = initMap('map', 36.5, 127.5, 7);
  if (!map) return;

  events.forEach(ev => {
    const lat = parseFloat(ev.lat || ev['위도'] || 0);
    const lng = parseFloat(ev.lng || ev['경도'] || 0);
    const title = ev.title || ev['행사명'] || ev['축제명'] || '';
    if (lat && lng) addMarker(lat, lng, title);
  });
}
