from jnpr.junos import Device
from jnpr.junos.exception import ConnectError
from datetime import timedelta

def get_bgp_status(hosts, username, password):
    bgp_data = []

    for host in hosts:
        try:
            dev = Device(host=host, user=username, passwd=password)
            dev.open()

            bgp_info = dev.rpc.get_bgp_summary_information()

            for peer in bgp_info.findall('.//bgp-peer'):
                peer_data = {}
                peer_data['partner_name'] = peer.findtext('peer-group') or 'N/A'
                peer_data['peer_ip'] = peer.findtext('peer-address') or 'N/A'
                peer_data['peer_as'] = peer.findtext('peer-as') or 'N/A'
                peer_data['status'] = peer.findtext('peer-state') or 'N/A'
                peer_data['state'] = peer.findtext('peer-state') or 'N/A'

                uptime = peer.findtext('elapsed-time')
                if uptime:
                    try:
                        seconds = int(uptime) if uptime.isdigit() else 0
                        uptime_str = str(timedelta(seconds=seconds))
                        peer_data['up_down'] = uptime_str
                    except:
                        peer_data['up_down'] = 'N/A'
                else:
                    peer_data['up_down'] = 'N/A'

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
