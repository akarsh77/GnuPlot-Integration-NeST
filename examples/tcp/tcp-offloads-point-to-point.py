# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2019-2022 NITK Surathkal

########################
# SHOULD BE RUN AS ROOT
########################
from nest.topology import *
from nest.experiment import *
from nest.topology.network import Network
from nest.topology.address_helper import AddressHelper

# This program emulates point to point networks that connect two hosts `h1`
# and `h2` via two routers `r1` and `r2`. This program is similar to
# `tcp-cubic-point-to-point-3.py`. It demonstrates how to disable Generic
# Segmentation Offload (GSO), Generic Receive Offload (GRO) and TCP
# Segmentation Offload (TSO). By default, these offloads are enabled in the
# Linux kernel.

##############################################################################
#                              Network Topology                              #
#                                                                            #
#      1000mbit, 1ms -->       10mbit, 10ms -->       1000mbit, 1ms -->      #
# h1 -------------------- r1 -------------------- r2 -------------------- h2 #
#     <-- 1000mbit, 1ms       <-- 10mbit, 10ms        <-- 1000mbit, 1ms      #
#                                                                            #
##############################################################################

# This program runs for 200 seconds and creates a new directory called
# `tcp-offloads-point-to-point(date-timestamp)_dump`. It contains a `README`
# which provides details about the sub-directories and files within this
# directory. See the plots in `netperf`, `ping` and `ss` sub-directories for
# this program.

# Create two hosts `h1` and `h2`, and two routers `r1` and `r2`
h1 = Node("h1")
h2 = Node("h2")
r1 = Router("r1")
r2 = Router("r2")

# Set the IPv4 address for the networks, and not the interfaces.
# We will use the `AddressHelper` later to assign addresses to the interfaces.
n1 = Network("192.168.1.0/24")  # network on the left of `r1`
n2 = Network("192.168.2.0/24")  # network between two routers
n3 = Network("192.168.3.0/24")  # network on the right of `r2`

# Connect `h1` to `r1`, `r1` to `r2`, and then `r2` to `h2`
# `eth1` and `eth2` are the interfaces at `h1` and `h2`, respectively.
# `etr1a` is the first interface at `r1` which connects it with `h1`
# `etr1b` is the second interface at `r1` which connects it with `r2`
# `etr2a` is the first interface at `r2` which connects it with `r1`
# `etr2b` is the second interface at `r2` which connects it with `h2`
(eth1, etr1a) = connect(h1, r1, network=n1)
(etr1b, etr2a) = connect(r1, r2, network=n2)
(etr2b, eth2) = connect(r2, h2, network=n3)

# Assign IPv4 addresses to all the interfaces in the network.
AddressHelper.assign_addresses()

# Set the link attributes: `h1` --> `r1` --> `r2` --> `h2`
# Note: we enable `pfifo` queue discipline on the link from `r1` to `r2`.
# Default configuration of `pfifo` in Linux is used. For more details about
# `pfifo` in Linux, use this command on CLI: `man tc-pfifo`.
eth1.set_attributes("1000mbit", "1ms")  # from `h1` to `r1`
etr1b.set_attributes("10mbit", "10ms", "pfifo")  # from `r1` to `r2`
etr2b.set_attributes("1000mbit", "1ms")  # from `r2` to `h2`

# Set the link attributes: `h2` --> `r2` --> `r1` --> `h1`
eth2.set_attributes("1000mbit", "1ms")  # from `h2` to `r2`
etr2a.set_attributes("10mbit", "10ms")  # from `r2` to `r1`
etr1a.set_attributes("1000mbit", "1ms")  # from `r1` to `h1`

# Set default routes in all hosts and routers.
h1.add_route("DEFAULT", eth1)
h2.add_route("DEFAULT", eth2)
r1.add_route("DEFAULT", etr1b)
r2.add_route("DEFAULT", etr2a)

# Disable GSO, GRO and TSO. For more details about offloads, visit this link:
# https://www.kernel.org/doc/Documentation/networking/segmentation-offloads.txt
offload_type = ["gso", "gro", "tso"]
eth1.disable_offload(offload_type)
etr1b.disable_offload(offload_type)
etr2a.disable_offload(offload_type)
eth2.disable_offload(offload_type)

# Set up an Experiment. This API takes the name of the experiment as a string.
exp = Experiment("tcp-offloads-point-to-point")

# Configure a flow from `h1` to `h2`.
flow1 = Flow(h1, h2, eth2.get_address(), 0, 200, 1)

# Use `flow1` as a TCP flow. TCP CUBIC is default in Linux.
exp.add_tcp_flow(flow1)

# Run the experiment
exp.run()
