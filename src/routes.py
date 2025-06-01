from flask import render_template
from src.bgp_data import get_bgp_status
from src.table_generator import generate_table
from src.input_handler import get_user_input

def setup_routes(app):
    @app.route('/', methods=['GET'])
    def dashboard():
        hosts, username, password = get_user_input()
        app.config['BGP_DATA'] = get_bgp_status(hosts, username, password)
        table = generate_table(app.config['BGP_DATA'])
        return render_template('dashboard.html', table=table)

    @app.route('/routes/<peer_ip>/<route_type>')
    def show_routes(peer_ip, route_type):
        bgp_data = app.config.get('BGP_DATA', [])
        peer_data = next((item for item in bgp_data if item['peer_ip'].startswith(peer_ip)), None)
        if not peer_data:
            return "Peer not found", 404

        routes = peer_data.get(f"{route_type}_routes", [])
        return render_template('routes.html', peer_ip=peer_ip, route_type=route_type, routes=routes)
