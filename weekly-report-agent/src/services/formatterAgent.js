function section(title, items) {
  const body =
    items.length > 0 ? items.map((x) => `- ${x}`).join('\n') : '- (Khong co du lieu)';
  return `## ${title}\n${body}`;
}

/**
 * @param {{team, weekStart, weekEnd}} meta
 * @param {{highlights, completed, in_progress, blockers, decisions, next_steps}} analysis
 */
function toMarkdown(meta, analysis) {
  return `# Bao cao tuan - ${meta.team}
${meta.weekStart} -> ${meta.weekEnd}

${section('1. Ket qua noi bat', analysis.highlights)}

${section('2. Cong viec da hoan thanh', analysis.completed)}

${section('3. Cong viec dang thuc hien', analysis.in_progress)}

${section('4. Kho khan', analysis.blockers)}

${section('5. Quyet dinh', analysis.decisions)}

${section('6. Cong viec tiep theo', analysis.next_steps)}
`;
}

export const formatterAgent = { toMarkdown };
