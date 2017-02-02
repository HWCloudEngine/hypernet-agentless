import glob
import json
import SocketServer
import subprocess


class Config(object):
    _CONF_PATHS = [
        '/etc/neutron/*.tmpl',
        '/etc/neutron/plugins/ml2/*.tmpl',
        '/etc/hyperswitch/*.tmpl',
    ]

    _SERVICES = [
        'neutron-ovs-cleanup',
        'neutron-l3-agent',
        'neutron-metadata-agent',
        'neutron-plugin-openvswitch-agent',
        'hyperswitch-cleanup',
        'hyperswitch',
    ]
    
    def apply(self, params):
        for conf_path in self._CONF_PATHS:
            for file_conf in glob.glob(conf_path):
                with open(file_conf, 'r') as source:
                    lines = source.readlines()                
                for i in range(len(lines)):
                    for key, value in params.iteritems():
                        lines[i] = lines[i].replace('##%s##' % key, value)
                with open(file_conf[0:file_conf.rfind('.')], 'w') as dest:
                    for line in lines:
                        dest.write(line)
        if 'host' in params:
            subprocess.call(['hostname', params['host']]) 
            with open('/etc/hostname', 'w') as dest:
                dest.write(params['host'])
        for service in self._SERVICES:
            subprocess.call(['service', service, 'stop']) 
            subprocess.call(['service', service, 'start']) 
            

class ConfigTCPHandler(SocketServer.StreamRequestHandler):

    def __init__(self):
        self.config = Config()

    def handle(self):
        data = json.decoder.JSONDecoder().decode(self.rfile.readline().strip())
        print('received %s from %s' % (data, self.client_address[0]))
        self.config.apply(data)
        self.wfile.write("OK")
        

def main():
    HOST, PORT = "0.0.0.0", 8080

    server = SocketServer.TCPServer((HOST, PORT), ConfigTCPHandler)
    print('Started config tcp server on %s:%s ' % (HOST, PORT))

    server.serve_forever()


if __name__ == "__main__":
    main()