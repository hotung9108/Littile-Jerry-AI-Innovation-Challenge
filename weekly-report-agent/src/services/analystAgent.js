import { groqClient } from './groqClient.js';
import { config } from '../config.js';

const SYSTEM_PROMPT = `Ban la mot Engineering Manager Assistant. Nhiem vu cua ban la doc du lieu
tong hop tu Jira trong 1 tuan (da duoc chuan hoa) va viet lai thanh mot bao cao tuan
danh cho stakeholder, bang TIENG VIET, van phong ro rang, ngan gon, huong toi hanh dong.

Luon tra ve DUY NHAT 1 JSON object, KHONG kem giai thich, KHONG markdown, dung dinh dang:
{
  "highlights": string[],       // Ket qua noi bat trong tuan
  "completed": string[],        // Cong viec da hoan thanh (neu co the, ghi kem ma task)
  "in_progress": string[],      // Cong viec dang thuc hien
  "blockers": string[],         // Kho khan / vuong mac dang gap phai
  "decisions": string[],        // Cac quyet dinh ky thuat / nghiep vu da chot trong tuan
  "next_steps": string[]        // Cong viec du kien lam tiep theo
}

Yeu cau:
- Moi phan tu trong mang la 1 cau/gach dau dong, sup vien tong hop tu du lieu, khong bia dat them so lieu.
- Neu mot muc khong co du lieu, tra ve mang rong [] cho muc do, KHONG bo qua key.
- "decisions" neu du lieu khong the hien ro quyet dinh nao, hay suy luan hop ly tu cac
  thay doi trang thai/ghi chu (vd: doi huong xu ly, chon giai phap thay the), neu khong
  co gi de suy luan thi de mang rong.`;

function buildUserPrompt(weeklyAggregate) {
  return `Du lieu tong hop cua team "${weeklyAggregate.team}" tu ${weeklyAggregate.weekStart} den ${weeklyAggregate.weekEnd}:

${JSON.stringify(weeklyAggregate, null, 2)}

Hay phan tich va tra ve JSON theo dung dinh dang da quy dinh.`;
}

/**
 * Fallback template khi chay o che do MOCK_LLM=true (khong goi mang that).
 * Van dua tren du lieu aggregate thuc te, chi khong qua LLM de suy dien van phong.
 */
function mockAnalysis(agg) {
  const fmtTask = (t) => `${t.key} - ${t.title} (${t.author})`;

  return {
    highlights: [
      `Hoan thanh ${agg.stats.completed_count}/${agg.stats.total_tasks} task trong tuan, tong ${agg.stats.total_hours_logged} gio cong.`,
      agg.stats.blocked_count > 0
        ? `Con ${agg.stats.blocked_count} task dang bi block, can uu tien xu ly dau tuan sau.`
        : `Khong co task nao bi block trong tuan, tien do on dinh.`,
    ],
    completed: agg.completed.map(fmtTask),
    in_progress: agg.in_progress.map(fmtTask),
    blockers: [
      ...agg.blocked.map((t) => `${fmtTask(t)}: dang bi block`),
      ...agg.free_text_blockers.map((b) => `${b.date} (${b.author}): ${b.text}`),
    ],
    decisions: deriveDecisionsFromNotes(agg.daily_notes),
    next_steps: agg.todo.map(fmtTask).concat(
      agg.in_progress.length > 0
        ? [`Tiep tuc hoan thien ${agg.in_progress.length} task dang lam do de dong trong tuan toi.`]
        : []
    ),
  };
}

function deriveDecisionsFromNotes(dailyNotes) {
  // Heuristic don gian cho che do mock: liet ke cac ghi chu co ve lien quan den
  // "quyet dinh" (chua duoc AI phan tich sau nhu khi goi that Groq).
  const keywords = ['quyet dinh', 'chot', 'doi huong', 'chuyen sang', 'thay the'];
  const found = dailyNotes.filter((n) => keywords.some((k) => n.notes.toLowerCase().includes(k)));
  return found.map((n) => `${n.date} (${n.author}): ${n.notes}`);
}

/**
 * @param {WeeklyAggregate} weeklyAggregate
 * @returns {Promise<{highlights, completed, in_progress, blockers, decisions, next_steps}>}
 */
async function analyzeWeek(weeklyAggregate) {
  if (config.mockLlm) {
    return mockAnalysis(weeklyAggregate);
  }

  const result = await groqClient.callGroqJson({
    systemPrompt: SYSTEM_PROMPT,
    userPrompt: buildUserPrompt(weeklyAggregate),
  });

  // Dam bao du 6 key ngay ca khi LLM tra ve thieu (phong thu loi)
  const keys = ['highlights', 'completed', 'in_progress', 'blockers', 'decisions', 'next_steps'];
  for (const k of keys) if (!Array.isArray(result[k])) result[k] = [];
  return result;
}

export const analystAgent = { analyzeWeek };
