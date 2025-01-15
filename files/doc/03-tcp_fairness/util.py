from time import sleep
from subprocess import Popen

def config_ip(net):
    h1, h2, r1 = net.get('h1', 'h2', 'r1')
    h1.cmd('ifconfig h1-eth0 10.0.1.11/24')
    h1.cmd('route add default gw 10.0.1.1')

    h2.cmd('ifconfig h2-eth0 10.0.2.22/24')
    h2.cmd('route add default gw 10.0.2.1')

    r1.cmd('ifconfig r1-eth0 10.0.1.1/24')
    r1.cmd('ifconfig r1-eth1 10.0.2.1/24')
    r1.cmd('echo 1 > /proc/sys/net/ipv4/ip_forward')

    for n in [ h1, h2, r1 ]:
        for intf in n.intfList():
            intf.updateAddr()

def start_tcpdump(net,dname,cc_name):
    h2 = net.get("h2")
    h2.popen("tcpdump -w ./{}/{}.pcap -i h2-eth0 -n".format(dname,cc_name))

def start_iperf(net, inter_flow_time, num_flows):
    # todo: start tcpdump
    h1, h2 = net.get('h1', 'h2')
    print( 'Start iperf ...')
    # start servers
    for i in range(num_flows):
        target_port = 5201+i # iperf basic port is 5201
        h2.popen('iperf -s -p {} -D'.format(target_port))
    # start clients
    for i in range(num_flows):
        on_duration = 2*inter_flow_time*(num_flows-i-1)+1
        target_port = 5201+i
        h1.popen("iperf -c {} -p {} -t {}".format(h2.IP(),target_port,on_duration))
        print("Flow {} starts for {} seconds, target port is {}".format(i,on_duration,target_port))
        sleep(inter_flow_time)
    # wait for all flows to finished
    sleep(inter_flow_time*(num_flows+1))

def stop_iperf():
    print( 'Kill iperf ...')
    Popen('pgrep -f iperf | xargs kill -9', shell=True).wait()

def stop_tcpdump():
    print("kill tcpdump ...")
    Popen("pkill tcpdump",shell=True).wait()
