
from hypernet_agentless.server import config
from hypernet_agentless.server.db.hyperswitch import dns_db 
from hypernet_agentless.common import hs_constants
from oslo_log import log as logging
from sqlalchemy import and_
from sqlalchemy import desc
from sqlalchemy import func
from sqlalchemy import distinct
import math
import uuid

LOG = logging.getLogger(__name__)

'''
This class manages the ratio-based policy of HyperSwitch (HS) allocation.
The policy is based on a ratio that is actually the amount of ports to be connected to a HS instance (or multiple HS instances, if HA is set).
All port and HS life cycle events are covered - allowing the amount of allocated HS to expand and shrink according to ports allocations. 
HS failures are also handled.
Note:
HS instances are identified via their IP addresses
port instances are identified via the unique name they are looking up as their VPN server - 'www.<port_uuid in short format>.com'
'''

class RatioManagement(object): 


    def __init__(self, callback_handle): 
        self.ratio       = config.hs_ratio()
        self.is_ha       = config.hs_ha()
        self.hs_lc       = HSLifeCycle(callback_handle)
        self.primary_discriminator = "primary"
        self.secondary_discriminator = "secondary"
        LOG.info("ratio is %s, high availability is %s" %(self.ratio, self.is_ha ))
       
    
    def _handle_port_added(self, context, port_id, index, discriminator, hyperswitch_data):
        tenant_id = hyperswitch_data[hs_constants.HYPERSWITCH]['tenant_id']
        vacant_hs_tuple = get_vacant_hs(context, tenant_id, discriminator)
        #if there is no potentially vacant HS, or the potentially vacant one has already the max amount of ports attached to it
        if vacant_hs_tuple == None or vacant_hs_tuple['port_count'] >= self.ratio:
            #need to create a new HS
            LOG.debug("No %s vacant HS for %s, creating a new one" %(discriminator, port_id))
            hs_dict = self.hs_lc.launch_new_HS(context, hyperswitch_data)
            _persist_hs_data(context, tenant_id, hs_dict)
            hs_ip = hs_dict['vms_ips'][index]['vms_ip']
            hs_id = hs_dict['id']
        else:
            #there is a vacant HS so we can use it for the new port
            hs_id = vacant_hs_tuple['hs_id']
            hs_ip = get_hs_ip_by_index(context, hs_id, index)
            
            LOG.debug("%s with index %s will be attached to existing HS %s to IP %s" %(port_id, index, hs_id, hs_ip))
         
        #at any case - update the persistency so that the lookup name the new port has will be resolved to this HS IP       
        add_dns_mapping(context, hs_id, hs_ip, port_id, index, tenant_id,discriminator) 
        return hs_id
        
    def new_port_added(self, context, port_id, index, hyperswitch_data):
        LOG.debug("port added %s with index %s" %(port_id, index))
        hs_ids = []
        hs_ids.append(self._handle_port_added(context, port_id, index, self.primary_discriminator, hyperswitch_data))
        if self.is_ha:
            hs_ids.append(self._handle_port_added(context, port_id, index, self.secondary_discriminator, hyperswitch_data)) 
        return hs_ids    
    
    def _handle_port_removed(self, context, port_id, discriminator):
        #first see to which HSs this port was connected
        hs_id = get_hs_by_port_id(context, port_id, discriminator)
        if hs_id == None:
            LOG.debug("port %s does not exist in DNS mappings, doing nothing" %(port_id))
            return #This port does not exist in our records, no need to proceed
            
        #then remove the mapping record
        delete_records_by_port_id(context, port_id)
        
        if (get_port_dns_domain_name_by_hs(context, hs_id).__len__ == 0):
            #no need for this HS, it does not serve any port
            LOG.debug("No additional ports are using HS %s, so it needs to be removed" %(hs_id))
            self.hs_lc.delete_HS(context, hs_id)
            _delete_hs_data(hs_id)
        else: 
            #if the HS stays, see whether its ports can be consolidated with other HSs' ports
            LOG.debug("Other ports are using HS %s, consider consolidating since port %s is removed" %(hs_id, port_id))
            tenant_id = get_hs_tenant(context, hs_id)
            self._consider_consolidation(context, tenant_id)    
    
    
    def port_removed(self, context, port_id):
        LOG.debug("port %s is removed" %(port_id))
        self._handle_port_removed(context, port_id, self.primary_discriminator)
        if self.is_ha:
            self._handle_port_removed(context, port_id, self.secondary_discriminator)

    
    def _consider_consolidation(self, context, tenant_id):
        #Note: in case of HA we do the consolidation independently on the primary HS group and the secondary one. 
        if self._should_consolidate(context, tenant_id, self.primary_discriminator):
            self._handle_consider_consolidation(context, get_all_hs_ordered(context, tenant_id, self.primary_discriminator), self.primary_discriminator)
            if self.is_ha and self._should_consolidate(context, tenant_id, self.secondary_discriminator):
                self._handle_consider_consolidation(context, get_all_hs_ordered(context, tenant_id, self.secondary_discriminator), self.secondary_discriminator)
      
      
    def _should_consolidate(self, context, tenant_id, discriminator):
        #return whether the amount of primary HS instances is larger than the amount required for this amount of ports given the set ratio
        #return get_hs_count(context, discriminator) > math.ceil(get_port_count(context, discriminator)/self.ratio)
        hs_count = get_hs_count(context, tenant_id, discriminator)
        port_count = get_port_count(context, tenant_id, discriminator)
        result = (hs_count) > math.ceil(float(port_count)/self.ratio) #need to force to a float since python 2.x truncates the division of 2 ints into an int
        return result
     
     
    ''' 
    This method receives hs_group as an array of 2-tuples in the format of (ip, port_count)
    The array is sorted by port_count, lowest value first
    '''        
    def _handle_consider_consolidation(self, context, hs_group_ordered, discriminator):
        #Best choice would be to delete the HS with smallest amount of ports connected 
        #and spread its ports across other HSs, starting with the less utilized ones first 
        #all_hs is an array of 2-tuples of the format (ip, port_count)
        #The HS at the top is the one with least ports connected
        hs_to_remove = hs_group_ordered.pop()
        port_dns_domain_names_to_migrate = get_port_dns_domain_name_by_hs(context,hs_to_remove['hs_id'])
    
        while port_dns_domain_names_to_migrate.__len__() > 0:
            #Take the next HS with least amount of ports connected
            hs = hs_group_ordered.pop()
            #How many more ports can this HS handle (according to the defined ratio)
            vacancies = self.ratio - hs['port_count']
            while vacancies > 0:
                port_dns_domain_name_to_migrate = port_dns_domain_names_to_migrate.pop()
                hs_ip = get_hs_ip_by_index(context, hs['hs_id'], port_dns_domain_name_to_migrate[1])
                migrate_port(context, port_dns_domain_name_to_migrate[0], port_dns_domain_name_to_migrate[1], hs['hs_id'], hs_ip, discriminator)
                LOG.info("In DNS records - migrated port %s with index %s to HS %s with IP %s" % (port_dns_domain_name_to_migrate[0], port_dns_domain_name_to_migrate[1], hs['hs_id'], hs_ip))
                vacancies = vacancies - 1
        self.hs_lc.delete_HS(context, hs_to_remove['hs_id'])
        _delete_hs_data(context, hs_to_remove['hs_id'])

domains_table_name='domains'
records_table_name='records'
hs_data_table_name='hs_data'


def _persist_hs_data(context, tenant_id, hs_dict):
    hs_id = hs_dict['id']
    vms_ips = hs_dict['vms_ips']
    for vm_ip in vms_ips:
        index = vm_ip['index']
        ip = vm_ip['vms_ip']
        
        hs_data = dns_db.HS_Data(tenant_id = tenant_id,
                                 hs_id = hs_id,
                                 net_index = index,
                                 ip = ip
                                )
        context.session.add(hs_data)

def _delete_hs_data(context, hs_id):
    context.session.query(dns_db.HS_Data).filter(dns_db.HS_Data.hs_id == hs_id).delete(synchronize_session='fetch')
    
    
'''
Returns [{'hs_id' : id, 
          'port_count' : port_count
        }]
'''
def get_all_hs_ordered(context, tenant_id, discriminator):
    tuple_arr = context.session.query(dns_db.DNS_Record.hs_id.label('c_hs_id'), func.count(dns_db.DNS_Record.name).label('c_count_name')
                              ).filter(and_(dns_db.DNS_Record.type == 'A',
                                            dns_db.DNS_Record.discriminator == discriminator,
                                            dns_db.DNS_Record.tenant_id == tenant_id
                                            )
                              ).group_by('c_hs_id'
                              ).order_by(desc('c_count_name')
                              ).all()           
    
    result = []
    for hs_id_count_tuple in tuple_arr:
        result.append({"hs_id" : hs_id_count_tuple[0], "port_count" : hs_id_count_tuple[1]})
    
    return result

'''    
Returns [ip0, ip1, ip2]
'''
def get_hs_ip_by_index(context, hs_id, index):
    hs_data = context.session.query(dns_db.HS_Data).filter(and_(dns_db.HS_Data.hs_id == hs_id, dns_db.HS_Data.net_index == index)).one_or_none()
    return None if hs_data == None else hs_data[0].ip
    

''' 
Returns (hs_id, hs_ip, port_count) of the hs with least ports
calling code must verify the port_count is indeed below ratio 
(DAL should not include this business logic)
'''
def get_vacant_hs(context, tenant_id, discriminator):
    all_hs_ordered = get_all_hs_ordered(context, tenant_id, discriminator)
    return None if all_hs_ordered.__len__() == 0 else all_hs_ordered.pop()


def delete_records_by_port_id(context, port_id):
    #query for the domain id. this will make clearing 'records' table easier and can also be used to delete from 'domains' table.
    domain = context.session.query(dns_db.DNS_Domain).filter(dns_db.DNS_Domain.name == get_dns_domain_name(port_id)).one_or_none()
    if domain != None:
        domain_id = domain.id
    else:
        return #no records to delete for this port_id
    
    #delete domain entry
    context.session.delete(domain)
    #bulk delete records entries for this domain
    records = context.session.query(dns_db.DNS_Record).filter(dns_db.DNS_Record.domain_id == domain_id).delete(synchronize_session='fetch')
    

def get_hs_by_port_id(context, port_id, discriminator):
    record = context.session.query(dns_db.DNS_Record).filter(and_(dns_db.DNS_Record.name == get_dns_domain_name(port_id), 
                                                                   dns_db.DNS_Record.type == 'A', 
                                                                   dns_db.DNS_Record.discriminator == discriminator
                                                                   )
                                                              ).first()
    return None if record == None else record.hs_id
    

def get_hs_count(context, tenant_id, discriminator):
    hs_count = context.session.query(func.count(distinct(dns_db.DNS_Record.hs_id))).filter(and_(dns_db.DNS_Record.discriminator == discriminator, 
                                                                                                dns_db.DNS_Record.type == 'A',
                                                                                                dns_db.DNS_Record.tenant_id == tenant_id
                                                                                       )
                                                                                   ).scalar()
    return hs_count

def get_port_count(context, tenant_id, discriminator):
    port_count = context.session.query(func.count('*')).filter(and_(dns_db.DNS_Record.discriminator == discriminator, 
                                                                    dns_db.DNS_Record.type == 'A',
                                                                    dns_db.DNS_Record.tenant_id == tenant_id
                                                            )
                                                       ).scalar()
    return port_count


'''
This method returns an array of (port dns domain name, index) tuples
'''
def get_port_dns_domain_name_by_hs(context, hs_id):
    result = context.session.query(dns_db.DNS_Record.name, dns_db.DNS_Record.net_index).filter(and_(dns_db.DNS_Record.hs_id == hs_id, 
                                                                                                    dns_db.DNS_Record.type == 'A'
                                                                                                    )
                                                                                               ).all()
    return result 

    
def migrate_port(context, port_dns_domain_name_to_migrate, index, hs_id, ip, discriminator):
    port = context.session.query(dns_db.DNS_Record).filter(and_(dns_db.DNS_Record.name == port_dns_domain_name_to_migrate,
                                                                dns_db.DNS_Record.discriminator == discriminator
                                                                )
                                                           ).one_or_none()
    if port == None:
        LOG.error("attempting to migrate a non-existing port %s" % port_dns_domain_name_to_migrate)
        return
    
    port.content = ip
    port.hs_id = hs_id
    

def add_dns_mapping(context, hs_id, hs_ip, port_id, index, tenant_id, discriminator): 

    dns_domain_name = get_dns_domain_name(port_id)
    #First need to make sure a domains record does not exist for this port.
    #(can happen in case this method is called for the secondary mappings, but this method should not hold business logic, so we cannot condition on discriminator value)
    domain = context.session.query(dns_db.DNS_Domain).filter(dns_db.DNS_Domain.name == dns_domain_name).one_or_none()
    if domain == None:
        domain = dns_db.DNS_Domain(tenant_id = tenant_id,
                                   name = dns_domain_name,
                                   type = 'NATIVE'
                                   )
        context.session.add(domain)   
        context.session.flush() #we need the domain id for the records entries
    domain_id = domain.id               
    #Once we have the domain ID - add records of types A and SOA
    a_record = dns_db.DNS_Record(tenant_id = tenant_id,
                                 domain_id = domain_id,
                                 name = dns_domain_name,
                                 type = 'A',
                                 content = hs_ip,
                                 ttl = 120, 
                                 discriminator = discriminator,
                                 hs_id = hs_id,
                                 net_index = index
                                 )                             
    context.session.add(a_record)
    
    soa_record = dns_db.DNS_Record(tenant_id = tenant_id,
                                   domain_id = domain_id,
                                   name = dns_domain_name[4::],
                                   type = 'SOA',
                                   content = 'xxx',
                                   ttl = 120, 
                                   discriminator = discriminator
                                  )                             
    context.session.add(soa_record)
            
def get_hs_tenant(context, hs_id):
    tenant_id_tuple = context.session.query(dns_db.HS_Data.tenant_id).filter(dns_db.HS_Data.hs_id == hs_id).first()
    return None if tenant_id_tuple == None else tenant_id_tuple[0]    

#--------------------------------------------------------------------------------------------

def get_dns_domain_name(port_id_str):
    return 'www.'+port_id_str+'.com' 


def get_port_id(dns_domain_name):
    str_len = dns_domain_name.__len__()
    return dns_domain_name[4:str_len-4:] #remove prefix of 'www.' and suffix of '.com' - 4 chars each

#--------------------------------------------------------------------------------------------


class HSLifeCycle(object): 
    '''
    classdocs
    '''

    def __init__(self, callback_handle):
        '''
        Constructor
        '''
        self._callback_handle = callback_handle  
    
    # Returns a HS dictionary 
    def launch_new_HS(self, context, hyperswitch_data):
        return self._callback_handle.create_hyperswitch(context, hyperswitch_data)
        
    
    def delete_HS(self, context, hs_id):
        self._callback_handle.delete_hyperswitch(context, hs_id)
        
        
#--------------------------------------------------------------------------------------------
    
if __name__ == "__main__": 
    pass
    
    
    
    
    
    
     
    