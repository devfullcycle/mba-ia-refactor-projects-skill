function presentFinancialReport(courses) {
    return courses.map((course) => ({
        course: course.title,
        revenue: course.revenue,
        students: course.students.map((student) => ({ student: student.name, paid: student.paid })),
    }));
}

module.exports = { presentFinancialReport };
