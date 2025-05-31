import getpass

def get_user_input():
    hosts = input("Enter router IP(s) (comma-separated for multiple): ").split(',')
    hosts = [host.strip() for host in hosts]
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    return hosts, username, password
