// In-memory "database". Trong production co the thay bang Postgres/Mongo,
// interface ben ngoai (add/get) giu nguyen nen phan con lai cua app khong doi.

const state = {
  dailyReports: [], // raw daily reports (schema: xem CONTRACT.md)
  weeklyReports: [], // ket qua da sinh ra boi agent workflow
};

function addDailyReports(reports) {
  for (const r of reports) {
    // Ghi de neu da co report cung team + author + date (idempotent theo ngay)
    const idx = state.dailyReports.findIndex(
      (x) => x.team === r.team && x.author === r.author && x.date === r.date
    );
    if (idx >= 0) state.dailyReports[idx] = r;
    else state.dailyReports.push(r);
  }
  return reports;
}

function getDailyReports({ team, from, to }) {
  return state.dailyReports.filter((r) => {
    if (team && r.team !== team) return false;
    if (from && r.date < from) return false;
    if (to && r.date > to) return false;
    return true;
  });
}

function saveWeeklyReport(report) {
  state.weeklyReports.push(report);
  return report;
}

function getWeeklyReportById(id) {
  return state.weeklyReports.find((r) => r.id === id) || null;
}

function listWeeklyReports({ team } = {}) {
  return state.weeklyReports.filter((r) => !team || r.team === team);
}

export const store = {
  addDailyReports,
  getDailyReports,
  saveWeeklyReport,
  getWeeklyReportById,
  listWeeklyReports,
};
