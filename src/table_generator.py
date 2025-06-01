from tabulate import tabulate

def generate_table(data):
    headers = ['Partner Name', 'Peer IP', 'Peer AS', 'Status', 'State', 'Up/Down Time',
               'Active Subnets', 'Received Subnets', 'Accepted Subnets',
               'Received Prefixes', 'Advertised Prefixes']
    table_data = [
        [
            item['partner_name'],
            item['peer_ip'],
            item['peer_as'],
            item['status'],
            '<span style="color: green;">✅</span>' if item['state'] == 'Established' else '<span style="color: red;">❌</span>',
            item['up_down'],
            item['active_subnets'],
            item['received_subnets'],
            item['accepted_subnets'],
            f'<a href="/routes/{item["peer_ip"].split("+")[0]}/received">{len(item["received_routes"])}</a>',
            f'<a href="/routes/{item["peer_ip"].split("+")[0]}/advertised">{len(item["advertised_routes"])}</a>'
        ] for item in data
    ]
    return tabulate(table_data, headers=headers, tablefmt='html', disable_numparse=True)
