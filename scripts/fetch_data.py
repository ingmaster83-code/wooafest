"""
fetch_data.py — 한눈에보는문화정보 API 수집 스크립트
매일 새벽 GitHub Actions에서 실행됨
"""
import os
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
import urllib.request
import urllib.parse

API_KEY = os.environ.get('DATA_GO_KR_API_KEY', '')
CULTURE_API_KEY = os.environ.get('CULTURE_API_KEY', '')
BASE_URL = 'https://apis.data.go.kr/B553457/cultureinfo'
CULTURE_BASE_URL = 'https://api.kcisa.kr/openapi/CNV_060/request'
DATA_DIR = Path(__file__).parent.parent / 'data' / 'culture'
FESTIVAL_JSON_PATH = Path(__file__).parent.parent / 'data' / 'festival.json'

# 전국문화축제표준데이터 (data.go.kr publicDataPk=15013104, 문화체육관광부/한국관광공사, 분기별 갱신)
# www.data.go.kr가 제공하는 공개 다운로드 엔드포인트라 serviceKey 없이도 받을 수 있고,
# api.data.go.kr/apis.data.go.kr 계열과 달리 GitHub Actions IP에서도 정상 동작함
# (wooatrash에서 같은 방식으로 검증됨). festival.json은 2026-06-29 최초 커밋 이후 이 데이터셋을
# 한 번 내려받아 넣기만 하고 자동 갱신 파이프라인이 없어 계속 고정돼 있었음 — 이 함수가 그 갱신을 담당한다.
FESTIVAL_DOWNLOAD_URL = 'https://www.data.go.kr/download/standard.json'
FESTIVAL_PUBLIC_DATA_PK = '15013104'
FESTIVAL_SVC_TABLE_NM = 'tn_pubr_public_cltur_fstvl_svc'
FESTIVAL_FIELD_MAP = {
    'FSTVL_NM': '축제명', 'OPAR': '개최장소', 'FSTVL_START_DATE': '축제시작일자',
    'FSTVL_END_DATE': '축제종료일자', 'FSTVL_CO': '축제내용', 'MNNST_NM': '주관기관명',
    'AUSPC_INSTT_NM': '주최기관명', 'SUPRT_INSTT_NM': '후원기관명', 'PHONE_NUMBER': '전화번호',
    'HOMEPAGE_URL': '홈페이지주소', 'RELATE_INFO': '관련정보', 'RDNMADR': '소재지도로명주소',
    'LNMADR': '소재지지번주소', 'LATITUDE': '위도', 'LONGITUDE': '경도',
    'REFERENCE_DATE': '데이터기준일자', 'INSTT_CODE': '제공기관코드', 'INSTT_NM': '제공기관명',
}

# 마라톤 API (apizoa.com, 인증키 불필요, 무료 요금제 월 1,000회 — 2026-08-25 확인)
# 필터 없이 한 번 호출하면 전체 데이터(280건, nextCursor 없음)가 다 옴 — 별도 페이지네이션 불필요.
MARATHON_API_URL = 'https://apizoa.com/api/v1/marathons'
MARATHON_JSON_PATH = Path(__file__).parent.parent / 'data' / 'marathon.json'

REGIONS = ['서울', '경기', '인천', '부산', '대구', '광주', '대전', '울산', '세종',
           '강원', '충북', '충남', '전북', '전남', '경북', '경남', '제주']

REGION_CODES = {
    '서울': '11', '경기': '41', '인천': '28', '부산': '26', '대구': '27',
    '광주': '29', '대전': '30', '울산': '31', '세종': '36', '강원': '42',
    '충북': '43', '충남': '44', '전북': '45', '전남': '46', '경북': '47',
    '경남': '48', '제주': '50'
}

REALMS = {
    '축제': 'A', '공연': 'B', '전시': 'D', '교육체험': 'G',
    '아동가족': 'E', '체육': 'H', '연극': 'B01', '음악': 'B02',
    '국악': 'B04', '무용': 'B03', '뮤지컬': 'B05', '오페라': 'B06'
}

# 새 문화예술공연(통합) API의 dtype 매핑 (유효값: 연극,뮤지컬,오페라,음악,콘서트,국악,무용,전시,기타)
CULTURE_DTYPES = {
    '전시': ['전시'], '연극': ['연극'], '뮤지컬': ['뮤지컬'],
    '음악': ['음악', '콘서트'], '국악': ['국악'], '무용': ['무용'], '오페라': ['오페라'],
    '아동가족': ['기타'], '교육체험': ['기타'], '체육': ['기타'],
    '공연': ['연극', '뮤지컬', '음악', '콘서트', '무용', '오페라', '국악'],  # 공연 = 여러 dtype 합산
}


def fetch_xml(endpoint, params):
    params['serviceKey'] = API_KEY
    params['numOfRows'] = '100'
    params['pageNo'] = '1'
    url = f"{BASE_URL}/{endpoint}?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        print(f"  ⚠️  fetch 실패 [{endpoint}]: {e}")
        return None


def parse_items(xml_str):
    if not xml_str:
        return []
    try:
        root = ET.fromstring(xml_str)
        items = []
        for item in root.iter('item'):
            d = {}
            for child in item:
                d[child.tag] = child.text or ''
            items.append(d)
        return items
    except ET.ParseError as e:
        print(f"  ⚠️  XML 파싱 오류: {e}")
        return []


def normalize_item(item):
    return {
        'seq': item.get('seq', ''),
        'title': item.get('title', item.get('TITLE', '')),
        'place': item.get('place', item.get('PLACE', '')),
        'startDate': item.get('startDate', item.get('STARTDATE', '')).replace('-', ''),
        'endDate': item.get('endDate', item.get('ENDDATE', '')).replace('-', ''),
        'fee': item.get('price', item.get('PRICE', '')),
        'realm': item.get('realmName', item.get('REALMNAME', '')),
        'area': item.get('areaName', item.get('AREANAME', '')),
        'lat': item.get('lat', item.get('LAT', '')),
        'lng': item.get('lng', item.get('LNG', '')),
        'thumbnail': item.get('thumbnail', item.get('THUMBNAIL', '')),
        'phone': item.get('phone', item.get('PHONE', '')),
        'url': item.get('url', item.get('URL', ''))
    }


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 저장: {path} ({len(data.get('items', []))}건)")


def fetch_period(period_code, out_file, label):
    """this_week.json/this_month.json을 만든다. calendar.js/event.html이 여기서 읽는다.
    예전엔 period2(구API)를 썼는데 stDate/edDate를 사실상 무시하고 pageNo와 무관하게
    항상 같은 고정 표본만 주는 문제가 있어(2026-08-25 확인, 매달 옮겨다녀도 캘린더에 같은
    행사만 보이는 버그였음), 이미 정상 작동하는 문화예술API 기반 by_realm/*.json을 모아
    날짜로 직접 필터링하는 방식으로 대체. 축제는 festival.json에서 calendar.js가 따로
    병합하므로 여기서는 제외해 중복 표시를 막는다."""
    print(f"\n📥 {label} 수집 중... (문화예술API 데이터에서 날짜로 필터링)")
    today = datetime.now()
    if period_code == 'W':
        # 이번주 (월~일)
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
    else:
        # 이번달
        start = today.replace(day=1)
        next_m = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
        end = next_m - timedelta(days=1)
    start_s, end_s = start.strftime('%Y%m%d'), end.strftime('%Y%m%d')

    items = []
    for realm_file in sorted((DATA_DIR / 'by_realm').glob('*.json')):
        if realm_file.stem == '축제':
            continue
        try:
            data = json.loads(realm_file.read_text('utf-8'))
        except Exception:
            continue
        for it in data.get('items', []):
            ev_start = it.get('startDate') or ''
            ev_end = it.get('endDate') or ev_start
            if ev_start and ev_end and ev_start <= end_s and ev_end >= start_s:
                items.append(it)

    save_json(out_file, {
        'updated': datetime.now().isoformat(),
        'period': f"{start.strftime('%Y-%m-%d')}~{end.strftime('%Y-%m-%d')}",
        'total': len(items),
        'items': items
    })


def fetch_by_region():
    print("\n📥 지역별 행사 수집 중...")
    for region, code in REGION_CODES.items():
        print(f"  → {region} ({code})")
        params = {'areaCd': code}
        xml = fetch_xml('area2', params)
        items = [normalize_item(i) for i in parse_items(xml)]

        out = DATA_DIR / 'by_region' / f'{region}.json'
        existing = []
        if out.exists():
            try:
                existing = json.loads(out.read_text('utf-8')).get('items', [])
            except Exception:
                pass

        save_json(out, {
            'updated': datetime.now().isoformat(),
            'region': region,
            'total': len(items),
            'items': items if items else existing
        })
        time.sleep(0.5)


def fetch_culture_xml(params):
    params['serviceKey'] = CULTURE_API_KEY
    params.setdefault('numOfRows', '100')
    params.setdefault('pageNo', '1')
    url = CULTURE_BASE_URL + '?' + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8')
    except Exception as e:
        print(f"  ⚠️  culture API fetch 실패: {e}")
        return None


def normalize_culture_item(item, realm):
    import re as _re
    raw_period = item.get('eventPeriod', '')
    start, end = '', ''
    if '~' in raw_period:
        parts = raw_period.split('~')
        start = parts[0].strip().replace('-', '').replace(' ', '')
        end = parts[1].strip().replace('-', '').replace(' ', '')
    raw_desc = item.get('description', '')
    content = _re.sub(r'<[^>]+>', '', raw_desc).strip() if raw_desc else ''
    return {
        'seq': '',
        'title': item.get('title', ''),
        'place': item.get('eventSite', ''),
        'startDate': start,
        'endDate': end,
        'fee': item.get('charge', ''),
        'realm': realm,
        'area': '',
        'lat': '',
        'lng': '',
        'thumbnail': item.get('imageObject', ''),
        'phone': item.get('contactPoint', ''),
        'url': item.get('url', ''),
        'content': content
    }


def fetch_by_realm():
    print("\n📥 분야별 행사 수집 중...")
    year = str(datetime.now().year)

    # 기존 API로 축제만 수집
    for realm in ['축제']:
        code = REALMS[realm]
        print(f"  → {realm} (기존 API)")
        params = {'realmCode': code}
        xml = fetch_xml('realm2', params)
        items = [normalize_item(i) for i in parse_items(xml)]
        out = DATA_DIR / 'by_realm' / f'{realm}.json'
        existing = []
        if out.exists():
            try:
                existing = json.loads(out.read_text('utf-8')).get('items', [])
            except Exception:
                pass
        save_json(out, {'updated': datetime.now().isoformat(), 'realm': realm, 'total': len(items), 'items': items if items else existing})
        time.sleep(0.5)

    if not CULTURE_API_KEY:
        print("  ⚠️  CULTURE_API_KEY 없음, 공연/전시 분야 수집 건너뜀")
        return

    # 새 API로 공연/전시 등 수집
    done_dtypes = {}
    for realm, dtypes in CULTURE_DTYPES.items():
        print(f"  → {realm} (문화예술API, dtype={dtypes})")
        items = []
        for dtype in dtypes:
            if dtype not in done_dtypes:
                params = {'dtype': dtype, 'title': year, 'numOfRows': '200'}
                xml = fetch_culture_xml(params)
                raw = parse_items(xml)
                done_dtypes[dtype] = [normalize_culture_item(i, dtype) for i in raw]
                time.sleep(0.3)
            items += done_dtypes[dtype]
        out = DATA_DIR / 'by_realm' / f'{realm}.json'
        existing = []
        if out.exists():
            try:
                existing = json.loads(out.read_text('utf-8')).get('items', [])
            except Exception:
                pass
        save_json(out, {'updated': datetime.now().isoformat(), 'realm': realm, 'total': len(items), 'items': items if items else existing})
        time.sleep(0.3)


def fetch_festival_standard_dataset():
    """전국문화축제표준데이터를 받아 festival.json으로 저장 (모듈 상단 주석 참고)."""
    print("\n📥 전국문화축제표준데이터 수집 중...")
    all_records = []
    page = 1
    per_page = 5000
    while True:
        params = [('publicDataPk', FESTIVAL_PUBLIC_DATA_PK)]
        # INSTT_CODE/INSTT_NM은 colNmList에 넣으면 서버가 빈 응답을 줌(원인불명) —
        # 요청 안 해도 응답에 자동 포함되므로 여기선 빼고 요청한다
        params += [('colNmList', c) for c in FESTIVAL_FIELD_MAP if c not in ('INSTT_CODE', 'INSTT_NM')]
        params += [
            ('perPage', per_page),
            ('page', page),
            ('svcTableNm', FESTIVAL_SVC_TABLE_NM),
            ('totalCount', '999999'),
        ]
        url = FESTIVAL_DOWNLOAD_URL + '?' + urllib.parse.urlencode(params)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                items = json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            print(f"  ⚠️  festival 표준데이터셋 fetch 실패: {e}")
            break

        if not items:
            break

        for it in items:
            record = {}
            for api_key, kor_key in FESTIVAL_FIELD_MAP.items():
                v = it.get(api_key, '')
                record[kor_key] = '' if v is None or v == 'null' else v
            all_records.append(record)

        print(f"  {page}페이지 완료 (누적 {len(all_records)}건)")
        if len(items) < per_page:
            break
        page += 1
        time.sleep(0.3)

    if not all_records:
        print("  ⚠️  0건 수집됨 — 기존 festival.json을 그대로 둠")
        return

    fields = [{'id': kor} for kor in FESTIVAL_FIELD_MAP.values()]
    FESTIVAL_JSON_PATH.write_text(
        json.dumps({'fields': fields, 'records': all_records}, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f"  ✅ 저장: {FESTIVAL_JSON_PATH} ({len(all_records)}건)")


def fetch_marathon_data():
    """apizoa.com 마라톤 API를 받아 marathon.json으로 저장 (모듈 상단 주석 참고)."""
    print("\n📥 마라톤 대회 데이터 수집 중...")
    req = urllib.request.Request(MARATHON_API_URL, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"  ⚠️  마라톤 API fetch 실패: {e}")
        return

    items = body.get('data', [])
    if not items:
        print("  ⚠️  0건 수집됨 — 기존 marathon.json을 그대로 둠")
        return

    MARATHON_JSON_PATH.write_text(
        json.dumps({'updated': datetime.now().isoformat(), 'total': len(items), 'items': items}, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    print(f"  ✅ 저장: {MARATHON_JSON_PATH} ({len(items)}건)")


if __name__ == '__main__':
    print("🎪 wooafest 데이터 수집 시작")
    print(f"   시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not API_KEY:
        print("⚠️  DATA_GO_KR_API_KEY 환경변수가 없습니다. 테스트 모드로 실행합니다.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / 'by_region').mkdir(exist_ok=True)
    (DATA_DIR / 'by_realm').mkdir(exist_ok=True)

    fetch_by_region()
    fetch_by_realm()
    fetch_festival_standard_dataset()
    fetch_marathon_data()

    # this_week/this_month은 위 by_realm/*.json을 날짜로 필터링해서 만들므로 반드시 이후에 실행
    fetch_period('W', DATA_DIR / 'this_week.json', '이번주 행사')
    fetch_period('M', DATA_DIR / 'this_month.json', '이번달 행사')

    print("\n✅ 데이터 수집 완료!")
