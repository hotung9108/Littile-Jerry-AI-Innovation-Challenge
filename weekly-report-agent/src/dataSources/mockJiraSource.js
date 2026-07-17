import { store } from '../data/store.js';

// Pool task "kieu Jira" cho 1 team, tien hoa trang thai qua cac ngay trong tuan
// de mo phong dung nhip lam viec thuc te (To Do -> In Progress -> Done/Blocked).
const TASK_POOL = [
  { key: 'PROJ-101', title: 'Thiet ke schema bang order', type: 'Task' },
  { key: 'PROJ-102', title: 'Fix bug rate limit o API gateway', type: 'Bug' },
  { key: 'PROJ-103', title: 'Xay dung endpoint tao bao cao tuan', type: 'Story' },
  { key: 'PROJ-104', title: 'Tich hop Groq LLM cho agent phan tich', type: 'Story' },
  { key: 'PROJ-105', title: 'Viet unit test cho module normalizer', type: 'Task' },
  { key: 'PROJ-106', title: 'Toi uu query bao cao doanh thu', type: 'Task' },
  { key: 'PROJ-107', title: 'Migrate DB sang connection pool moi', type: 'Task' },
  { key: 'PROJ-108', title: 'Fix loi timeout khi goi Jira webhook', type: 'Bug' },
  { key: 'PROJ-109', title: 'Thiet ke UI trang xem bao cao tuan', type: 'Story' },
  { key: 'PROJ-110', title: 'Review va merge PR module aggregator', type: 'Task' },
];

const AUTHORS = ['Nguyen Van A', 'Tran Thi B', 'Le Van C'];

const BLOCKER_POOL = [
  'Cho DevOps cap quyen truy cap DB staging',
  'Phu thuoc API tu team Payment chua san sang',
  'Thieu tai lieu dac ta tu Product',
  'Moi truong staging bi down tu sang',
];

function pad(n) {
  return String(n).padStart(2, '0');
}

function toDateStr(date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function pickStatusForDay(dayIndex, totalDays, taskIdx) {
  // Mo phong vong doi task: cang ve cuoi tuan cang nhieu task Done,
  // xen ke vai task Blocked de test nhanh "kho khan".
  const progress = dayIndex / (totalDays - 1 || 1);
  const roll = Math.random();

  if (taskIdx % 5 === 3 && progress > 0.4 && roll < 0.5) return 'Blocked';
  if (progress < 0.3) return roll < 0.6 ? 'To Do' : 'In Progress';
  if (progress < 0.7) return roll < 0.55 ? 'In Progress' : 'Done';
  return roll < 0.8 ? 'Done' : 'In Progress';
}

/**
 * Sinh du lieu mock cho 1 tuan lam viec va luu vao store chung.
 * @param {{team?: string, weekStartISO?: string, numDays?: number}} opts
 * @returns {RawDailyReport[]} danh sach report vua sinh ra
 */
function generateMockWeek({ team = 'Backend Team', weekStartISO, numDays = 5 } = {}) {
  const start = weekStartISO ? new Date(weekStartISO) : mostRecentMonday();
  const reports = [];

  for (let d = 0; d < numDays; d++) {
    const date = new Date(start);
    date.setDate(start.getDate() + d);
    const dateStr = toDateStr(date);

    for (const author of AUTHORS) {
      const tasksForAuthor = TASK_POOL.filter((_, i) => i % AUTHORS.length === AUTHORS.indexOf(author));
      const tasks = tasksForAuthor.map((t, i) => ({
        key: t.key,
        title: t.title,
        type: t.type,
        status: pickStatusForDay(d, numDays, i),
        hours_logged: Math.round((Math.random() * 5 + 1) * 10) / 10,
        comment: sampleComment(t, d),
      }));

      const blockers = tasks.some((t) => t.status === 'Blocked')
        ? [BLOCKER_POOL[Math.floor(Math.random() * BLOCKER_POOL.length)]]
        : [];

      reports.push({
        date: dateStr,
        team,
        author,
        source: 'mock',
        tasks,
        blockers,
        notes: sampleDailyNote(author, d),
      });
    }
  }

  store.addDailyReports(reports);
  return reports;
}

function sampleComment(task, dayIndex) {
  const templates = [
    `Da phan tich yeu cau, bat dau code phan chinh cua ${task.key}.`,
    `Tiep tuc hoan thien ${task.key}, du kien xong trong 1-2 ngay toi.`,
    `Da test xong ${task.key}, chuan bi tao PR.`,
    `Dang cho review PR cua ${task.key}.`,
    `Gap vuong mac nho khi lam ${task.key}, dang tim huong xu ly.`,
  ];
  return templates[(dayIndex + task.key.length) % templates.length];
}

function sampleDailyNote(author, dayIndex) {
  const templates = [
    `${author}: hop dau tuan de chia task, khong co gi bat thuong.`,
    `${author}: tap trung xu ly cac task uu tien cao, on dinh.`,
    `${author}: co support them cho ban trong team ve mot van de ky thuat.`,
    `${author}: chuan bi demo cuoi tuan, ra soat lai cac task dang lam.`,
    `${author}: tong ket tuan, chuan bi ban giao cac task da xong.`,
  ];
  return templates[dayIndex % templates.length];
}

function mostRecentMonday() {
  const now = new Date();
  const day = now.getDay(); // 0 = Sunday
  const diff = (day === 0 ? -6 : 1) - day;
  now.setDate(now.getDate() + diff);
  now.setHours(0, 0, 0, 0);
  return now;
}

/**
 * Implement dung contract chung: fetchDailyReports({team, from, to})
 * Neu store chua co du lieu trong khoang [from, to], tu dong sinh mock cho tien test.
 */
async function fetchDailyReports({ team, from, to }) {
  let reports = store.getDailyReports({ team, from, to });
  if (reports.length === 0) {
    generateMockWeek({ team, weekStartISO: from });
    reports = store.getDailyReports({ team, from, to });
  }
  return reports;
}

export const mockJiraSource = {
  fetchDailyReports,
  generateMockWeek, // ham rieng, chi mock source moi co - dung cho endpoint /api/mock/*
};
