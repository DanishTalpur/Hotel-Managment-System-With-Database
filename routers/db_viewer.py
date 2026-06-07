from flask import Blueprint, render_template, request, jsonify
from database import db
from sqlalchemy import inspect, text
from datetime import date
import re

db_viewer_router = Blueprint('db_viewer', __name__)

FORBIDDEN_SQL = re.compile(
    r'\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|TRUNCATE|GRANT|REVOKE)\b',
    re.IGNORECASE
)


def _get_table_names():
    return inspect(db.engine).get_table_names()


def _is_safe_select(sql):
    cleaned = sql.strip().rstrip(';').strip()
    if not cleaned.upper().startswith('SELECT'):
        return False
    if FORBIDDEN_SQL.search(cleaned):
        return False
    if ';' in cleaned:
        return False
    return True


def _rows_to_dicts(result):
    columns = list(result.keys())
    return [dict(zip(columns, row)) for row in result.fetchall()]


@db_viewer_router.route('/database')
def database_viewer():
    return render_template(
        'db_viewer.html',
        active='database',
        current_date=date.today().strftime('%A, %d %B %Y'),
        preset_queries=[
            ('All guests', 'SELECT customer_id, first_name, last_name, email, phone FROM customer ORDER BY customer_id DESC LIMIT 10'),
            ('Active bookings', "SELECT booking_id, customer_id, status, planned_checkin, planned_checkout FROM booking WHERE status IN ('booked', 'checked_in') ORDER BY booking_id DESC"),
            ('Latest invoices', 'SELECT invoice_id, booking_id, subtotal, total_amount, payment_status FROM invoice ORDER BY invoice_id DESC LIMIT 10'),
            ('Row counts', 'SELECT (SELECT COUNT(*) FROM customer) AS guests, (SELECT COUNT(*) FROM booking) AS bookings, (SELECT COUNT(*) FROM invoice) AS invoices, (SELECT COUNT(*) FROM payment) AS payments'),
        ]
    )


@db_viewer_router.route('/database/api/tables')
def api_table_counts():
    counts = {}
    for table in _get_table_names():
        result = db.session.execute(text(f'SELECT COUNT(*) AS cnt FROM "{table}"'))
        counts[table] = result.scalar()
    return jsonify({'tables': counts})


@db_viewer_router.route('/database/api/table/<table_name>')
def api_table_data(table_name):
    if table_name not in _get_table_names():
        return jsonify({'error': 'Unknown table'}), 404

    result = db.session.execute(text(f'SELECT * FROM "{table_name}" ORDER BY rowid DESC LIMIT 50'))
    rows = _rows_to_dicts(result)
    columns = list(result.keys()) if rows else []
    if not columns:
        result = db.session.execute(text(f'SELECT * FROM "{table_name}" LIMIT 0'))
        columns = list(result.keys())

    return jsonify({'table': table_name, 'columns': columns, 'rows': rows})


@db_viewer_router.route('/database/api/query', methods=['POST'])
def api_run_query():
    data = request.get_json(silent=True) or {}
    sql = (data.get('sql') or '').strip()
    if not sql:
        return jsonify({'error': 'Query is empty.'}), 400
    if not _is_safe_select(sql):
        return jsonify({'error': 'Only single SELECT queries are allowed (read-only).'}), 400

    try:
        result = db.session.execute(text(sql))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
        return jsonify({'columns': columns, 'rows': rows, 'row_count': len(rows)})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 400
