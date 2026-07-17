import express from 'express';
import { authRouter } from './routes/auth.routes.js';
import { notFound } from './middlewares/notFound.js';
import { errorHandler } from './middlewares/errorHandler.js';

export const app = express();

app.use(express.json());
app.use(authRouter);

app.use(notFound);
app.use(errorHandler);
