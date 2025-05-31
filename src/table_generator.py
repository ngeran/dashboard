from tabulate import tabulate

def generate_table(data):
    headers = ['Partner Name', 'Peer IP', 'Peer AS', 'Status', 'State', 'Up/Down Time',
               'Active Subnets', 'Received Subnets', 'Accepted Subnets']
    table_data = [
        [
            item['partner_name'],
            item['peer_ip'],
            item['peer_as'],
            item['status'],
            item['state'],
            item['up_down'],
            item['active_subnets'],
            item['received_subnets'],
            item['accepted_subnets']
        ] for item in data
    ]
    return tabulate(table_data, headers=headers, tablefmt='html')
