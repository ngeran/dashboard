from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
import re

def fetch_routes(host, username, password, peer_ip, group_name):
    """Fetch received and advertised routes for a peer using CLI commands."""
    routes = {'received': [], 'advertised': []}

    try:
        with Device(host=host, user=username, passwd=password) as dev:
            # Fetch Advertised Routes
            advertised_cmd = f"show route advertising-protocol bgp {peer_ip} table inet.0"
            advertised_output = dev.cli(advertised_cmd, warning=False)
            print(f"Debug: Advertised CLI Output for {peer_ip}:\n{advertised_output}")

            # Parse prefixes from CLI output
            prefix_pattern = r'^\*\s+([\d\.]+/\d+)\s+'
            for line in advertised_output.splitlines():
                match = re.match(prefix_pattern, line.strip())
                if match:
                    routes['advertised'].append(match.group(1))

            # Fetch Received Routes
            received_cmd = f"show route receive-protocol bgp {peer_ip} table inet.0"
            received_output = dev.cli(received_cmd, warning=False)
            print(f"Debug: Received CLI Output for {peer_ip}:\n{received_output}")

            for line in received_output.splitlines():
                match = re.match(prefix_pattern, line.strip())
                if match:
                    routes['received'].append(match.group(1))

            print(f"Debug: Routes for {peer_ip} - Received: {routes['received']}, Advertised: {routes['advertised']}")

    except ConnectError as err:
        print(f"Failed to connect to {host}: {err}")
    except Exception as e:
        print(f"Error fetching routes for {peer_ip} (Group: {group_name}) on {host}: {e}")

    return routes

if __name__ == "__main__":
    # Standalone testing
    JUNOS_HOST = '10.0.0.10'
    JUNOS_USERNAME = 'admin'
    JUNOS_PASSWORD = 'your_password'  # Replace with actual password
    PEER_IP = '10.0.0.11'
    GROUP_NAME = 'BLACKROCK'

    print(f"Fetching routes for {PEER_IP} on {JUNOS_HOST}...")
    routes = fetch_routes(JUNOS_HOST, JUNOS_USERNAME, JUNOS_PASSWORD, PEER_IP, GROUP_NAME)

    print("\nAdvertised Routes:")
    if routes['advertised']:
        for prefix in routes['advertised']:
            print(f"  - {prefix}")
    else:
        print("  (None)")

    print("\nReceived Routes:")
    if routes['received']:
        for prefix in routes['received']:
            print(f"  - {prefix}")
    else:
        print("  (None)")
