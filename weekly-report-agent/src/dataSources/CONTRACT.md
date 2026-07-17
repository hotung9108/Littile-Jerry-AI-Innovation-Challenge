# Data Source Contract

Moi "data source" (mock hoac Jira that) deu phai implement 1 ham duy nhat:

```js
async function fetchDailyReports({ team, from, to }) -> RawDailyReport[]
```

- `team`: string, ten team/board can loc (co the null = lay tat ca)
- `from`, `to`: string dang "YYYY-MM-DD", khoang ngay can lay bao cao
- Tra ve mang `RawDailyReport`, moi phan tu co dung shape sau (bat ke nguon la mock hay Jira that):

```ts
RawDailyReport {
  date: string;        // "YYYY-MM-DD"
  team: string;        // ten team
  author: string;      // nguoi thuc hien / assignee
  source: "mock" | "jira";
  tasks: Array<{
    key: string;        // vd "PROJ-101"
    title: string;
    status: string;     // "To Do" | "In Progress" | "Done" | "Blocked" (chua chuan hoa)
    type: string;       // "Story" | "Bug" | "Task" | ...
    hours_logged: number;
    comment: string;    // ghi chu rieng cho task nay trong ngay
  }>;
  blockers: string[];   // cac kho khan tu do (khong gan voi 1 task cu the) trong ngay
  notes: string;        // ghi chu tu do / standup note cua ngay
}
```

Vi sao lam vay:
- Toan bo pipeline phia sau (normalizer -> aggregator -> agent LLM) chi lam viec voi
  `RawDailyReport[]`, khong biet va khong quan tam du lieu den tu dau.
- Muon chuyen tu mock sang Jira that: chi can viet 1 file adapter moi implement dung
  ham `fetchDailyReports`, roi doi `DATA_SOURCE=jira` trong `.env`. Khong phai sua
  normalizer/aggregator/groqClient/agentWorkflow/routes.
