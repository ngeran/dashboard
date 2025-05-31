from flask import render_template
from src.bgp_data import get_bgp_status
from src.table_generator import generate_table
from src.input_handler import get_user_input

def setup_routes(app):
    @app.route('/')
    def dashboard():
        hosts, username, password = get_user_input()
        bgp_data = get_bgp_status(hosts, username, password)
        table_html = generate_table(bgp_data)
        return render_template('dashboard.html', table=table_html)
