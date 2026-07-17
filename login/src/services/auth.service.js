import bcrypt from 'bcryptjs';
import { findUserByEmail } from '../repositories/user.repository.js';
import { signAccessToken } from '../lib/jwt.js';
import { HttpError } from '../utils/httpError.js';

const INVALID_CREDENTIALS = 'Email hoặc mật khẩu không đúng';

export const login = async ({ email, password }) => {
  const normalizedEmail = email.trim().toLowerCase();
  const user = await findUserByEmail(normalizedEmail);

  if (!user || !(await bcrypt.compare(password, user.password))) {
    throw new HttpError(401, INVALID_CREDENTIALS);
  }

  const token = signAccessToken({ sub: user.id, email: user.email });
  return { token };
};
