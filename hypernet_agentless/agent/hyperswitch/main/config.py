import json
import os
import SocketServer
import subprocess


MNGT_IP_FILE = '/etc/hyperswitch/mngt_ip'


class Config(object):
    _SERVICES = [
        'neutron-ovs-cleanup',
        'neutron-l3-agent',
        'neutron-metadata-agent',
        'neutron-plugin-openvswitch-agent',
        'hyperswitch-cleanup',
        'hyperswitch',
#        'hyperswitch-config',
    ]

    def _write_file(self, file_name, content):
        with open(file_name, 'w') as dest:
            if isinstance(content, str):
                dest.write(content)
            else:
                for line in content:
                    dest.write(line)

    def apply(self, params):
        proc = subprocess.Popen(
            ['find', '/etc', '-name', '*.tmpl'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, _ = proc.communicate()
        for file_conf in stdout.split():
            print('file configuration %s' % file_conf)
            with open(file_conf, 'r') as source:
                lines = source.readlines()                
            for i in range(len(lines)):
                for key, value in params.iteritems():
                    if value:
                        lines[i] = lines[i].replace('##%s##' % key, value)
            self._write_file(
                file_conf[0:file_conf.rfind('.')], lines)
        if 'host' in params:
            subprocess.call(['hostname', params['host']]) 
            self._write_file('/etc/hostname', params['host'])
        if 'mngt_ip' in params:
            self._write_file(MNGT_IP_FILE, params['mngt_ip'])
        for service in self._SERVICES:
            subprocess.call(['service', service, 'restart']) 


class ConfigTCPHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        config = Config()
        data = json.decoder.JSONDecoder().decode(self.rfile.readline().strip())
        print('received %s from %s' % (data, self.client_address[0]))
        config.apply(data)
        self.wfile.write("OK")


def main():
    HOST = '0.0.0.0'
    PORT = 8080
    if os.path.exists(MNGT_IP_FILE):
        with open(MNGT_IP_FILE, 'r') as source:
            HOST = source.readline()                
    server = SocketServer.TCPServer((HOST, PORT), ConfigTCPHandler)
    print('Started config tcp server on %s:%s ' % (HOST, PORT))

    server.serve_forever()


if __name__ == "__main__":
    main()