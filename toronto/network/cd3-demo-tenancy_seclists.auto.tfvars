# Copyright (c) 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
############################
# Network
# Major Objects - Security List - tfvars
# Allowed Values:
# vcn_id can be the ocid or the key of vcns (map)
# compartment_id can be the ocid or the name of the compartment hierarchy delimited by double hiphens "--"
# Example : compartment_id = "ocid1.compartment.oc1..aaaaaaaahwwiefb56epvdlzfic6ah6jy3xf3c" or compartment_id = "Network-root-cpt--Network" where "Network-root-cpt" is the parent of "Network" compartment
# Sample import command for Security List:
# terraform import "module.security-lists[\"<<seclists terraform variable name>>\"].oci_core_security_list.security_list" <<security list ocid>>
############################
seclists = {
  # Seclist map #
  # Start of #toronto_cd3_demo_vcn_SL1# #
  cd3_demo_vcn_SL1 = {
        compartment_id = "root"
        vcn_id     = "cd3_demo_vcn"
        display_name     = "SL1"
        ingress_sec_rules = [
             {  #cd3_demo_vcn_SL1_192.168.0.0/24#
                protocol = "all"
                source = "192.168.0.0/24"
                description = ""
                options = {
                    all = []
                }
             },
####ADD_NEW_INGRESS_SEC_RULES #toronto_cd3_demo_vcn_SL1# ####
        ]
        egress_sec_rules = [
             {
                protocol = "all"
                destination = "0.0.0.0/0"
                description = ""
                options = {
                    all = []
                }
             },
####ADD_NEW_EGRESS_SEC_RULES #toronto_cd3_demo_vcn_SL1# ####
        ]
        defined_tags = {
                "n"= ""
        }
      },
  # End of #toronto_cd3_demo_vcn_SL1# #
##Add New Seclists for toronto here##
}