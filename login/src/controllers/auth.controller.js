import * as authService from '../services/auth.service.js';
import { HttpError } from '../utils/httpError.js';

export const login = async (req, res) => {
  const { email, password } = req.body ?? {};

  if (typeof email !== 'string' || typeof password !== 'string' || !email.trim() || !password) {
    throw new HttpError(400, 'Thiếu email hoặc password');
  }

  const result = await authService.login({ email, password });
  res.json(result);
};
