(function () {
  const INTERHIGH_MODE = "__interhigh__";

  function normalizeEventKey(eventKey) {
    return String(eventKey || "").split("|").slice(0, 3).join("|");
  }

  function normalizeName(name) {
    return String(name || "").replace(/\s+/g, "");
  }

  function normalizeSchoolName(school) {
    return String(school || "").trim().replace(/(?:高校|高)$/, "");
  }

  function parseTimeToCentis(value) {
    if (!value || value === "-----") return null;
    const parts = String(value).split(":");
    if (parts.length === 1) {
      const [seconds, centis] = parts[0].split(".");
      return Number(seconds) * 100 + Number(centis);
    }
    const [minutes, rest] = parts;
    const [seconds, centis] = rest.split(".");
    return (Number(minutes) * 60 + Number(seconds)) * 100 + Number(centis);
  }

  function blockNameSet() {
    return new Set((window.INTERHIGH_BLOCKS || []).map((block) => block.name));
  }

  function blockForPrefecture(prefecture) {
    const blocks = window.INTERHIGH_BLOCKS || [];
    if (blockNameSet().has(prefecture)) return prefecture;
    const block = blocks.find((item) => item.prefectures.includes(prefecture));
    return block ? block.name : "";
  }

  function rowSchoolPrefecture(row) {
    return row.schoolPrefecture || row.prefecture || "";
  }

  function blockTournamentCodes(data) {
    return new Set(
      (data.tournaments || [])
        .filter((item) => item.isBlockTournament)
        .map((item) => item.code)
    );
  }

  function standardCentisMap() {
    return new Map(
      Object.entries(window.INTERHIGH_STANDARD_TIMES || {}).map(([key, value]) => [
        normalizeEventKey(key),
        parseTimeToCentis(value),
      ])
    );
  }

  function representativeMarkers() {
    return new Map(
      (window.SWIM_INTERNATIONAL_REPRESENTATIVES || []).map((item) => [
        normalizeName(item.name),
        item.marker,
      ])
    );
  }

  function isInternationalRepresentative(row) {
    return representativeMarkers().has(normalizeName(row.name));
  }

  function isBFinal(row) {
    return String(row.divisionName || "").includes("B");
  }

  function isStandardDivision(row) {
    const name = String(row.divisionName || "");
    if (isBFinal(row)) return false;
    return (
      name.includes("予選") ||
      name.includes("決勝") ||
      name.includes("タイム決勝") ||
      name.includes("スイムオフ")
    );
  }

  function isPodiumDivision(row) {
    const name = String(row.divisionName || "");
    if (isBFinal(row)) return false;
    return name.includes("決勝") || name.includes("タイム決勝");
  }

  function competitorEventKey(row) {
    const block = blockForPrefecture(rowSchoolPrefecture(row)) || blockForPrefecture(row.prefecture);
    const schoolPrefecture = rowSchoolPrefecture(row);
    const school = normalizeSchoolName(row.school);
    const competitor = row.isRelay ? `relay:${school}` : `person:${normalizeName(row.name)}:${school}`;
    return [normalizeEventKey(row.eventKey), block, schoolPrefecture, competitor].join("|");
  }

  function rowSort(left, right) {
    return (
      left.timeCentis - right.timeCentis ||
      -(left.finaPoint || 0) + (right.finaPoint || 0) ||
      String(left.name || "").localeCompare(String(right.name || ""), "ja")
    );
  }

  function allResultRows(data) {
    return data.allRows && data.allRows.length ? data.allRows : data.rows || [];
  }

  function blockResultRows(data) {
    const blockCodes = blockTournamentCodes(data);
    return allResultRows(data).filter((row) => blockCodes.has(row.tournamentCode) && row.timeCentis != null);
  }

  function interhighQualifyingKeys(data) {
    const keys = new Set();
    const standards = standardCentisMap();
    const rows = blockResultRows(data);

    for (const row of rows) {
      const standard = standards.get(normalizeEventKey(row.eventKey));
      if (standard != null && isStandardDivision(row) && row.timeCentis <= standard) {
        keys.add(competitorEventKey(row));
      }
    }

    const podiumGroups = new Map();
    for (const row of rows.filter(isPodiumDivision)) {
      const key = [row.tournamentCode, normalizeEventKey(row.eventKey), row.divisionName].join("|");
      if (!podiumGroups.has(key)) podiumGroups.set(key, []);
      podiumGroups.get(key).push(row);
    }

    for (const groupRows of podiumGroups.values()) {
      groupRows.slice().sort(rowSort).slice(0, 3).forEach((row) => keys.add(competitorEventKey(row)));
    }

    return keys;
  }

  function bestInterhighRows(data, eventKey = "") {
    const normalizedEventKey = normalizeEventKey(eventKey);
    const qualifyingKeys = interhighQualifyingKeys(data);
    const bestRows = new Map();
    for (const row of allResultRows(data)) {
      if (row.timeCentis == null) continue;
      if (normalizedEventKey && normalizeEventKey(row.eventKey) !== normalizedEventKey) continue;
      if (!row.isRelay && isInternationalRepresentative(row)) continue;
      const key = competitorEventKey(row);
      if (!qualifyingKeys.has(key)) continue;
      const current = bestRows.get(key);
      if (!current || rowSort(row, current) < 0) {
        bestRows.set(key, { ...row, school: normalizeSchoolName(row.school), prefecture: rowSchoolPrefecture(row) });
      }
    }
    return [...bestRows.values()].sort(rowSort).map((row, index) => ({ ...row, rank: index + 1 }));
  }

  function relayMembers(row) {
    if (Array.isArray(row.relayMemberDetails) && row.relayMemberDetails.length) {
      return row.relayMemberDetails;
    }
    return String(row.relayMembers || "")
      .split("/")
      .map((name) => name.trim())
      .filter(Boolean)
      .map((name) => ({ name, schoolGrade: "-" }));
  }

  function eventSortKeyFactory(data) {
    const eventOrders = new Map(
      (data.events || []).map((event, index) => [normalizeEventKey(event.eventKey), index])
    );
    return (row) => eventOrders.get(normalizeEventKey(row.eventKey)) ?? 999;
  }

  function shortEventLabel(label) {
    return String(label || "")
      .replace(/^(男子|女子)\s+/, "")
      .replace("フリーリレー", "FR")
      .replace("メドレーリレー", "MR")
      .replace("個人メドレー", "IM")
      .replace("バタフライ", "Fly")
      .replace("平泳ぎ", "Br")
      .replace("背泳ぎ", "Ba")
      .replace("自由形", "Fr");
  }

  function genderLabel(row) {
    return row.genderCode === 1 || row.genderName === "男子" ? "男" : "女";
  }

  function buildInterhighParticipants(data) {
    const eventSortKey = eventSortKeyFactory(data);
    const participants = new Map();

    function ensureParticipant(name, school, grade, gender, prefecture) {
      const normalizedSchool = normalizeSchoolName(school);
      const key = [normalizeName(name), normalizedSchool].join("|");
      if (!participants.has(key)) {
        participants.set(key, {
          name,
          school: normalizedSchool,
          schoolGrade: grade || "-",
          gender,
          prefecture,
          events: new Map(),
        });
      }
      const participant = participants.get(key);
      if ((!participant.schoolGrade || participant.schoolGrade === "-") && grade && grade !== "-") {
        participant.schoolGrade = grade;
      }
      return participant;
    }

    for (const row of bestInterhighRows(data)) {
      const members = row.isRelay ? relayMembers(row) : [{ name: row.name, schoolGrade: row.schoolGrade }];
      for (const member of members) {
        const participant = ensureParticipant(member.name, row.school, member.schoolGrade, genderLabel(row), row.prefecture);
        const key = normalizeEventKey(row.eventKey);
        if (!participant.events.has(key)) {
          participant.events.set(key, {
            key,
            label: shortEventLabel(row.eventLabel),
            sortKey: eventSortKey(row),
          });
        }
      }
    }

    return [...participants.values()].map((participant) => ({
      ...participant,
      eventList: [...participant.events.values()].sort((left, right) => left.sortKey - right.sortKey),
    }));
  }

  window.SWIM_INTERHIGH = {
    INTERHIGH_MODE,
    normalizeEventKey,
    normalizeName,
    normalizeSchoolName,
    parseTimeToCentis,
    blockForPrefecture,
    rowSchoolPrefecture,
    blockTournamentCodes,
    isInternationalRepresentative,
    isStandardDivision,
    isPodiumDivision,
    competitorEventKey,
    rowSort,
    interhighQualifyingKeys,
    bestInterhighRows,
    buildInterhighParticipants,
    shortEventLabel,
    genderLabel,
  };
})();
