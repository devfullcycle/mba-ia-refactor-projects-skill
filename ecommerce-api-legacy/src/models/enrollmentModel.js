const { run } = require('../database/connection');

function create(db, userId, courseId) {
  return run(db, 'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
}

function deleteByUserId(db, userId) {
  return run(db, 'DELETE FROM enrollments WHERE user_id = ?', [userId]);
}

module.exports = { create, deleteByUserId };
