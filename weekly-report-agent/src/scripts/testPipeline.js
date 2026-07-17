import { mockJiraSource } from '../dataSources/mockJiraSource.js';
import { agentWorkflow } from '../services/agentWorkflow.js';

async function main() {
  const team = 'Backend Team';
  const weekStartISO = '2026-07-13'; // Thu Hai

  console.log('== 1. Sinh mock daily reports cho tuan ==');
  const raw = mockJiraSource.generateMockWeek({ team, weekStartISO, numDays: 5 });
  console.log(`Da sinh ${raw.length} daily report (3 nguoi x 5 ngay)`);
  console.log(JSON.stringify(raw[0], null, 2));

  console.log('\n== 2-5. Chay agent workflow: normalize -> aggregate -> analyze (Groq/mock) -> format ==');
  const report = await agentWorkflow.generateWeeklyReport({
    team,
    weekStart: '2026-07-13',
    weekEnd: '2026-07-17',
  });

  console.log('\n--- STATS ---');
  console.log(report.stats);

  console.log('\n--- MARKDOWN ---\n');
  console.log(report.markdown);
}

main().catch((err) => {
  console.error('Loi:', err);
  process.exit(1);
});
