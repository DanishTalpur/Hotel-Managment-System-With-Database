from flask import Flask
from database import db
import os

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'your-secret-key-here'
    
    # Get the instance folder path
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(instance_path, "hotel.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    from routers.dashboard import dashboard_router
    from routers.guests import guests_router
    from routers.reservations import reservations_router
    from routers.rooms import rooms_router
    from routers.invoices import invoices_router
    from routers.services import services_router
    from routers.extras import extras_router
    from routers.rates import rates_router
    
    app.register_blueprint(dashboard_router)
    app.register_blueprint(guests_router)
    app.register_blueprint(reservations_router)
    app.register_blueprint(rooms_router)
    app.register_blueprint(invoices_router)
    app.register_blueprint(services_router)
    app.register_blueprint(extras_router)
    app.register_blueprint(rates_router)
    
    return app