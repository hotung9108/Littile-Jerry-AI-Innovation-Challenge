import express from 'express';
import cors from 'cors';
import { config } from './config.js';
import { router as reportRoutes } from './routes/reportRoutes.js';

const app = express();

app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
  res.json({
    status: 'ok',
    dataSource: process.env.DATA_SOURCE || 'mock',
    mockLlm: config.mockLlm,
    groqModel: config.groq.model,
  });
});

app.use('/api', reportRoutes);

app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

app.listen(config.port, () => {
  console.log(`Weekly Report Agent dang chay tai http://localhost:${config.port}`);
  console.log(`Data source: ${process.env.DATA_SOURCE || 'mock'} | Mock LLM: ${config.mockLlm}`);
});
