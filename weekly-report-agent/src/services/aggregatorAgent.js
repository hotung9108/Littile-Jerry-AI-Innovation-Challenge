// AggregatorAgent: gop nhieu NormalizedDailyReport (nhieu ngay, nhieu author)
// thanh 1 buc tranh tong the cua ca tuan, khu trung task theo key (lay trang thai
// moi nhat theo ngay), de lam input "sach" cho AnalystAgent (Groq LLM).

function latestStatusByTaskKey(normalizedReports) {
  const byKey = new Map(); // key -> { ...task, date, author, lastStatus }

  // Sap xep theo ngay tang dan de "de sau ghi de truoc" = luon la trang thai moi nhat
  const sorted = [...normalizedReports].sort((a, b) => a.date.localeCompare(b.date));

  for (const day of sorted) {
    const allTasks = [...day.completed, ...day.in_progress, ...day.blocked, ...day.todo];
    for (const t of allTasks) {
      byKey.set(t.key, {
        ...t,
        date: day.date,
        author: day.author,
      });
    }
  }
  return byKey;
}

/**
 * @param {NormalizedDailyReport[]} normalizedReports
 * @returns WeeklyAggregate
 */
function aggregateWeek(normalizedReports, { team, weekStart, weekEnd }) {
  const latestByKey = latestStatusByTaskKey(normalizedReports);
  const allLatestTasks = Array.from(latestByKey.values());

  const completed = allLatestTasks.filter((t) => t.status === 'Done');
  const inProgress = allLatestTasks.filter((t) => t.status === 'In Progress');
  const blocked = allLatestTasks.filter((t) => t.status === 'Blocked');
  const todo = allLatestTasks.filter((t) => t.status === 'Todo');

  const totalHours = allLatestTasks.reduce((sum, t) => sum + (t.hours_logged || 0), 0);

  const freeTextBlockers = normalizedReports.flatMap((d) =>
    d.blockers_free_text.map((b) => ({ date: d.date, author: d.author, text: b }))
  );

  const dailyNotes = normalizedReports
    .filter((d) => d.notes)
    .map((d) => ({ date: d.date, author: d.author, notes: d.notes }));

  const authors = Array.from(new Set(normalizedReports.map((d) => d.author)));

  return {
    team,
    weekStart,
    weekEnd,
    authors,
    stats: {
      total_tasks: allLatestTasks.length,
      completed_count: completed.length,
      in_progress_count: inProgress.length,
      blocked_count: blocked.length,
      todo_count: todo.length,
      total_hours_logged: Math.round(totalHours * 10) / 10,
    },
    completed,
    in_progress: inProgress,
    blocked,
    todo,
    free_text_blockers: freeTextBlockers,
    daily_notes: dailyNotes,
  };
}

export const aggregatorAgent = { aggregateWeek };
