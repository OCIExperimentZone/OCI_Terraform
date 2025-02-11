# Copyright (c) 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
############################
# Network
# Major Objects - Default Security List - tfvars
# Sample import command for Default Security List:
# terraform import "module.default-security-lists[\"<<default_seclists terraform variable name>>\"].oci_core_default_security_list.default_security_list" <<default security list ocid>>
############################
default_seclists = {
  # Seclist map #
  # Start of #toronto_cd3_demo_vcn_Default-Security-List-for-cd3_demo_vcn# #
  cd3_demo_vcn_Default-Security-List-for-cd3_demo_vcn = {
        compartment_id = "root"
        vcn_id     = "cd3_demo_vcn"
        display_name     = "Default Security List for cd3_demo_vcn"
        ingress_sec_rules = [
             {  #cd3_demo_vcn_Default-Security-List-for-cd3_demo_vcn_0.0.0.0/0#
                protocol = "1"
                source = "0.0.0.0/0"
                options = {
                    icmp = []
                }
             },
             {  #cd3_demo_vcn_Default-Security-List-for-cd3_demo_vcn_0.0.0.0/0#
                protocol = "6"
                source = "0.0.0.0/0"
                options = {
                    tcp= [{
                        destination_port_range_max = "22"
                        destination_port_range_min = "22"
                    }]
                }
             },
             {  #cd3_demo_vcn_Default-Security-List-for-cd3_demo_vcn_192.168.0.0/24#
                protocol = "1"
                source = "192.168.0.0/24"
                options = {
                    icmp = []
                }
             },
####ADD_NEW_INGRESS_SEC_RULES #toronto_cd3_demo_vcn_Default-Security-List-for-cd3_demo_vcn# ####
        ]
        egress_sec_rules = [
             {
                protocol = "all"
                destination = "0.0.0.0/0"
                options = {
                    all = []
                }
             },
####ADD_NEW_EGRESS_SEC_RULES #toronto_cd3_demo_vcn_Default-Security-List-for-cd3_demo_vcn# ####
        ]
      },
  # End of #toronto_cd3_demo_vcn_Default-Security-List-for-cd3_demo_vcn# #
##Add New Default Seclists for toronto here##
}