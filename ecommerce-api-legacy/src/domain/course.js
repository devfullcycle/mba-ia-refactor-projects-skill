'use strict';

const { NotFoundError } = require('./errors');

function assertActiveCourse(course) {
    if (!course || Number(course.active) !== 1) {
        throw new NotFoundError('Curso não encontrado');
    }
    return course;
}

module.exports = { assertActiveCourse };
