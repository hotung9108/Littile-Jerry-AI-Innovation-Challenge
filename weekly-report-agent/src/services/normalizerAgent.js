// NormalizerAgent: nhan RawDailyReport (tu bat ky nguon nao) va chuan hoa lai:
// - Chuan hoa cac gia tri status ve 4 nhom co dinh: Done / In Progress / Blocked / Todo
// - Tach task theo tung nhom de aggregator xu ly de dang
// - Giu lai note/blocker tu do de agent LLM doc hieu ngu canh

const STATUS_MAP = {
  done: 'Done',
  resolved: 'Done',
  closed: 'Done',
  'to do': 'Todo',
  todo: 'Todo',
  open: 'Todo',
  backlog: 'Todo',
  'in progress': 'In Progress',
  'in review': 'In Progress',
  'code review': 'In Progress',
  blocked: 'Blocked',
  'on hold': 'Blocked',
};

function normalizeStatus(rawStatus = '') {
  const key = rawStatus.trim().toLowerCase();
  return STATUS_MAP[key] || 'In Progress'; // fallback an toan
}

/**
 * @param {RawDailyReport} raw
 * @returns NormalizedDailyReport
 */
function normalizeDailyReport(raw) {
  const tasks = (raw.tasks || []).map((t) => ({
    key: t.key,
    title: (t.title || '').trim(),
    type: t.type || 'Task',
    status: normalizeStatus(t.status),
    hours_logged: Number(t.hours_logged) || 0,
    comment: (t.comment || '').trim(),
  }));

  return {
    date: raw.date,
    team: raw.team,
    author: raw.author,
    source: raw.source,
    completed: tasks.filter((t) => t.status === 'Done'),
    in_progress: tasks.filter((t) => t.status === 'In Progress'),
    blocked: tasks.filter((t) => t.status === 'Blocked'),
    todo: tasks.filter((t) => t.status === 'Todo'),
    blockers_free_text: (raw.blockers || []).map((b) => b.trim()).filter(Boolean),
    notes: (raw.notes || '').trim(),
  };
}

function normalizeDailyReports(rawReports) {
  return rawReports.map(normalizeDailyReport);
}

export const normalizerAgent = { normalizeDailyReports, normalizeDailyReport, normalizeStatus };
