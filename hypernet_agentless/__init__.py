import sys
import site


sys.path.insert(0, '/opt/juno_neutron/lib/python2.7/site-packages')
sys.path.insert(0, '/opt/juno_neutron/lib64/python2.7/site-packages')
site.addsitedir('/opt/juno_neutron/lib/python2.7/site-packages')
site.addsitedir('/opt/juno_neutron/lib64/python2.7/site-packages')
