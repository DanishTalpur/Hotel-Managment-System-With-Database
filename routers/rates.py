from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import Rate, RateType, RoomType, OccupancyType, Facility, RateFacility
from database import db
from datetime import datetime, date

rates_router = Blueprint('rates', __name__)

@rates_router.route('/rates')
def rates_screen():
    # Fetch unique seasons (start_date, end_date) from Rate table
    seasons_raw = db.session.query(Rate.start_date, Rate.end_date).distinct().all()
    seasons = []
    for start, end in seasons_raw:
        seasons.append({
            'start_date': start,
            'end_date': end,
            'value': f"{start.strftime('%Y-%m-%d')}_{end.strftime('%Y-%m-%d')}",
            'label': f"{start.strftime('%d %b')} – {end.strftime('%d %b')}"
        })
    
    # Get season filter from request args
    season_filter = request.args.get('season', '')
    filter_start, filter_end = None, None
    
    if season_filter:
        try:
            start_str, end_str = season_filter.split('_')
            filter_start = datetime.strptime(start_str, '%Y-%m-%d').date()
            filter_end = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            pass
            
    # Default to first season or active season if none specified
    if not filter_start and seasons:
        today = date.today()
        default_season = None
        for s in seasons:
            if s['start_date'] <= today <= s['end_date']:
                default_season = s
                break
        if not default_season:
            default_season = seasons[0]
        
        filter_start = default_season['start_date']
        filter_end = default_season['end_date']
        season_filter = default_season['value']

    # Retrieve all rates for selected season
    rates_query = Rate.query
    if filter_start and filter_end:
        rates_query = rates_query.filter_by(start_date=filter_start, end_date=filter_end)
    rates = rates_query.all()
    
    # Map rates to (room_type_id, occupancy_type_id, rate_type_id)
    rates_map = {}
    for r in rates:
        rates_map[(r.room_type_id, r.occupancy_type_id, r.rate_type_id)] = r
        
    room_types = RoomType.query.all()
    occupancy_types = OccupancyType.query.all()
    rate_types = RateType.query.order_by(RateType.rate_type_id).all()
    
    # Construct Rate Matrix
    matrix_rows = []
    for rt in room_types:
        for ot in occupancy_types:
            row_rates = []
            has_any_rate = False
            for rtype in rate_types:
                rate_obj = rates_map.get((rt.room_type_id, ot.occupancy_type_id, rtype.rate_type_id))
                if rate_obj:
                    has_any_rate = True
                row_rates.append({
                    'rate_type': rtype,
                    'rate': rate_obj
                })
            # Only include combinations that have rates in the selected season
            if has_any_rate:
                matrix_rows.append({
                    'room_type': rt,
                    'occupancy_type': ot,
                    'row_rates': row_rates
                })

    # Stats
    total_rate_types = RateType.query.count()
    active_seasons_count = len(seasons)
    total_records = Rate.query.count()
    # Calculate avg rack rate (rate_type_id = 1)
    avg_rack = db.session.query(db.func.avg(Rate.amount)).filter_by(rate_type_id=1).scalar() or 0
    
    stats = {
        'rate_types': total_rate_types,
        'active_seasons': active_seasons_count,
        'total_records': total_records,
        'avg_rack_rate': avg_rack
    }
    
    # Facilities for selected rate type
    facility_rate_type_id = request.args.get('facility_rate_type', type=int)
    if not facility_rate_type_id and rate_types:
        facility_rate_type_id = rate_types[0].rate_type_id
        
    selected_rate_type = RateType.query.get(facility_rate_type_id) if facility_rate_type_id else None
    
    all_facilities = Facility.query.all()
    rate_facility_ids = []
    if selected_rate_type:
        rate_facility_ids = [f.facility_id for f in selected_rate_type.facilities]
        
    facilities_data = []
    for fac in all_facilities:
        facilities_data.append({
            'facility': fac,
            'enabled': fac.facility_id in rate_facility_ids
        })

    return render_template(
        'rates.html',
        active='rates',
        current_date=datetime.now().strftime('%A, %d %B %Y'),
        seasons=seasons,
        season_filter=season_filter,
        filter_start=filter_start,
        filter_end=filter_end,
        matrix_rows=matrix_rows,
        rate_types=rate_types,
        room_types=room_types,
        occupancy_types=occupancy_types,
        stats=stats,
        selected_rate_type=selected_rate_type,
        facilities=facilities_data
    )

@rates_router.route('/rates/add', methods=['POST'])
def add_rate():
    rate_type_id = int(request.form['rate_type_id'])
    room_type_id = int(request.form['room_type_id'])
    occupancy_type_id = int(request.form['occupancy_type_id'])
    amount = float(request.form['amount'])
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
    
    # Check if rate already exists for this combination and dates
    existing = Rate.query.filter_by(
        rate_type_id=rate_type_id,
        room_type_id=room_type_id,
        occupancy_type_id=occupancy_type_id,
        start_date=start_date,
        end_date=end_date
    ).first()
    
    if existing:
        existing.amount = amount
        flash('Rate updated successfully!', 'success')
    else:
        rate = Rate(
            rate_type_id=rate_type_id,
            room_type_id=room_type_id,
            occupancy_type_id=occupancy_type_id,
            amount=amount,
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(rate)
        flash('Rate added successfully!', 'success')
        
    db.session.commit()
    season_val = f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
    return redirect(url_for('rates.rates_screen', season=season_val))

@rates_router.route('/rates/delete_row', methods=['POST'])
def delete_row():
    room_type_id = int(request.form['room_type_id'])
    occupancy_type_id = int(request.form['occupancy_type_id'])
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
    
    # Delete all rates matching this combination and season
    rates_to_delete = Rate.query.filter_by(
        room_type_id=room_type_id,
        occupancy_type_id=occupancy_type_id,
        start_date=start_date,
        end_date=end_date
    ).all()
    
    deleted_count = 0
    for rate in rates_to_delete:
        db.session.delete(rate)
        deleted_count += 1
        
    db.session.commit()
    flash(f'Deleted {deleted_count} rate(s) for the selected room occupancy and season.', 'success')
    
    season_val = f"{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"
    return redirect(url_for('rates.rates_screen', season=season_val))

@rates_router.route('/rates/facility/save', methods=['POST'])
def save_facilities():
    rate_type_id = int(request.form['rate_type_id'])
    enabled_facility_ids = request.form.getlist('facilities', type=int)
    
    # Delete existing mappings in RateFacility
    RateFacility.query.filter_by(rate_type_id=rate_type_id).delete()
    
    # Add new mappings
    for fac_id in enabled_facility_ids:
        mapping = RateFacility(rate_type_id=rate_type_id, facility_id=fac_id)
        db.session.add(mapping)
        
    db.session.commit()
    flash('Facility settings updated successfully!', 'success')
    
    season = request.form.get('season_filter', '')
    return redirect(url_for('rates.rates_screen', facility_rate_type=rate_type_id, season=season))
