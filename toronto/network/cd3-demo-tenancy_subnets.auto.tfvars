# Copyright (c) 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
#############################
# Network
# Major Objects - Subnets - tfvars
# Allowed Values:
# vcn_id, route_table_id, dhcp_options_id can be the ocid or the key of vcns (map), route_tables (map) and dhcp_options (map) respectively
# security_list_ids can be a list of ocids or the key of security_lists (map)
# compartment_id can be the ocid or the name of the compartment hierarchy delimited by double hiphens "--"
# Example : compartment_id = "ocid1.compartment.oc1..aaaaaaaahwwiefb56epvdlzfic6ah6jy3xf3c" or compartment_id = "Network-root-cpt--Network" where "Network-root-cpt" is the parent of "Network" compartment
# Sample import command for Subnet:
# terraform import "module.subnets[\"<<subnets terraform variable name>>\"].oci_core_subnet.subnet" <<subnet ocid>>
#############################
subnets = {
  # Subnets map #
  cd3_demo_vcn_cd3_demo_vcn = {
        cidr_block = "192.168.0.0/24"
        compartment_id= "root"
        vcn_id = "cd3_demo_vcn"
        display_name = "cd3_demo_vcn"
        prohibit_public_ip_on_vnic = "true"
        route_table_id = "cd3_demo_vcn_RT1"
        dhcp_options_id = "cd3_demo_vcn_dhcp-interna" 
        security_list_ids = ["cd3_demo_vcn_SL1"]
        defined_tags = {
                "n"= ""
        }
      },
##Add New Subnets for toronto here##
}