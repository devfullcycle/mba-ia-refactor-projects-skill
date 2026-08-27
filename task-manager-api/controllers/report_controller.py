from flask import jsonify
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import datetime, timezone, timedelta

def summary_report():
    try:
        total_tasks = Task.query.count()
        total_users = User.query.count()
        total_categories = Category.query.count()

        pending = Task.query.filter_by(status='pending').count()
        in_progress = Task.query.filter_by(status='in_progress').count()
        done = Task.query.filter_by(status='done').count()
        cancelled = Task.query.filter_by(status='cancelled').count()

        p1 = Task.query.filter_by(priority=1).count()
        p2 = Task.query.filter_by(priority=2).count()
        p3 = Task.query.filter_by(priority=3).count()
        p4 = Task.query.filter_by(priority=4).count()
        p5 = Task.query.filter_by(priority=5).count()

        # Fix Deprecated: datetime.utcnow -> timezone-aware now(timezone.utc)
        now_utc = datetime.now(timezone.utc)
        now_naive = now_utc.replace(tzinfo=None)

        all_tasks = Task.query.all()
        overdue_count = 0
        overdue_list = []
        for t in all_tasks:
            if t.due_date:
                # To compare, both must be tz-aware or both naive. Task's due_date is naive so let's convert to tz-aware if needed, or make sure we match
                # Let's compare t.due_date with naive now_utc.replace(tzinfo=None) or match database schema
                due_naive = t.due_date.replace(tzinfo=None) if t.due_date.tzinfo else t.due_date
                if due_naive < now_naive:
                    if t.status != 'done' and t.status != 'cancelled':
                        overdue_count += 1
                        overdue_list.append({
                            'id': t.id,
                            'title': t.title,
                            'due_date': str(t.due_date),
                            'days_overdue': (now_naive - due_naive).days
                        })

        seven_days_ago = now_naive - timedelta(days=7)
        recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()

        recent_done = Task.query.filter(
            Task.status == 'done',
            Task.updated_at >= seven_days_ago
        ).count()

        users = User.query.all()
        user_stats = []
        for u in users:
            user_tasks = Task.query.filter_by(user_id=u.id).all()
            total = len(user_tasks)
            completed = 0
            for t in user_tasks:
                if t.status == 'done':
                    completed += 1
            user_stats.append({
                'user_id': u.id,
                'user_name': u.name,
                'total_tasks': total,
                'completed_tasks': completed,
                'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0
            })

        report = {
            'generated_at': str(now_utc),
            'overview': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'total_categories': total_categories,
            },
            'tasks_by_status': {
                'pending': pending,
                'in_progress': in_progress,
                'done': done,
                'cancelled': cancelled,
            },
            'tasks_by_priority': {
                'critical': p1,
                'high': p2,
                'medium': p3,
                'low': p4,
                'minimal': p5,
            },
            'overdue': {
                'count': overdue_count,
                'tasks': overdue_list,
            },
            'recent_activity': {
                'tasks_created_last_7_days': recent_tasks,
                'tasks_completed_last_7_days': recent_done,
            },
            'user_productivity': user_stats,
        }

        return jsonify(report), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def user_report(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

        tasks = Task.query.filter_by(user_id=user_id).all()

        total = len(tasks)
        done = 0
        pending = 0
        in_progress = 0
        cancelled = 0
        overdue = 0
        high_priority = 0

        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)

        for t in tasks:
            if t.status == 'done':
                done += 1
            elif t.status == 'pending':
                pending += 1
            elif t.status == 'in_progress':
                in_progress += 1
            elif t.status == 'cancelled':
                cancelled += 1

            if t.priority <= 2:
                high_priority += 1

            if t.due_date:
                due_naive = t.due_date.replace(tzinfo=None) if t.due_date.tzinfo else t.due_date
                if due_naive < now_naive:
                    if t.status != 'done' and t.status != 'cancelled':
                        overdue += 1

        report = {
            'user': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
            },
            'statistics': {
                'total_tasks': total,
                'done': done,
                'pending': pending,
                'in_progress': in_progress,
                'cancelled': cancelled,
                'overdue': overdue,
                'high_priority': high_priority,
                'completion_rate': round((done / total) * 100, 2) if total > 0 else 0
            }
        }

        return jsonify(report), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
