// Adapter goi Jira That (Jira Cloud REST API v3).
// Day la phan ban se dung THAY the cho mockJiraSource khi co Jira that.
// Chi can set DATA_SOURCE=jira trong .env va dien du bien JIRA_* ben duoi.
//
// Cac bien can trong .env:
//   JIRA_BASE_URL   vd: https://your-domain.atlassian.net
//   JIRA_EMAIL      email tai khoan Jira dung de goi API
//   JIRA_API_TOKEN  tao tai https://id.atlassian.com/manage-profile/security/api-tokens
//   JIRA_PROJECT_KEY  vd: PROJ
//   JIRA_JQL_EXTRA  (tuy chon) dieu kien JQL bo sung, vd: 'AND assignee in (...)'

function getEnv() {
  return {
    baseUrl: process.env.JIRA_BASE_URL,
    email: process.env.JIRA_EMAIL,
    apiToken: process.env.JIRA_API_TOKEN,
    projectKey: process.env.JIRA_PROJECT_KEY,
    extraJql: process.env.JIRA_JQL_EXTRA || '',
  };
}

function authHeader(email, apiToken) {
  const token = Buffer.from(`${email}:${apiToken}`).toString('base64');
  return `Basic ${token}`;
}

/**
 * Goi Jira /rest/api/3/search de lay cac issue duoc cap nhat trong khoang [from, to],
 * roi bien doi changelog cua tung issue thanh cac RawDailyReport theo dung format
 * chung (xem CONTRACT.md), gom nhom theo (ngay, nguoi thuc hien).
 */
async function fetchDailyReports({ team, from, to }) {
  const { baseUrl, email, apiToken, projectKey, extraJql } = getEnv();

  if (!baseUrl || !email || !apiToken || !projectKey) {
    throw new Error(
      'Thieu cau hinh Jira that (JIRA_BASE_URL / JIRA_EMAIL / JIRA_API_TOKEN / JIRA_PROJECT_KEY). ' +
        'Dien du vao .env roi thu lai, hoac dung DATA_SOURCE=mock de test.'
    );
  }

  const jql =
    `project = "${projectKey}" AND updated >= "${from}" AND updated <= "${to}"` +
    (extraJql ? ` ${extraJql}` : '');

  const url = new URL(`${baseUrl}/rest/api/3/search`);
  url.searchParams.set('jql', jql);
  url.searchParams.set('maxResults', '100');
  url.searchParams.set('fields', 'summary,status,issuetype,assignee,updated,worklog,comment');
  url.searchParams.set('expand', 'changelog');

  const res = await fetch(url, {
    headers: {
      Authorization: authHeader(email, apiToken),
      Accept: 'application/json',
    },
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`Jira API loi ${res.status}: ${body}`);
  }

  const data = await res.json();
  return transformIssuesToDailyReports(data.issues || [], team);
}

/**
 * Gom cac issue Jira thanh cac RawDailyReport theo (ngay cap nhat, assignee).
 * Day la logic "best-effort": mot doi thuc te co the muon doc them tu changelog
 * de biet chinh xac ngay chuyen trang thai, hoac tu Tempo/worklog de lay so gio.
 */
function transformIssuesToDailyReports(issues, team) {
  const byKey = new Map(); // "date::author" -> RawDailyReport

  for (const issue of issues) {
    const assignee = issue.fields.assignee?.displayName || 'Chua giao';
    const dateStr = (issue.fields.updated || '').slice(0, 10); // "YYYY-MM-DD"
    const mapKey = `${dateStr}::${assignee}`;

    if (!byKey.has(mapKey)) {
      byKey.set(mapKey, {
        date: dateStr,
        team: team || 'Unknown Team',
        author: assignee,
        source: 'jira',
        tasks: [],
        blockers: [],
        notes: '',
      });
    }

    const dailyReport = byKey.get(mapKey);
    const lastComment = issue.fields.comment?.comments?.slice(-1)[0];

    dailyReport.tasks.push({
      key: issue.key,
      title: issue.fields.summary,
      status: issue.fields.status?.name || 'Unknown',
      type: issue.fields.issuetype?.name || 'Task',
      hours_logged: sumWorklogHours(issue.fields.worklog?.worklogs),
      comment: extractPlainText(lastComment?.body) || '',
    });

    if ((issue.fields.status?.name || '').toLowerCase().includes('block')) {
      dailyReport.blockers.push(`${issue.key}: ${issue.fields.summary}`);
    }
  }

  return Array.from(byKey.values());
}

function sumWorklogHours(worklogs = []) {
  const totalSeconds = worklogs.reduce((sum, w) => sum + (w.timeSpentSeconds || 0), 0);
  return Math.round((totalSeconds / 3600) * 10) / 10;
}

// Jira comment body la Atlassian Document Format (ADF), rut gon lay text thuan.
function extractPlainText(adfNode) {
  if (!adfNode || typeof adfNode !== 'object') return '';
  let text = '';
  function walk(node) {
    if (!node) return;
    if (node.type === 'text' && node.text) text += node.text + ' ';
    if (Array.isArray(node.content)) node.content.forEach(walk);
  }
  walk(adfNode);
  return text.trim();
}

export const jiraSource = { fetchDailyReports };
