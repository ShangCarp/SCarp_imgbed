#!/usr/bin/python
import subprocess

from mininet.topo import Topo
from mininet.node import Host
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.cli import CLI

from time import sleep
from argparse import ArgumentParser
from util import *

import os

parser = ArgumentParser(description='Args for reproduce convergence and fairness test')

parser.add_argument('--cc', '-c', type=str, help='Congestion control algorithm to be tested', required=True)

args = parser.parse_args()

class FairnessTopo(Topo):
    def build(self):
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        r1 = self.addHost('r1')
        self.addLink(h1, r1)
        self.addLink(h2, r1, bw=100, delay='10ms', max_queue_size=1317) # One-way-delay is 10ms, RTT is 20ms;
        # 1BDP = 10^8 * 20*10^-3 /1518 = 1317 (pkts)

def fairness_evaluation(net,cc_name,inter_flow_time = 1,num_flows = 10):
    os.system('sysctl -w net.ipv4.tcp_congestion_control={}'.format(cc_name))
    # XXX: make sure the cc_name is valid!
    dname = 'cca-%s' % cc_name
    if not os.path.exists(dname):
        os.makedirs(dname)

    start_tcpdump(net,dname,cc_name)
    start_iperf(net, inter_flow_time, num_flows)
    stop_iperf()
    stop_tcpdump()

if __name__ == '__main__':
    topo = FairnessTopo()
    net = Mininet(topo=topo, link=TCLink, controller=None)
    config_ip(net)

    net.start()

    CLI(net)
    cc_name = args.cc
    fairness_evaluation(net,cc_name)

    net.stop()
