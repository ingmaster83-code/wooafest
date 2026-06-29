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
BASE_URL = 'https://apis.data.go.kr/B553457/cultureinfo'
DATA_DIR = Path(__file__).parent.parent / 'data' / 'culture'

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
    print(f"\n📥 {label} 수집 중...")
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

    params = {
        'stDate': start.strftime('%Y%m%d'),
        'edDate': end.strftime('%Y%m%d'),
    }
    xml = fetch_xml('period2', params)
    items = [normalize_item(i) for i in parse_items(xml)]

    existing = []
    if out_file.exists():
        try:
            existing = json.loads(out_file.read_text('utf-8')).get('items', [])
        except Exception:
            pass

    save_json(out_file, {
        'updated': datetime.now().isoformat(),
        'period': f"{start.strftime('%Y-%m-%d')}~{end.strftime('%Y-%m-%d')}",
        'total': len(items),
        'items': items if items else existing
    })
    time.sleep(0.5)


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


def fetch_by_realm():
    print("\n📥 분야별 행사 수집 중...")
    for realm, code in REALMS.items():
        print(f"  → {realm} ({code})")
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

        save_json(out, {
            'updated': datetime.now().isoformat(),
            'realm': realm,
            'total': len(items),
            'items': items if items else existing
        })
        time.sleep(0.5)


if __name__ == '__main__':
    print("🎪 wooafest 데이터 수집 시작")
    print(f"   시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not API_KEY:
        print("⚠️  DATA_GO_KR_API_KEY 환경변수가 없습니다. 테스트 모드로 실행합니다.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / 'by_region').mkdir(exist_ok=True)
    (DATA_DIR / 'by_realm').mkdir(exist_ok=True)

    fetch_period('W', DATA_DIR / 'this_week.json', '이번주 행사')
    fetch_period('M', DATA_DIR / 'this_month.json', '이번달 행사')
    fetch_by_region()
    fetch_by_realm()

    print("\n✅ 데이터 수집 완료!")
