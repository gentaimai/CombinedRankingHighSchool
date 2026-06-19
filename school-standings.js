const SWIM_DATA = window.SWIM_RANKING_DATA;

const INDIVIDUAL_POINTS = Array.from({ length: 16 }, (_, index) => 16 - index);
const EVENT_CONFIG = {
  men: {
    code: 1,
    label: "男子学校対抗得点",
    events: [
      ["1|1|2", "50mFr"],
      ["1|1|3", "100mFr"],
      ["1|1|4", "200mFr"],
      ["1|1|5", "400mFr"],
      ["1|1|7", "1500mFr"],
      ["1|2|3", "100mBa"],
      ["1|2|4", "200mBa"],
      ["1|3|3", "100mBr"],
      ["1|3|4", "200mBr"],
      ["1|4|3", "100mFly"],
      ["1|4|4", "200mFly"],
      ["1|5|4", "200mIM"],
      ["1|5|5", "400mIM"],
      ["1|6|5", "4x100mFR"],
      ["1|6|6", "4x200mFR"],
      ["1|7|5", "4x100mMR"],
    ],
  },
  women: {
    code: 2,
    label: "女子学校対抗得点",
    events: [
      ["2|1|2", "50mFr"],
      ["2|1|3", "100mFr"],
      ["2|1|4", "200mFr"],
      ["2|1|5", "400mFr"],
      ["2|1|6", "800mFr"],
      ["2|2|3", "100mBa"],
      ["2|2|4", "200mBa"],
      ["2|3|3", "100mBr"],
      ["2|3|4", "200mBr"],
      ["2|4|3", "100mFly"],
      ["2|4|4", "200mFly"],
      ["2|5|4", "200mIM"],
      ["2|5|5", "400mIM"],
      ["2|6|5", "4x100mFR"],
      ["2|6|6", "4x200mFR"],
      ["2|7|5", "4x100mMR"],
    ],
  },
};

function pointForPosition(position, isRelay) {
  const base = position >= 1 && position <= 16 ? 17 - position : 0;
  return isRelay ? base * 2 : base;
}

function normalizeEventKey(eventKey) {
  return eventKey.split("|").slice(0, 3).join("|");
}

function normalizeRepresentativeName(name) {
  return String(name || "").replace(/\s+/g, "");
}

const REPRESENTATIVE_MARKERS = new Map(
  (window.SWIM_INTERNATIONAL_REPRESENTATIVES || []).map((item) => [
    normalizeRepresentativeName(item.name),
    item.marker,
  ])
);

function isInternationalRepresentative(row) {
  return REPRESENTATIVE_MARKERS.has(normalizeRepresentativeName(row.name));
}

function formatPoints(value) {
  if (!value) return "-";
  return Number.isInteger(value) ? String(value) : value.toFixed(1);
}

function schoolKey(row) {
  return [row.school, row.prefecture || ""].join("|");
}

function normalizeSchoolLabel(rows) {
  const bySchool = new Map();
  for (const row of rows) {
    if (!bySchool.has(row.school)) {
      bySchool.set(row.school, new Set());
    }
    bySchool.get(row.school).add(row.prefecture);
  }
  const labelMap = new Map();
  for (const [school, prefectures] of bySchool.entries()) {
    for (const prefecture of prefectures) {
      const suffix = prefectures.size > 1 ? "(" + prefecture + ")" : "";
      labelMap.set([school, prefecture || ""].join("|"), school + suffix);
    }
  }
  return labelMap;
}

function buildStandings(genderKey) {
  const config = EVENT_CONFIG[genderKey];
  const allowedEventKeys = new Set(config.events.map(([key]) => key));
  const genderRows = SWIM_DATA.rows.filter(
    (row) => row.genderCode === config.code && allowedEventKeys.has(normalizeEventKey(row.eventKey)) && row.school
  );
  const schoolLabels = normalizeSchoolLabel(genderRows);
  const schools = new Map();

  for (const [eventKey] of config.events) {
    const eventRows = genderRows
      .filter((row) => normalizeEventKey(row.eventKey) === eventKey)
      .slice()
      .sort((left, right) => left.timeCentis - right.timeCentis || left.name.localeCompare(right.name, "ja"));
    const scoringRows = eventRows[0]?.isRelay
      ? eventRows
      : eventRows.filter((row) => !isInternationalRepresentative(row));

    let position = 1;
    let index = 0;
    while (index < scoringRows.length) {
      const tieGroup = [scoringRows[index]];
      let nextIndex = index + 1;
      while (nextIndex < scoringRows.length && scoringRows[nextIndex].timeCentis === scoringRows[index].timeCentis) {
        tieGroup.push(scoringRows[nextIndex]);
        nextIndex += 1;
      }

      const spanPositions = Array.from({ length: tieGroup.length }, (_, offset) => position + offset);
      const totalPoints = spanPositions.reduce(
        (sum, currentPosition) => sum + pointForPosition(currentPosition, tieGroup[0].isRelay),
        0
      );
      const awardedPoints = totalPoints / tieGroup.length;

      for (const row of tieGroup) {
        const key = schoolKey(row);
        if (!schools.has(key)) {
          schools.set(key, {
            school: row.school,
            prefecture: row.prefecture,
            displaySchool: schoolLabels.get(key) || row.school,
            totalPoints: 0,
            eventPoints: {},
          });
        }
        const schoolRecord = schools.get(key);
        schoolRecord.eventPoints[eventKey] = (schoolRecord.eventPoints[eventKey] || 0) + awardedPoints;
        schoolRecord.totalPoints += awardedPoints;
      }

      index = nextIndex;
      position += tieGroup.length;
    }
  }

  const standings = [...schools.values()].sort(
    (left, right) => right.totalPoints - left.totalPoints || left.displaySchool.localeCompare(right.displaySchool, "ja")
  );

  let rank = 1;
  for (let index = 0; index < standings.length; index += 1) {
    if (index > 0 && standings[index].totalPoints < standings[index - 1].totalPoints) {
      rank = index + 1;
    }
    standings[index].rank = rank;
  }

  return {
    config,
    standings,
    scoredSchools: standings.filter((item) => item.totalPoints > 0).length,
  };
}

function renderStandingsPage() {
  const genderKey = document.body.dataset.gender === "women" ? "women" : "men";
  const { config, standings, scoredSchools } = buildStandings(genderKey);
  const visibleStandings = standings.filter((item) => item.totalPoints > 0);
  const tableHead = document.getElementById("score-head");
  const tableBody = document.getElementById("score-body");
  const pageTitle = document.getElementById("page-title");
  const pageSubtitle = document.getElementById("page-subtitle");
  const statSchools = document.getElementById("stat-schools");
  const statScored = document.getElementById("stat-scored");
  const statEvents = document.getElementById("stat-events");

  pageTitle.textContent = config.label;
  pageSubtitle.textContent = "公開済みの詳細結果から学校別得点を集計した一覧です。国際大会代表選手は個人種目の得点対象から除外し、下位選手を繰り上げて計算しています。リレー種目は順位通り、その倍点で計算しています。";
  statSchools.textContent = visibleStandings.length;
  statScored.textContent = scoredSchools;
  statEvents.textContent = config.events.length;

  tableHead.innerHTML =
    "<tr><th>順位</th><th>学校</th><th>総合得点</th>" +
    config.events.map(([, label]) => `<th>${label}</th>`).join("") +
    "</tr>";

  tableBody.innerHTML = "";
  for (const school of visibleStandings) {
    const tr = document.createElement("tr");
    const cells = [
      `<td class="rank">${school.rank}</td>`,
      `<td class="school">${school.displaySchool}</td>`,
      `<td class="total">${formatPoints(school.totalPoints)}</td>`,
      ...config.events.map(([eventKey]) => `<td>${formatPoints(school.eventPoints[eventKey] || 0)}</td>`),
    ];
    tr.innerHTML = cells.join("");
    tableBody.appendChild(tr);
  }
}

document.addEventListener("DOMContentLoaded", renderStandingsPage);
