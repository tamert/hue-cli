import fnmatch
import nmap
import logging

log = logging.getLogger(__name__)

nm = nmap.PortScanner()


def lan_scan(net='192.168.1.0/24', port=None, intensity=None,
            nmapargs=None, top=50, services=False, repeat=1, showall=False):
    '''Scan network and ports.

    port='22-433', port=22, port='22,80', port=(80, 443, '2000-2200')
    '''
    if isinstance(port, (tuple, list)):
        port = ','.join(map(str, port))

    nmapargs = (nmapargs,) if isinstance(nmapargs, str) else tuple(nmapargs or ())
    if services:
        nmapargs = ('-sV',)
    if intensity is not None:
        assert 0 <= intensity <= 9
        nmapargs += ('--version-intensity {}'.format(intensity),)
    if top:
        nmapargs += ('--top-ports {}'.format(top),)  # ('-F',) # -F is not working
    # if force:
    #     nmapargs += ('-R',)

    for i in range(repeat or 1):
        nm.scan(net, ports=str(port) if port else None, arguments=' '.join(nmapargs))
        for ip in nm.all_hosts():
            host = nm[ip]
            ports = [
                port for proto in host.all_protocols()
                for port, status in host[proto].items()
                if status['state'] == 'open'
            ]
            if ports or showall:
                data = {
                    'hostname': nm[ip].hostname() or '',
                    'ip': ip, 'ports': ports, 'tcp': nm[ip].get('tcp')
                    # 'status': host['status']['state'],  # up
                }
                # lookup mac address in case they ran with sudo
                mac = host['addresses'].get('mac')
                vendor = host['vendor'][mac] if mac and mac in host['vendor'] else None
                if mac:
                    data.update({'mac': mac, 'vendor': vendor})
                yield data


def scan(hostname=None, ignore=None, ip=None, n=None, hasname=None, **kw):
    '''Scan devices on your local network. Filter by hostname or ip.
    '''
    # get all devices
    devices = lan_scan(**kw)
    if hostname:
        devices = (d for d in devices if matches(d, hostname))
    if ignore:
        devices = (d for d in devices if not matches(d, ignore))
    if ip:
        devices = (d for d in devices if check_ranges([d['ip'], d['ip'].split('.')], ip))
    if hasname:
        devices = (d for d in devices if d['hostname'])
    if n is not None:
        devices = (d for d, i in zip(devices, range(n)))
    # get devices grouped into different categories
    return devices


def hostname(ip=None, port='22-433'):
    if ip is None:
        ip = me()
    nm.scan(ip, str(port) if port else None)
    return nm[ip].hostname()


_SKIP_ME = {'lo0'}


def me(*names, v6=False, all=False):
    import ifcfg
    inet = 'inet6' if v6 else 'inet'
    ips = {k: ifc[inet] for k, ifc in ifcfg.interfaces().items()
           if k not in _SKIP_ME and ifc.get(inet)}
    if names:
        return [ips.get(n) for n in names]
    if all:
        return ips
    return max_common_prefix('192.168.4', *ips.values(), n=2, split='.')


'''

Utils

'''

MATCH_COLS = 'hostname', 'ip'


def matches(d, pat):
    pat = str(pat)
    return any(pat in str(d[c]) or fnmatch.fnmatch(str(d[c]), pat) for c in MATCH_COLS)


def check_ranges(xs, ranges):
    ranges = str(ranges).split(',')
    between = lambda x, xmin, xmax: xmin < x < xmax
    return any(
        (between(x, *r.split('-')) if '-' in r else x == r)
        for x in xs or () for r in ranges
    )


def max_common_prefix(prefix, *values, n=1, split=None):
    if split:
        prefix, values = prefix.split(split), (x.split(split) for x in values)
    match = max((
        (i, x) for i, x in ((n_common_prefix(prefix, val), val) for val in values)
        if i >= n), default=(None, None))[1]
    if match is not None and split:
        match = split.join(match)
    return match


def n_common_prefix(*strs):
    return next(
        (i for i, chs in enumerate(zip(*strs)) if len(set(chs)) > 1),
        min(len(s) for s in strs))
