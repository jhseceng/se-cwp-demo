import nmap
from flask import make_response ,jsonify

def nmap_host(target_ip):

     # target_ip = request.form.get('target')
     nm = nmap.PortScanner()
     scan_res = nm.scan('target_ip', '80')
     res = make_response(jsonify(
         scan_res), 200)
     res.headers['Content-type'] = 'application/json'
     return res


if __name__ == '__main__':
    nmap_host('127.0.0.1')