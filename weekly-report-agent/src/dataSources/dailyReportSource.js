import { mockJiraSource } from './mockJiraSource.js';
import { jiraSource } from './jiraSource.js';

/**
 * Doi DATA_SOURCE=jira trong .env de chuyen tu mock sang goi Jira that.
 * Toan bo phan con lai cua app (normalizer, aggregator, agent, routes) khong doi,
 * vi ca 2 adapter deu implement dung 1 ham fetchDailyReports({team, from, to})
 * va tra ve dung cung 1 schema (xem CONTRACT.md).
 */
export function getDailyReportSource() {
  const mode = (process.env.DATA_SOURCE || 'mock').toLowerCase();
  if (mode === 'jira') return jiraSource;
  return mockJiraSource;
}
