import { config } from '../config.js';

/**
 * Goi Groq Chat Completions API (tuong thich OpenAI) va yeu cau tra ve JSON thuan.
 * Model mac dinh: openai/gpt-oss-120b (Groq khuyen nghi thay the llama-3.3-70b-versatile
 * da bi deprecate). Doi qua GROQ_MODEL trong .env neu muon dung model khac.
 */
async function callGroqJson({ systemPrompt, userPrompt }) {
  if (config.mockLlm) {
    return null; // agentWorkflow se tu xu ly fallback mock, khong goi mang
  }

  const res = await fetch(config.groq.baseUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${config.groq.apiKey}`,
    },
    body: JSON.stringify({
      model: config.groq.model,
      temperature: 0.3,
      max_completion_tokens: 2000,
      response_format: { type: 'json_object' },
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
    }),
  });

  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`Groq API loi ${res.status}: ${body}`);
  }

  const data = await res.json();
  const content = data.choices?.[0]?.message?.content;
  if (!content) throw new Error('Groq API tra ve response rong');

  try {
    return JSON.parse(content);
  } catch {
    throw new Error('Khong parse duoc JSON tu Groq response: ' + content.slice(0, 300));
  }
}

export const groqClient = { callGroqJson };
