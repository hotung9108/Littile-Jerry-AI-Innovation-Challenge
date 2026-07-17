import { Router } from 'express';
import { mockJiraSource } from '../dataSources/mockJiraSource.js';
import { store } from '../data/store.js';
import { agentWorkflow } from '../services/agentWorkflow.js';

export const router = Router();

/**
 * POST /api/mock/generate-week
 * body: { team?, weekStartISO?, numDays? }
 * Sinh du lieu mock kieu Jira cho 1 tuan va luu vao store.
 */
router.post('/mock/generate-week', (req, res) => {
  try {
    const { team, weekStartISO, numDays } = req.body || {};
    const reports = mockJiraSource.generateMockWeek({ team, weekStartISO, numDays });
    res.json({ count: reports.length, reports });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

/**
 * GET /api/daily-reports?team=...&from=YYYY-MM-DD&to=YYYY-MM-DD
 * Xem lai cac raw daily report dang co trong store (du lieu tho, chua qua agent).
 */
router.get('/daily-reports', (req, res) => {
  const { team, from, to } = req.query;
  const reports = store.getDailyReports({ team, from, to });
  res.json({ count: reports.length, reports });
});

/**
 * POST /api/daily-reports
 * Cho phep them thu cong 1 hoac nhieu daily report (vd tu webhook / nguon khac),
 * mien la dung schema trong CONTRACT.md.
 */
router.post('/daily-reports', (req, res) => {
  const body = Array.isArray(req.body) ? req.body : [req.body];
  const saved = store.addDailyReports(body);
  res.status(201).json({ count: saved.length, reports: saved });
});

/**
 * POST /api/weekly-report
 * body: { team, weekStart: "YYYY-MM-DD", weekEnd: "YYYY-MM-DD" }
 * Chay toan bo agent workflow: collector -> normalizer -> aggregator -> analyst (Groq) -> formatter
 */
router.post('/weekly-report', async (req, res) => {
  try {
    const { team, weekStart, weekEnd } = req.body || {};
    const report = await agentWorkflow.generateWeeklyReport({ team, weekStart, weekEnd });
    res.status(201).json(report);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

/**
 * GET /api/weekly-report/:id
 */
router.get('/weekly-report/:id', (req, res) => {
  const report = store.getWeeklyReportById(req.params.id);
  if (!report) return res.status(404).json({ error: 'Khong tim thay bao cao' });
  res.json(report);
});

/**
 * GET /api/weekly-report?team=...
 * Liet ke tat ca bao cao tuan da tao (khong kem markdown day du cho gon)
 */
router.get('/weekly-report', (req, res) => {
  const reports = store
    .listWeeklyReports({ team: req.query.team })
    .map(({ markdown, ...rest }) => rest);
  res.json({ count: reports.length, reports });
});
