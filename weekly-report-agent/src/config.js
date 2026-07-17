import dotenv from 'dotenv';
dotenv.config();

export const config = {
  port: process.env.PORT || 4000,
  groq: {
    apiKey: process.env.GROQ_API_KEY || '',
    model: process.env.GROQ_MODEL || 'openai/gpt-oss-120b',
    baseUrl: 'https://api.groq.com/openai/v1/chat/completions',
  },
  // Neu khong co API key HOAC MOCK_LLM=true -> dung che do mock (khong goi mang)
  mockLlm: (process.env.MOCK_LLM || 'true').toLowerCase() === 'true' || !process.env.GROQ_API_KEY,
};
