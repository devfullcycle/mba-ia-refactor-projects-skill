const { run, all } = require('../db');

const create = (userId, courseId) =>
  run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [
    userId,
    courseId,
  ]);

const listByUser = (userId) =>
  all('SELECT id FROM enrollments WHERE user_id = ?', [userId]);

module.exports = { create, listByUser };
