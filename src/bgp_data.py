from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from lxml import etree
from lxml.builder import E
import re
#V3
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
        dev = None
        try:
            dev = Device(host=host, user=username, passwd=password)
            dev.open()

            # --- RPC call to get BGP summary information (without 'detail=True') ---
            # Your device already provides detail in this response.
            bgp_summary_info = dev.rpc.get_bgp_summary_information()

            # Print the raw XML to double-check its structure always
            print(f"\n--- Raw XML Response from get_bgp_summary_information on {host} ---")
            print(etree.tostring(bgp_summary_info, pretty_print=True).decode())
            print("--- End Raw XML Response from get_bgp_summary_information ---\n")


            # Get BGP configuration to map peer IPs to group names (still needed)
            # You might need to use database='committed' if 'candidate' isn't what you want
            bgp_config_filter = E.protocols(E.bgp(E.group()))
            config_xml = dev.rpc.get_config(filter_xml=bgp_config_filter, database='candidate')

            peer_group_map = {}
            for group in config_xml.findall('.//group'):
                group_name = group.findtext('name') or 'N/A'
                for neighbor in group.findall('neighbor'):
                    neighbor_ip = neighbor.findtext('name')
                    if neighbor_ip:
                        peer_group_map[neighbor_ip] = group_name

            # Process BGP peer information from the summary
            # The root of the XML from get_bgp_summary_information is <bgp-information>
            # And peers are <bgp-peer>
            for peer_data_xml in bgp_summary_info.findall('.//bgp-peer'):
                peer_data = {}

                # Extract peer IP, cleaning if necessary
                peer_ip = peer_data_xml.findtext('peer-address') or 'N/A'
                peer_ip_clean = peer_ip.split('+')[0] if '+' in peer_ip else peer_ip

                peer_data['partner_name'] = peer_group_map.get(peer_ip_clean, 'N/A')
                peer_data['peer_ip'] = peer_ip
                peer_data['peer_as'] = peer_data_xml.findtext('peer-as') or 'N/A'
                peer_data['status'] = peer_data_xml.findtext('peer-state') or 'N/A'
                peer_data['state'] = peer_data_xml.findtext('peer-state') or 'N/A'

                uptime_element = peer_data_xml.find('elapsed-time')
                peer_state = peer_data_xml.findtext('peer-state') or 'N/A'
                peer_data['up_down'] = format_junos_time(uptime_element, peer_state)

                # --- Extract prefix counts from bgp-rib within the current peer ---
                total_active = 0
                total_received = 0
                total_accepted = 0

                # Iterate through all 'bgp-rib' elements directly within the current 'bgp-peer'
                for bgp_rib in peer_data_xml.findall('bgp-rib'): # Use direct child 'bgp-rib'
                    total_active += int(bgp_rib.findtext('active-prefix-count') or '0')
                    total_received += int(bgp_rib.findtext('received-prefix-count') or '0')
                    total_accepted += int(bgp_rib.findtext('accepted-prefix-count') or '0')

                peer_data['active_subnets'] = str(total_active)
                peer_data['received_subnets'] = str(total_received)
                peer_data['accepted_subnets'] = str(total_accepted)

                bgp_data.append(peer_data)

            if dev:
                dev.close()

        except ConnectError as err:
            print(f"Failed to connect to {host}: {err}")
            bgp_data.append({
                'partner_name': 'N/A', 'peer_ip': host, 'peer_as': 'N/A',
                'status': 'Error', 'state': 'Connection Failed', 'up_down': 'N/A',
                'active_subnets': '0', 'received_subnets': '0', 'accepted_subnets': '0'
            })
        except Exception as e:
            print(f"An unexpected error occurred for host {host}: {e}")
            if dev:
                dev.close()
            bgp_data.append({
                'partner_name': 'N/A', 'peer_ip': host, 'peer_as': 'N/A',
                'status': 'Error', 'state': f"Unhandled Error: {e}", 'up_down': 'N/A',
                'active_subnets': '0', 'received_subnets': '0', 'accepted_subnets': '0'
            })

    return bgp_data

# Example Usage (assuming you have a main script that calls this)
if __name__ == "__main__":
    # Replace with your actual hosts, username, and password
    JUNOS_HOSTS = ['your_junos_device_ip_or_hostname'] # e.g., ['192.168.1.100']
    JUNOS_USERNAME = 'your_username'
    JUNOS_PASSWORD = 'your_password'

    print("Fetching BGP status...")
    status = get_bgp_status(JUNOS_HOSTS, JUNOS_USERNAME, JUNOS_PASSWORD)

    if status:
        for entry in status:
            print("-" * 30)
            for k, v in entry.items():
                print(f"{k.replace('_', ' ').title()}: {v}")
    else:
        print("No BGP data retrieved.")
