from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from lxml.builder import E  # Required for building XML filters
import re  # Required for regex in format_junos_time
from src.route_fetcher import fetch_routes

def format_junos_time(uptime_element, peer_state):
    """Convert uptime to Junos-style format (e.g., 1w2d3h4m Up/Down)."""
    if uptime_element is None:
        return 'N/A'

    try:
        seconds_str = uptime_element.get('seconds')
        if seconds_str:
            seconds = int(seconds_str)
        else:
            time_text = uptime_element.text or ''
            if not re.match(r'^\d+:\d+:\d+$', time_text):
                return 'N/A'
            hours, minutes, _ = map(int, time_text.split(':'))
            seconds = hours * 3600 + minutes * 60

        if seconds < 0:
            return 'N/A'

        weeks = seconds // (7 * 24 * 3600)
        seconds %= (7 * 24 * 3600)
        days = seconds // (24 * 3600)
        seconds %= (24 * 3600)
        hours = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60

        parts = []
        if weeks:
            parts.append(f"{weeks}w")
        if days:
            parts.append(f"{days}d")
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")

        formatted_time = ''.join(parts) if parts else '0m'
        return f"{formatted_time} {'Up' if peer_state == 'Established' else 'Down'}"
    except (ValueError, AttributeError) as e:
        print(f"Debug: Error in format_junos_time: {e}")
        return 'N/A'

def get_bgp_status(hosts, username, password):
    bgp_data = []

    for host in hosts:
        try:
            dev = Device(host=host, user=username, passwd=password)
            dev.open()

            bgp_info = dev.rpc.get_bgp_summary_information()

            bgp_config_filter = E.protocols(E.bgp(E.group()))
            config_xml = dev.rpc.get_config(filter_xml=bgp_config_filter, database='candidate')

            peer_group_map = {}
            for group in config_xml.findall('.//group'):
                group_name = group.findtext('name') or 'N/A'
                for neighbor in group.findall('neighbor'):
                    neighbor_ip = neighbor.findtext('name')
                    if neighbor_ip:
                        peer_group_map[neighbor_ip] = group_name
            print(f"Debug: Peer Group Map for {host}: {peer_group_map}")

            for peer in bgp_info.findall('.//bgp-peer'):
                peer_data = {}

                peer_ip = peer.findtext('peer-address') or 'N/A'
                peer_ip_clean = peer_ip.split('+')[0] if '+' in peer_ip else peer_ip

                peer_data['partner_name'] = peer_group_map.get(peer_ip_clean, '')
                peer_data['peer_ip'] = peer_ip
                peer_data['peer_as'] = peer.findtext('peer-as') or ''
                peer_data['status'] = peer.findtext('peer-state') or 'N/A'
                peer_data['state'] = peer.findtext('peer-state') or 'N/A'

                uptime_element = peer.find('elapsed-time')
                peer_state = peer.findtext('peer-state') or 'N/A'
                peer_data['up_down'] = format_junos_time(uptime_element, peer_state)

                # Sum prefix counts across bgp-rib
                total_active = 0
                total_received = 0
                total_accepted = 0
                for bgp_rib in peer.findall('bgp-rib'):
                    total_active += int(bgp_rib.findtext('active-prefix-count') or '0')
                    total_received += int(bgp_rib.findtext('received-prefix-count') or '0')
                    total_accepted += int(bgp_rib.findtext('accepted-prefix-count') or '0')

                peer_data['active_subnets'] = str(total_active)
                peer_data['received_subnets'] = str(total_received)
                peer_data['accepted_subnets'] = str(total_accepted)

                # Fetch routes if group name is available
                group_name = peer_group_map.get(peer_ip_clean, '')
                if group_name:
                    print(f"Debug: Fetching routes for {peer_ip_clean} with group {group_name}")
                    routes = fetch_routes(host, username, password, peer_ip_clean, group_name)
                    peer_data['advertised_routes'] = routes.get('advertised', [])
                    peer_data['received_routes'] = routes.get('received', [])
                else:
                    print(f"Debug: No group name for {peer_ip_clean}, skipping routes")
                    peer_data['advertised_routes'] = []
                    peer_data['received_routes'] = []

                bgp_data.append(peer_data)

            # Debug: Print detailed peer data
            print(f"\nDebug: BGP Data for {host}:")
            for item in bgp_data:
                print("-" * 30)
                print(f"Partner Name: {item['partner_name']}")
                print(f"Peer Ip: {item['peer_ip']}")
                print(f"Peer As: {item['peer_as']}")
                print(f"Status: {item['status']}")
                print(f"State: {item['state']}")
                print(f"Up Down: {item['up_down']}")
                print(f"Active Subnets: {item['active_subnets']}")
                print(f"Received Subnets: {item['received_subnets']}")
                print(f"Accepted Subnets: {item['accepted_subnets']}")
                print("Advertised Routes:")
                if item['advertised_routes']:
                    for route in item['advertised_routes']:
                        print(f"  - {route}")
                else:
                    print("  (None)")
                print("Received Routes:")
                if item['received_routes']:
                    for route in item['received_routes']:
                        print(f"  - {route}")
                else:
                    print("  (None)")

            dev.close()

        except ConnectError as err:
            print(f"Failed to connect to {host}: {err}")
            bgp_data.append({
                'partner_name': '',
                'peer_ip': host,
                'peer_as': '',
                'status': 'Error',
                'state': 'Connection Failed',
                'up_down': 'N/A',
                'active_subnets': '0',
                'received_subnets': '0',
                'accepted_subnets': '0',
                'advertised_routes': [],
                'received_routes': []
            })

    return bgp_data
