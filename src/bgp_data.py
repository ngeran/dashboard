from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from lxml.builder import E
import re

def format_junos_time(uptime_element, peer_state):
    """Convert uptime to Junos-style format (e.g., 1w2d3h4m Up/Down)."""
    if uptime_element is None:
        return 'N/A'

    try:
        # Debug: Print raw element details
        print(f"Debug: Uptime element - text={uptime_element.text}, seconds={uptime_element.get('seconds')}")

        # Try to get seconds from the 'seconds' attribute
        seconds_str = uptime_element.get('seconds')
        if seconds_str:
            seconds = int(seconds_str)
        else:
            # Fallback: Parse HH:MM:SS format from text
            time_text = uptime_element.text or ''
            if not re.match(r'^\d+:\d+:\d+$', time_text):
                return 'N/A'
            hours, minutes, secs = map(int, time_text.split(':'))
            seconds = hours * 3600 + minutes * 60 + secs

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
    except (ValueError, TypeError, AttributeError) as e:
        print(f"Debug: Error in format_junos_time: {e}")
        return 'N/A'

def get_bgp_status(hosts, username, password):
    bgp_data = []

    for host in hosts:
        try:
            dev = Device(host=host, user=username, passwd=password)
            dev.open()

            # Get BGP summary information
            bgp_info = dev.rpc.get_bgp_summary_information()

            # Get BGP configuration to map peer IPs to group names
            bgp_config_filter = E.protocols(E.bgp(E.group()))
            config_xml = dev.rpc.get_config(filter_xml=bgp_config_filter, database='candidate')

            # Create a mapping of peer IPs to group names
            peer_group_map = {}
            for group in config_xml.findall('.//group'):
                group_name = group.findtext('name') or 'N/A'
                for neighbor in group.findall('neighbor'):
                    neighbor_ip = neighbor.findtext('name')
                    if neighbor_ip:
                        peer_group_map[neighbor_ip] = group_name

            # Process BGP peer information
            for peer in bgp_info.findall('.//bgp-peer'):
                peer_data = {}

                # Get peer IP to lookup group name
                peer_ip = peer.findtext('peer-address') or 'N/A'
                peer_ip_clean = peer_ip.split('+')[0] if '+' in peer_ip else peer_ip

                peer_data['partner_name'] = peer_group_map.get(peer_ip_clean, 'N/A')
                peer_data['peer_ip'] = peer_ip
                peer_data['peer_as'] = peer.findtext('peer-as') or 'N/A'
                peer_data['status'] = peer.findtext('peer-state') or 'N/A'
                peer_data['state'] = peer.findtext('peer-state') or 'N/A'

                # Get uptime element
                uptime_element = peer.find('elapsed-time')
                peer_state = peer.findtext('peer-state') or 'N/A'
                peer_data['up_down'] = format_junos_time(uptime_element, peer_state)

                peer_data['active_subnets'] = peer.findtext('active-prefix-count') or '0'
                peer_data['received_subnets'] = peer.findtext('received-prefix-count') or '0'
                peer_data['accepted_subnets'] = peer.findtext('accepted-prefix-count') or '0'

                bgp_data.append(peer_data)

            dev.close()

        except ConnectError as err:
            print(f"Failed to connect to {host}: {err}")
            bgp_data.append({
                'partner_name': 'N/A',
                'peer_ip': host,
                'peer_as': 'N/A',
                'status': 'Error',
                'state': 'Connection Failed',
                'up_down': 'N/A',
                'active_subnets': '0',
                'received_subnets': '0',
                'accepted_subnets': '0'
            })

    return bgp_data
