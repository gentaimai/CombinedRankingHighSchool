#!/usr/bin/env python3
import json
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

API_BASE = "https://result.swim.or.jp/api/v1"
OUTPUT_PATH = Path(__file__).with_name("ranking-data.js")

TOURNAMENTS = [
    {"prefecture": "北海道", "code": "0126311", "name": "第79回北海道高等学校選手権水泳競技大会", "date": "2026-07-11〜2026-07-12", "venue": "NOPPOROヤシマ商会スポーツパーク", "url": "https://result.swim.or.jp/tournament/0126311"},
    {"prefecture": "青森", "code": "0226311", "name": "第79回青森県高等学校総合体育大会水泳競技大会", "date": "2026-05-23〜2026-05-24", "venue": "新青森県総合運動公園マエダアリーナ50mプール", "url": "https://result.swim.or.jp/tournament/0226311"},
    {"prefecture": "岩手", "code": "0326301", "name": "第78回岩手県高等学校総合体育大会水泳競技大会", "date": "2026-06-12〜2026-06-14", "venue": "盛岡市立総合プール", "url": "https://result.swim.or.jp/tournament/0326301"},
    {"prefecture": "宮城", "code": "0426301", "name": "第75回宮城県高校総合体育大会", "date": "2026-06-12〜2026-06-14", "venue": "宮城県総合プール(国際）", "url": "https://result.swim.or.jp/tournament/0426301"},
    {"prefecture": "秋田", "code": "0526305", "name": "第72回秋田県高等学校総合体育大会水泳競技大会", "date": "2026-06-18〜2026-06-20", "venue": "秋田県立総合プール", "url": "https://result.swim.or.jp/tournament/0526305"},
    {"prefecture": "山形", "code": "0626302", "name": "第77回山形県高等学校総合体育大会・水泳競技大会", "date": "2026-06-19〜2026-06-21", "venue": "山形市総合スポーツセンター屋外プール", "url": "https://result.swim.or.jp/tournament/0626302"},
    {"prefecture": "福島", "code": "0726372", "name": "第72回福島県高等学校体育大会水泳競技大会", "date": "2026-06-19〜2026-06-21", "venue": "会津水泳場", "url": "https://result.swim.or.jp/tournament/0726372"},
    {"prefecture": "茨城", "code": "0826312", "name": "第77回関東高校水泳競技大会県予選会兼第75回茨城県高等学校選手権水泳競技大会", "date": "2026-06-20〜2026-06-21", "venue": "茨城県笠松運動公園水泳プール国際A級", "url": "https://result.swim.or.jp/tournament/0826312"},
    {"prefecture": "栃木", "code": "0926301", "name": "第67回 栃木県高等学校総合体育大会 水泳競技大会", "date": "2026-05-29〜2026-05-30", "venue": "日環アリーナ栃木 屋内水泳場", "url": "https://result.swim.or.jp/tournament/0926301"},
    {"prefecture": "群馬", "code": "1026301", "name": "令和8年度第61回群馬県高等学校総合体育大会兼関東高校水泳競技大会群馬県予選会", "date": "2026-06-20〜2026-06-21", "venue": "高崎市浜川プール", "url": "https://result.swim.or.jp/tournament/1026301"},
    {"prefecture": "埼玉", "code": "1126302", "name": "学校総合体育大会 兼 埼玉県高等学校選手権水泳競技大会 兼 関東高等学校選手権水泳競技大会埼玉県予選会", "date": "2026-06-20〜2026-06-22", "venue": "青木町公園総合運動場市民プール", "url": "https://result.swim.or.jp/tournament/1126302"},
    {"prefecture": "千葉", "code": "1226301", "name": "第79回千葉県高等学校総合体育大会水泳競技大会", "date": "2026-06-19〜2026-06-21", "venue": "千葉県国際総合水泳場", "url": "https://result.swim.or.jp/tournament/1226301"},
    {"prefecture": "東京", "code": "1326302", "name": "東京都高等学校選手権水泳競技大会", "date": "2026-06-20〜2026-06-21", "venue": "東京アクアティクスセンターメインプール", "url": "https://result.swim.or.jp/tournament/1326302"},
    {"prefecture": "神奈川", "code": "1426303", "name": "第64回神奈川県高等学校総合体育大会", "date": "2026-06-19〜2026-06-21", "venue": "横浜国際プール　国際", "url": "https://result.swim.or.jp/tournament/1426303"},
    {"prefecture": "山梨", "code": "1526307", "name": "第77回関東高等学校選手権水泳競技大会山梨県予選会 兼 第81回山梨県高等学校水泳競技大会", "date": "2026-06-20〜2026-06-21", "venue": "小瀬スポーツ公園水泳場50Mプール", "url": "https://result.swim.or.jp/tournament/1526307"},
    {"prefecture": "長野", "code": "1626301", "name": "令和8年度長野県高校総合体育大会水泳競技大会", "date": "2026-06-27〜2026-06-28", "venue": "アクアウィング", "url": "https://result.swim.or.jp/tournament/1626301"},
    {"prefecture": "新潟", "code": "1726302", "name": "新潟県高等学校総合体育大会水泳競技大会", "date": "2026-06-17〜2026-06-19", "venue": "ダイエープロビスフェニックスプール", "url": "https://result.swim.or.jp/tournament/1726302"},
    {"prefecture": "富山", "code": "1826311", "name": "第79回富山県高等学校選手権水泳競技大会", "date": "2026-06-14", "venue": "富山県総合体育センタープール", "url": "https://result.swim.or.jp/tournament/1826311"},
    {"prefecture": "石川", "code": "1926301", "name": "第79回石川県高等学校選手権水泳競技大会", "date": "2026-06-13", "venue": "金沢プール", "url": "https://result.swim.or.jp/tournament/1926301"},
    {"prefecture": "福井", "code": "2026301", "name": "福井県高等学校選手権水泳競技大会(兼)福井県中学校春季総合競技大会", "date": "2026-06-13〜2026-06-14", "venue": "福井運動公園水泳場", "url": "https://result.swim.or.jp/tournament/2026301"},
    {"prefecture": "静岡", "code": "2126301", "name": "静岡県高等学校総合体育大会水泳競技", "date": "2026-06-19〜2026-06-21", "venue": "静岡県立水泳場", "url": "https://result.swim.or.jp/tournament/2126301"},
    {"prefecture": "愛知", "code": "2226301", "name": "愛知県高等学校選手権水泳競技大会", "date": "2026-06-27〜2026-06-28", "venue": "クロコくんアリーナ", "url": "https://result.swim.or.jp/tournament/2226301"},
    {"prefecture": "三重", "code": "2326301", "name": "三重県高等学校選手権水泳競技大会", "date": "2026-06-20〜2026-06-21", "venue": "三重交通Ｇ スポーツの杜 鈴鹿水泳場", "url": "https://result.swim.or.jp/tournament/2326301"},
    {"prefecture": "岐阜", "code": "2426301", "name": "岐阜県高等学校総合体育大会水泳競技大会", "date": "2026-06-27〜2026-06-28", "venue": "長良川スイミングプラザ", "url": "https://result.swim.or.jp/tournament/2426301"},
    {"prefecture": "滋賀", "code": "2526302", "name": "滋賀県高校選手権　競泳", "date": "2026-06-13〜2026-06-14", "venue": "インフロニア草津アクアティクスセンター", "url": "https://result.swim.or.jp/tournament/2526302"},
    {"prefecture": "京都", "code": "2626302", "name": "第94回京都府高等学校選手権水泳競技大会　競泳競技", "date": "2026-06-27〜2026-06-28", "venue": "京都市西京極総合運動公園プール（京都アクアリーナ）", "url": "https://result.swim.or.jp/tournament/2626302"},
    {"prefecture": "大阪", "code": "2726301", "name": "大阪高校総合体育大会水泳競技大会中央大会", "date": "2026-06-26〜2026-06-28", "venue": "東和薬品RACTABドーム　メインプール", "url": "https://result.swim.or.jp/tournament/2726301"},
    {"prefecture": "兵庫", "code": "2826301", "name": "2026年度兵庫県高等学校総合体育大会 兼 第79回兵庫県高等学校選手権水泳競技大会 競泳競技", "date": "2026-06-26〜2026-06-28", "venue": "神戸ポートアイランドスポーツセンター", "url": "https://result.swim.or.jp/tournament/2826301"},
    {"prefecture": "奈良", "code": "2926301", "name": "奈良県高等学校総合体育大会　第80回奈良県高等学校選手権水泳競技大会 兼 第80回近畿高等学校選手権水泳競技大会奈良県予選会", "date": "2026-06-26〜2026-06-28", "venue": "スイムピア奈良", "url": "https://result.swim.or.jp/tournament/2926301"},
    {"prefecture": "和歌山", "code": "3026305", "name": "第76回和歌山県高等学校総合体育大会水泳競技大会", "date": "2026-06-11〜2026-06-12", "venue": "秋葉山公園県民水泳場", "url": "https://result.swim.or.jp/tournament/3026305"},
    {"prefecture": "鳥取", "code": "3126301", "name": "第61回鳥取県高等学校総合体育大会　水泳競技（競泳）", "date": "2026-06-13〜2026-06-14", "venue": "鳥取県営東山水泳場屋外50m", "url": "https://result.swim.or.jp/tournament/3126301"},
    {"prefecture": "島根", "code": "3226302", "name": "第64回島根県高等学校総合体育大会　2026年度島根県高等学校選手権水泳競技大会　第74回中国地域高等学校選手権水泳競技大会島根県予選会", "date": "2026-05-30", "venue": "島根県立水泳プール", "url": "https://result.swim.or.jp/tournament/3226302"},
    {"prefecture": "岡山", "code": "3326302", "name": "第65回岡山県高等学校総合体育大会", "date": "2026-06-13〜2026-06-14", "venue": "児島地区公園水泳場", "url": "https://result.swim.or.jp/tournament/3326302"},
    {"prefecture": "広島", "code": "3426392", "name": "第79回広島県高等学校総合体育大会水泳競技の部", "date": "2026-06-06〜2026-06-07", "venue": "広島市総合屋内プール", "url": "https://result.swim.or.jp/tournament/3426392"},
    {"prefecture": "山口", "code": "3526302", "name": "第74回中国高等学校選手権水泳競技大会山口県予選会", "date": "2026-06-13〜2026-06-14", "venue": "ＴＯＫＫＩアクアアリーナ山口", "url": "https://result.swim.or.jp/tournament/3526302"},
    {"prefecture": "香川", "code": "3626301", "name": "第66回 香川県高等学校総合体育大会水泳競技", "date": "2026-06-13〜2026-06-14", "venue": "香川県立総合水泳プール", "url": "https://result.swim.or.jp/tournament/3626301"},
    {"prefecture": "徳島", "code": "3726301", "name": "第66回徳島県高等学校体育大会水泳競技大会兼四国高校予選", "date": "2026-06-14", "venue": "むつみスイミング", "url": "https://result.swim.or.jp/tournament/3726301"},
    {"prefecture": "愛媛", "code": "3826301", "name": "令和8年度 第80回愛媛県高等学校総合体育大会", "date": "2026-06-13〜2026-06-14", "venue": "松山中央公園プール", "url": "https://result.swim.or.jp/tournament/3826301"},
    {"prefecture": "高知", "code": "3926301", "name": "第79回 高知県高等学校体育大会水泳競技(競泳の部）(2025/6/13-14)", "date": "2026-06-13〜2026-06-14", "venue": "くろしおアリーナ", "url": "https://result.swim.or.jp/tournament/3926301"},
    {"prefecture": "福岡", "code": "4026302", "name": "令和8年度福岡県高等学校体育連盟総合体育大会水泳競技選手権大会兼　第74回全九州高等学校水泳競技大会予選会", "date": "2026-06-13〜2026-06-14", "venue": "福岡市立総合西市民プール（25m併用）", "url": "https://result.swim.or.jp/tournament/4026302"},
    {"prefecture": "佐賀", "code": "4126301", "name": "令和8年度佐賀県高校総体水泳競技大会", "date": "2026-05-30〜2026-05-31", "venue": "SAGAサンライズパーク　SAGAアクア（50m）", "url": "https://result.swim.or.jp/tournament/4126301"},
    {"prefecture": "長崎", "code": "4226302", "name": "第78回長崎県高等学校総合体育大会　水泳競技", "date": "2026-06-06〜2026-06-07", "venue": "長崎市民総合プール", "url": "https://result.swim.or.jp/tournament/4226302"},
    {"prefecture": "熊本", "code": "4326313", "name": "熊本県高等学校総合体育大会水泳競技", "date": "2026-05-29〜2026-05-30", "venue": "熊本市総合屋内プール", "url": "https://result.swim.or.jp/tournament/4326313"},
    {"prefecture": "大分", "code": "4426302", "name": "第74回大分県高等学校総合体育大会水泳競技大会", "date": "2026-05-30〜2026-05-31", "venue": "別府市営青山プール", "url": "https://result.swim.or.jp/tournament/4426302"},
    {"prefecture": "宮崎", "code": "4526301", "name": "第53回宮崎県高等学校総合体育大会水泳競技", "date": "2026-05-30〜2026-05-31", "venue": "パーソルアクアパーク宮崎", "url": "https://result.swim.or.jp/tournament/4526301"},
    {"prefecture": "鹿児島", "code": "4626302", "name": "第78回鹿児島県高等学校水泳（競泳）競技大会", "date": "2026-05-28〜2026-05-29", "venue": "鴨池公園水泳プール", "url": "https://result.swim.or.jp/tournament/4626302"},
    {"prefecture": "沖縄", "code": "4726304", "name": "第74回沖縄県高等学校水泳競技大会", "date": "2026-05-30〜2026-05-31", "venue": "奥武山水泳プール50mプール", "url": "https://result.swim.or.jp/tournament/4726304"},
]

PRE_STATUS_NAMES = {"開催前", "エントリー済"}
LIVE_STATUS_NAMES = {"開催中"}
POST_STATUS_NAMES = {"大会終了", "記録未登録", "記録確定"}
RESULT_CLASS_CODES = {0, 3}
TARGET_STYLE_DISTANCES = {
    1: {2, 3, 4, 5, 6, 7},  # 自由形
    2: {3, 4},              # 背泳ぎ
    3: {3, 4},              # 平泳ぎ
    4: {3, 4},              # バタフライ
    5: {4, 5},              # 個人メドレー
    6: {5, 6},              # フリーリレー
    7: {5},                 # メドレーリレー
}


def log(message):
    print(message, flush=True)


def current_timestamp_jst():
    return datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S JST")


def normalize_status(raw_status_name):
    if raw_status_name in PRE_STATUS_NAMES:
        return "競技前"
    if raw_status_name in LIVE_STATUS_NAMES:
        return "競技中"
    if raw_status_name in POST_STATUS_NAMES:
        return "競技終了"
    return raw_status_name or "不明"


def is_short_course_name(waterway_name):
    return waterway_name == "短水路"


def is_target_event(gender_code, style_code, distance_code):
    allowed_distances = TARGET_STYLE_DISTANCES.get(style_code)
    if not allowed_distances or distance_code not in allowed_distances:
        return False
    if style_code == 1 and gender_code == 1 and distance_code == 6:
        return False
    if style_code == 1 and gender_code == 2 and distance_code == 7:
        return False
    return True


def normalize_event_key(event_key):
    return "|".join(str(event_key).split("|")[:3])


def load_existing_dataset():
    if not OUTPUT_PATH.exists():
        return None
    text = OUTPUT_PATH.read_text(encoding="utf-8")
    prefix = "window.SWIM_RANKING_DATA = "
    if not text.startswith(prefix):
        return None
    try:
        return json.loads(text[len(prefix):].rstrip(";\n"))
    except json.JSONDecodeError:
        return None


def load_dataset_from_text(text):
    prefix = "window.SWIM_RANKING_DATA = "
    if not text.startswith(prefix):
        return None
    try:
        return json.loads(text[len(prefix):].rstrip(";\n"))
    except json.JSONDecodeError:
        return None


def load_historical_datasets(limit=8):
    try:
        result = subprocess.run(
            ["git", "log", f"-n{limit}", "--format=%H", "--", "ranking-data.js"],
            capture_output=True,
            text=True,
            check=True,
        )
    except Exception:
        return []
    commits = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    datasets = []
    for commit in commits:
        try:
            content = subprocess.run(
                ["git", "show", f"{commit}:ranking-data.js"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        except Exception:
            continue
        dataset = load_dataset_from_text(content)
        if dataset:
            datasets.append(dataset)
    return datasets


def merge_existing_datasets(datasets):
    candidates = [dataset for dataset in datasets if dataset]
    if not candidates:
        return None

    merged_tournaments = {}
    merged_rows = {}
    merged_all_rows = {}
    best_meta = max(candidates, key=lambda item: (len(item.get("rows", [])), len(item.get("events", []))))

    for dataset in candidates:
        tournament_map = {item["code"]: item for item in dataset.get("tournaments", [])}
        rows_by_tournament = defaultdict(list)
        for row in dataset.get("rows", []):
            rows_by_tournament[row["tournamentCode"]].append(row)
        all_rows_by_tournament = defaultdict(list)
        for row in dataset.get("allRows", []):
            all_rows_by_tournament[row["tournamentCode"]].append(row)

        for code, tournament in tournament_map.items():
            current = merged_tournaments.get(code)
            current_rows = merged_rows.get(code, [])
            current_all_rows = merged_all_rows.get(code, [])
            candidate_rows = rows_by_tournament.get(code, [])
            candidate_all_rows = all_rows_by_tournament.get(code, [])
            current_complete = bool(current and current.get("fetchComplete"))
            candidate_complete = bool(tournament.get("fetchComplete"))

            take_candidate = False
            if current is None:
                take_candidate = True
            elif candidate_all_rows and len(candidate_all_rows) > len(current_all_rows):
                take_candidate = True
            elif candidate_complete and not current_complete:
                take_candidate = True
            elif len(candidate_rows) > len(current_rows):
                take_candidate = True
            elif candidate_complete == current_complete and tournament.get("fetchSucceededSpecCount", 0) > current.get("fetchSucceededSpecCount", 0):
                take_candidate = True

            if take_candidate:
                merged_tournaments[code] = tournament
                merged_rows[code] = candidate_rows
                merged_all_rows[code] = candidate_all_rows

    merged = {
        "generatedAt": best_meta.get("generatedAt"),
        "source": best_meta.get("source"),
        "tournaments": list(merged_tournaments.values()),
        "rows": [row for code in sorted(merged_rows) for row in merged_rows[code]],
        "allRows": [row for code in sorted(merged_all_rows) for row in merged_all_rows[code]],
        "events": best_meta.get("events", []),
    }
    return merged


def api_get(path, params=None, retries=4):
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params, doseq=True)
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    for attempt in range(retries):
        if attempt == 0:
            log(f"  GET {path}")
        else:
            log(f"  RETRY {attempt + 1}/{retries} {path}")
        request = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            body = error.read().decode("utf-8", errors="ignore")
            log(f"  HTTP ERROR {error.code} {path}")
            raise RuntimeError(f"HTTP {error.code} for {url}: {body[:300]}")
        except (TimeoutError, socket.timeout, OSError):
            log(f"  TIMEOUT/NETWORK ERROR {path}")
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise


def fallback_status_from_dates(date_text):
    today = time.strftime("%Y-%m-%d")
    if "〜" in date_text:
        start_date, end_date = date_text.split("〜", 1)
    else:
        start_date = end_date = date_text
    if today < start_date:
        return "競技前", "日程ベース推定"
    if start_date <= today <= end_date:
        return "競技中", "日程ベース推定"
    return "競技終了", "日程ベース推定"


def enrich_tournaments(existing_tournaments=None):
    existing_map = {item["code"]: item for item in (existing_tournaments or [])}
    enriched = []
    for tournament in TOURNAMENTS:
        log(f"[status] {tournament['prefecture']} {tournament['code']}")
        raw_status = ""
        status = ""
        waterway_name = ""
        is_short_course = False
        try:
            detail = api_get(f"/games/{tournament['code']}")
            raw_status = (detail.get("game_status") or {}).get("name", "")
            status = normalize_status(raw_status)
            waterway_name = (detail.get("waterway") or {}).get("name", "")
            is_short_course = is_short_course_name(waterway_name)
            log(f"  status={status} raw={raw_status}")
        except Exception:
            cached = existing_map.get(tournament["code"])
            if cached:
                raw_status = cached.get("statusRaw", "")
                status = cached.get("status", "") or normalize_status(raw_status)
                waterway_name = cached.get("waterwayName", "")
                is_short_course = cached.get("isShortCourse", False)
                log(f"  fallback cached status={status} raw={raw_status}")
            else:
                status, raw_status = fallback_status_from_dates(tournament["date"])
                log(f"  fallback date-based status={status} raw={raw_status}")
        enriched.append(
            {
                **tournament,
                "statusRaw": raw_status,
                "status": status,
                "waterwayName": waterway_name,
                "isShortCourse": is_short_course,
            }
        )
    return enriched


def should_fetch_tournament(tournament, existing_map, existing_rows_by_tournament, existing_all_rows_by_tournament):
    cached = existing_map.get(tournament["code"], {})
    cached_rows = existing_rows_by_tournament.get(tournament["code"], [])
    cached_all_rows = existing_all_rows_by_tournament.get(tournament["code"], [])
    if tournament.get("status") == "競技前":
        return False, "status-pre"
    if tournament.get("status") != "競技終了":
        return False, f"status-{tournament.get('statusRaw') or 'unknown'}"
    if cached_rows and not cached_all_rows:
        return True, "ended-missing-all-rows"
    if cached.get("fetchComplete") and cached_rows:
        return False, "already-complete"
    return True, "ended-incomplete"


def parse_time_to_centis(value):
    if not value or not isinstance(value, str):
        return None
    if any(token in value for token in ["失格", "棄権", "欠場"]):
        return None
    parts = value.split(":")
    try:
        if len(parts) == 1:
            seconds, centis = parts[0].split(".")
            return int(seconds) * 100 + int(centis)
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds, centis = parts[1].split(".")
            return (minutes * 60 + int(seconds)) * 100 + int(centis)
    except ValueError:
        return None
    return None


def event_label(gender_name, style_name, distance_name, relay_name):
    if style_name.endswith("リレー"):
        return f"{gender_name} {relay_name or distance_name}{style_name}"
    return f"{gender_name} {distance_name}{style_name}"


def competitor_key(swimmers):
    if "swimmer_code" in swimmers:
        return f"swimmer:{swimmers['swimmer_code']}"
    team_members = swimmers.get("team_members") or []
    if team_members:
        entry_group = team_members[0].get("entry_group") or {}
        code = entry_group.get("code") or swimmers.get("team_name")
        return f"relay:{code}"
    return None


def competitor_name(swimmers):
    if "swimmer_name" in swimmers:
        return swimmers["swimmer_name"]
    return swimmers.get("team_name", "不明")


def school_name(swimmers):
    if "entry_group" in swimmers:
        return swimmers["entry_group"].get("short_name") or swimmers["entry_group"].get("name")
    team_members = swimmers.get("team_members") or []
    if team_members:
        entry_group = team_members[0].get("entry_group") or {}
        return entry_group.get("short_name") or entry_group.get("name")
    return ""


def school_grade_label(swimmers):
    school_class = swimmers.get("school_class")
    if school_class and school_class.get("school_grade"):
        grade = school_class["school_grade"][0]
        return f"{grade}年" if grade else "-"
    team_members = swimmers.get("team_members") or []
    grades = []
    for member in team_members:
        school_class = member.get("school_class") or {}
        for grade in school_class.get("school_grade") or []:
            if grade:
                grades.append(grade)
    unique = sorted(set(grades))
    if not unique:
        return "-"
    return " / ".join(f"{grade}年" for grade in unique)


def relay_members_label(swimmers):
    team_members = swimmers.get("team_members") or []
    if not team_members:
        return ""
    return " / ".join(member.get("swimmer_name", "") for member in team_members if member.get("swimmer_name"))


def relay_member_details(swimmers):
    details = []
    for member in swimmers.get("team_members") or []:
        name = member.get("swimmer_name")
        if not name:
            continue
        school_class = member.get("school_class") or {}
        grades = school_class.get("school_grade") or []
        grade = grades[0] if grades else ""
        details.append({
            "name": name,
            "schoolGrade": f"{grade}年" if grade else "-",
        })
    return details


def collect_event_specs(game_code):
    try:
        races = api_get(f"/games/{game_code}/races")["data"]
    except Exception:
        log(f"  no races for {game_code}")
        return []
    specs = {}
    for race_day in races:
        for race_gender in race_day.get("race_genders", []):
            gender = race_gender["gender"]
            for held_style in race_gender.get("held_styles", []):
                style = held_style["swimming_style"]
                for held_distance in held_style.get("held_distances", []):
                    distance = held_distance["distance"]
                    if not is_target_event(gender["code"], style["code"], distance["code"]):
                        continue
                    for class_info in held_distance.get("classes", []):
                        class_meta = class_info["class"]
                        if class_meta["code"] not in RESULT_CLASS_CODES:
                            continue
                        for division in class_info.get("race_divisions", []):
                            division_meta = division["division"]
                            key = (
                                gender["code"],
                                style["code"],
                                distance["code"],
                                class_meta["code"],
                                division_meta["code"],
                            )
                            specs[key] = {
                                "gender": gender,
                                "style": style,
                                "distance": distance,
                                "class": class_meta,
                                "division": division_meta,
                            }
    log(f"  collected {len(specs)} event specs for {game_code}")
    return list(specs.values())


def fetch_results_for_event(game_code, spec):
    event_name = event_label(
        spec["gender"]["name"],
        spec["style"]["name"],
        spec["distance"]["name"],
        spec["distance"].get("name_for_relay"),
    )
    log(
        "  fetching "
        f"{game_code} {event_name} "
        f"class={spec['class']['code']} division={spec['division']['code']}"
    )
    path = (
        f"/games/{game_code}/results/genders/{spec['gender']['code']}"
        f"/swimming_styles/{spec['style']['code']}"
        f"/distances/{spec['distance']['code']}"
        f"/classes/{spec['class']['code']}"
        f"/race_divisions/{spec['division']['code']}"
        f"/heats/100"
    )
    try:
        rows = api_get(path)["data"]
        log(f"    results={len(rows)} via heat=100")
        return rows, True
    except Exception:
        log(f"    fallback heats lookup for {game_code} {event_name}")
        heats_path = (
            f"/games/{game_code}/heats/genders/{spec['gender']['code']}"
            f"/swimming_styles/{spec['style']['code']}"
            f"/distances/{spec['distance']['code']}"
            f"/classes/{spec['class']['code']}"
        )
        try:
            heat_info = api_get(heats_path)["data"]
        except Exception:
            log(f"    heats lookup failed for {game_code} {event_name}")
            return [], False
        target_heat = None
        for division in heat_info:
            if division["division"]["code"] == spec["division"]["code"]:
                heats = division.get("heats") or []
                if heats:
                    target_heat = heats[0]
                    break
        if target_heat is None:
            log(f"    no matching heat for {game_code} {event_name}")
            return [], False
        fallback_path = path.rsplit("/", 1)[0] + f"/{target_heat}"
        try:
            rows = api_get(fallback_path)["data"]
            log(f"    results={len(rows)} via heat={target_heat}")
            return rows, True
        except Exception:
            log(f"    fallback result fetch failed for {game_code} {event_name}")
            return [], False


def build_dataset(existing_data=None):
    tournaments = enrich_tournaments((existing_data or {}).get("tournaments"))
    existing_tournament_map = {item["code"]: item for item in (existing_data or {}).get("tournaments", [])}
    existing_rows_by_tournament = defaultdict(list)
    existing_all_rows_by_tournament = defaultdict(list)
    if existing_data:
        for row in existing_data.get("rows", []):
            row["eventKey"] = normalize_event_key(row["eventKey"])
            existing_rows_by_tournament[row["tournamentCode"]].append(row)
        for row in existing_data.get("allRows", []):
            row["eventKey"] = normalize_event_key(row["eventKey"])
            existing_all_rows_by_tournament[row["tournamentCode"]].append(row)
    event_rows = defaultdict(dict)
    all_rows = []
    tournaments_done = 0
    for tournament in tournaments:
        tournaments_done += 1
        log(f"[{tournaments_done}/{len(TOURNAMENTS)}] {tournament['prefecture']} {tournament['code']}")
        specs = collect_event_specs(tournament["code"])
        tournament_best = {}
        tournament_all_rows = []
        cached_rows = existing_rows_by_tournament.get(tournament["code"], [])
        cached_all_rows = existing_all_rows_by_tournament.get(tournament["code"], [])
        for payload in cached_rows:
            dedupe_key = (
                normalize_event_key(payload["eventKey"]),
                payload["name"] + "|" + payload["school"] + "|" + payload["prefecture"],
            )
            tournament_best[dedupe_key] = payload

        fetch_needed, fetch_reason = should_fetch_tournament(
            tournament,
            existing_tournament_map,
            existing_rows_by_tournament,
            existing_all_rows_by_tournament,
        )
        tournament["fetchReason"] = fetch_reason
        tournament["fetchUpdatedAt"] = current_timestamp_jst()
        tournament["targetSpecCount"] = len(specs)
        cached_tournament = existing_tournament_map.get(tournament["code"], {})
        tournament["fetchAttemptedSpecCount"] = cached_tournament.get("fetchAttemptedSpecCount", 0)
        tournament["fetchSucceededSpecCount"] = cached_tournament.get("fetchSucceededSpecCount", 0)
        tournament["fetchFailedSpecCount"] = cached_tournament.get("fetchFailedSpecCount", 0)
        tournament["fetchComplete"] = cached_tournament.get("fetchComplete", False)

        if not specs:
            log(f"  no specs for {tournament['code']}, using cached rows if available")
            tournament["fetchComplete"] = bool(cached_rows)
        elif not fetch_needed:
            log(f"  skip fetch for {tournament['code']} reason={fetch_reason}")
            if tournament["fetchComplete"]:
                tournament["fetchAttemptedSpecCount"] = len(specs)
                tournament["fetchSucceededSpecCount"] = len(specs)
                tournament["fetchFailedSpecCount"] = 0
        else:
            tournament["fetchAttemptedSpecCount"] = 0
            tournament["fetchSucceededSpecCount"] = 0
            tournament["fetchFailedSpecCount"] = 0

        for spec in specs if fetch_needed else []:
            tournament["fetchAttemptedSpecCount"] += 1
            rows, success = fetch_results_for_event(tournament["code"], spec)
            if success:
                tournament["fetchSucceededSpecCount"] += 1
            else:
                tournament["fetchFailedSpecCount"] += 1
            label = event_label(
                spec["gender"]["name"],
                spec["style"]["name"],
                spec["distance"]["name"],
                spec["distance"].get("name_for_relay"),
            )
            event_key = "|".join(
                [
                    str(spec["gender"]["code"]),
                    str(spec["style"]["code"]),
                    str(spec["distance"]["code"]),
                ]
            )
            for row in rows:
                centis = parse_time_to_centis(row.get("result_time"))
                swimmers = row.get("swimmers") or {}
                key = competitor_key(swimmers)
                if centis is None or not key:
                    continue
                dedupe_key = (event_key, key + "|" + tournament["prefecture"])
                payload = {
                    "eventKey": event_key,
                    "eventLabel": label,
                    "genderCode": spec["gender"]["code"],
                    "genderName": spec["gender"]["name"],
                    "styleCode": spec["style"]["code"],
                    "styleName": spec["style"]["name"],
                    "distanceCode": spec["distance"]["code"],
                    "distanceName": spec["distance"]["name"],
                    "isRelay": spec["style"]["name"].endswith("リレー"),
                    "time": row["result_time"],
                    "timeCentis": centis,
                    "name": competitor_name(swimmers),
                    "school": school_name(swimmers),
                    "schoolGrade": school_grade_label(swimmers),
                    "relayMembers": relay_members_label(swimmers),
                    "relayMemberDetails": relay_member_details(swimmers),
                    "prefecture": tournament["prefecture"],
                    "tournamentCode": tournament["code"],
                    "tournamentName": tournament["name"],
                    "tournamentDate": tournament["date"],
                    "venue": tournament["venue"],
                    "tournamentUrl": tournament["url"],
                    "waterwayName": tournament.get("waterwayName", ""),
                    "isShortCourse": tournament.get("isShortCourse", False),
                    "divisionName": spec["division"]["name"],
                    "resultId": row.get("result_id"),
                    "finaPoint": row.get("fina_point"),
                }
                tournament_all_rows.append(dict(payload))
                current = tournament_best.get(dedupe_key)
                if current is None or (centis, -(payload["finaPoint"] or 0)) < (
                    current["timeCentis"],
                    -(current["finaPoint"] or 0),
                ):
                    tournament_best[dedupe_key] = payload

        if fetch_needed:
            tournament["fetchComplete"] = (
                tournament["targetSpecCount"] > 0
                and tournament["fetchSucceededSpecCount"] == tournament["targetSpecCount"]
                and tournament["fetchFailedSpecCount"] == 0
            )
        log(
            f"  tournament {tournament['code']} best rows={len(tournament_best)} "
            f"cached rows={len(cached_rows)} "
            f"attempted={tournament['fetchAttemptedSpecCount']} "
            f"succeeded={tournament['fetchSucceededSpecCount']} "
            f"failed={tournament['fetchFailedSpecCount']} "
            f"complete={tournament['fetchComplete']}"
        )
        source_rows = list(tournament_best.values()) or cached_rows
        source_all_rows = tournament_all_rows if fetch_needed and tournament_all_rows else cached_all_rows
        tournament["resultRowCount"] = len(source_rows)
        tournament["allResultRowCount"] = len(source_all_rows)
        for payload in source_all_rows:
            payload["eventKey"] = normalize_event_key(payload["eventKey"])
            all_rows.append(payload)
        for payload in source_rows:
            payload["eventKey"] = normalize_event_key(payload["eventKey"])
            global_key = payload["name"] + "|" + payload["school"] + "|" + payload["prefecture"]
            existing = event_rows[payload["eventKey"]].get(global_key)
            if existing is None or (payload["timeCentis"], -(payload["finaPoint"] or 0)) < (
                existing["timeCentis"],
                -(existing["finaPoint"] or 0),
            ):
                event_rows[payload["eventKey"]][global_key] = payload

    events = []
    flat_rows = []
    for event_key, row_map in event_rows.items():
        rows = sorted(row_map.values(), key=lambda item: (item["timeCentis"], -(item["finaPoint"] or 0), item["name"]))
        for index, row in enumerate(rows, start=1):
            row["rank"] = index
        if rows:
            first = rows[0]
            events.append(
                {
                    "eventKey": event_key,
                    "eventLabel": first["eventLabel"],
                    "genderCode": first["genderCode"],
                    "genderName": first["genderName"],
                    "styleCode": first["styleCode"],
                    "styleName": first["styleName"],
                    "distanceCode": first["distanceCode"],
                    "distanceName": first["distanceName"],
                    "isRelay": first["isRelay"],
                    "entryCount": len(rows),
                    "bestTime": first["time"],
                }
            )
            flat_rows.extend(rows)

    events.sort(key=lambda item: (item["genderCode"], item["styleCode"], item["distanceCode"]))
    flat_rows.sort(key=lambda item: (item["eventLabel"], item["rank"]))
    all_rows.sort(
        key=lambda item: (
            item["eventLabel"],
            item["prefecture"],
            item["tournamentCode"],
            item["divisionName"],
            item["timeCentis"],
            item["name"],
        )
    )
    return {
        "generatedAt": current_timestamp_jst(),
        "source": "https://result.swim.or.jp/",
        "tournaments": tournaments,
        "events": events,
        "rows": flat_rows,
        "allRows": all_rows,
        "liveTournamentCount": len({row["tournamentCode"] for row in flat_rows}),
        "statusSummary": {
            "競技前": sum(1 for item in tournaments if item["status"] == "競技前"),
            "競技中": sum(1 for item in tournaments if item["status"] == "競技中"),
            "競技終了": sum(1 for item in tournaments if item["status"] == "競技終了"),
        },
        "fetchSummary": {
            "complete": sum(1 for item in tournaments if item.get("fetchComplete")),
            "incomplete": sum(1 for item in tournaments if item.get("targetSpecCount", 0) > 0 and not item.get("fetchComplete")),
            "skipped": sum(1 for item in tournaments if item.get("fetchAttemptedSpecCount", 0) == 0),
        },
    }


def main():
    existing_dataset = merge_existing_datasets([load_existing_dataset(), *load_historical_datasets()])
    dataset = build_dataset(existing_dataset)
    OUTPUT_PATH.write_text(
        "window.SWIM_RANKING_DATA = " + json.dumps(dataset, ensure_ascii=False) + ";\n",
        encoding="utf-8",
    )
    log(f"Wrote {OUTPUT_PATH}")
    log(f"Events: {len(dataset['events'])}")
    log(f"Rows: {len(dataset['rows'])}")
    log(f"All rows: {len(dataset.get('allRows', []))}")


if __name__ == "__main__":
    main()
