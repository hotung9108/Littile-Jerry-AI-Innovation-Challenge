export const errorHandler = (err, req, res, next) => {
  const statusCode = err.statusCode ?? 500;

  if (statusCode >= 500) {
    console.error('Unhandled error', err);
  }

  res.status(statusCode).json({
    message: statusCode >= 500 ? 'Đã có lỗi xảy ra, vui lòng thử lại sau' : err.message,
  });
};
