import sys
from itertools import groupby

if len(sys.argv) != 2:
    print("Usage: {} <elab-log-file>|-".format(sys.argv[0]))
    sys.exit(1)

def get_user_and_ip(line):
    last_col = line.split(" ")[-1]
    user,ip = last_col[1:-1].split("/")
    return user,ip

if sys.argv[1] == "-":
    lines = sys.stdin.read().splitlines()
else:
    lines = open(sys.argv[1]).read().splitlines()
rows = [(get_user_and_ip(line),line) for line in lines]
rows.sort()
grp_lines_by_user_ip = groupby(rows,key=lambda x:x[0])
user_ip = list(set([x for x,_ in rows]))
user_ip.sort()

# count unique IP for each user
grp_ip_by_user = dict((k,list(g)) for k,g in groupby(user_ip,key=lambda x:x[0]))
count_ip_by_user = [(user,len(list(ip))) for user,ip in grp_ip_by_user.items()]
flagged = [(u,count) for u,count in count_ip_by_user if count > 1]
for u,count in flagged:
    print("User {} accessed from {} IP addresses".format(u,count))
    for user,ip in grp_ip_by_user[u]:
        print("- {}".format(ip))

print('---------------------------------')
# count unique user for each IP
user_ip.sort(key=lambda x:x[1])
grp_user_by_ip = dict((k,list(g)) for k,g in groupby(user_ip,key=lambda x:x[1]))
count_user_by_ip = [(ip,len(list(user))) for ip,user in grp_user_by_ip.items()]
flagged = [(ip,count) for ip,count in count_user_by_ip if count > 1]
for ip,count in flagged:
    print("IP {} accessed from {} users".format(ip,count))
    for user,ip in grp_user_by_ip[ip]:
        print("- {}".format(user))
