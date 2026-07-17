import { v4 as uuidv4 } from 'uuid';
import { getDailyReportSource } from '../dataSources/dailyReportSource.js';
import { normalizerAgent } from './normalizerAgent.js';
import { aggregatorAgent } from './aggregatorAgent.js';
import { analystAgent } from './analystAgent.js';
import { formatterAgent } from './formatterAgent.js';
import { store } from '../data/store.js';

/**
 * Chay toan bo pipeline agent de tao bao cao tuan:
 *   1. CollectorAgent  -> lay RawDailyReport tu data source (mock hoac Jira that)
 *   2. NormalizerAgent -> chuan hoa status, tach completed/in_progress/blocked/todo
 *   3. AggregatorAgent -> gop ca tuan, khu trung task theo key
 *   4. AnalystAgent    -> goi Groq LLM de sinh 6 muc bao cao
 *   5. FormatterAgent  -> xuat ban Markdown de hien thi/gui di
 *
 * @param {{team: string, weekStart: string, weekEnd: string}} params
 */
async function generateWeeklyReport({ team, weekStart, weekEnd }) {
  if (!team || !weekStart || !weekEnd) {
    throw new Error('Thieu tham so: can co team, weekStart, weekEnd (YYYY-MM-DD)');
  }

  // 1) Collector
  const source = getDailyReportSource();
  const rawReports = await source.fetchDailyReports({ team, from: weekStart, to: weekEnd });

  if (rawReports.length === 0) {
    throw new Error(`Khong tim thay bao cao hang ngay nao cho team "${team}" trong khoang ${weekStart} -> ${weekEnd}`);
  }

  // 2) Normalizer
  const normalized = normalizerAgent.normalizeDailyReports(rawReports);

  // 3) Aggregator
  const aggregate = aggregatorAgent.aggregateWeek(normalized, { team, weekStart, weekEnd });

  // 4) Analyst (Groq LLM, co fallback mock khi MOCK_LLM=true)
  const analysis = await analystAgent.analyzeWeek(aggregate);

  // 5) Formatter
  const markdown = formatterAgent.toMarkdown({ team, weekStart, weekEnd }, analysis);

  const report = {
    id: uuidv4(),
    team,
    weekStart,
    weekEnd,
    generatedAt: new Date().toISOString(),
    stats: aggregate.stats,
    sections: analysis,
    markdown,
    rawReportsCount: rawReports.length,
  };

  store.saveWeeklyReport(report);
  return report;
}

export const agentWorkflow = { generateWeeklyReport };
