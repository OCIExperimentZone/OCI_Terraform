# Copyright (c) 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
############################
# Network
# Major Objects - Route Table - tfvars
# Allowed Values:
# vcn_id can be the ocid or the key of vcns (map)
# compartment_id can be the ocid or the name of the compartment hierarchy delimited by double hiphens "--"
# Example : compartment_id = "ocid1.compartment.oc1..aaaaaaaahwwiefb56epvdlzfic6ah6jy3xf3c" or compartment_id = "Network-root-cpt--Network" where "Network-root-cpt" is the parent of "Network" compartment
# Sample import command for Route Table:
# terraform import "module.route-tables[\"<<route_tables terraform variable name>>\"].oci_core_route_table.route_table" <<route table ocid>>
############################
route_tables = {
  # Route Table map #
  # Start of #toronto_cd3_demo_vcn_RT1# #
    cd3_demo_vcn_RT1 = {
        compartment_id = "root"
        vcn_id     = "cd3_demo_vcn"
        display_name     = "RT1"
        ### gateway_route_table for #toronto_cd3_demo_vcn_RT1# ##
        route_rules_igw = [
                ## Start Route Rule toronto_cd3_demo_vcn_RT1_cd3_demo_vcn_cd3_demo_vcn_igw_0.0.0.0/0
            {
                  network_entity_id = "cd3_demo_vcn_cd3_demo_vcn_igw"
                  description       = ""
                  destination       = "0.0.0.0/0"
                  destination_type  = "CIDR_BLOCK"
                 },
            ## End Route Rule toronto_cd3_demo_vcn_RT1_cd3_demo_vcn_cd3_demo_vcn_igw_0.0.0.0/0
####ADD_NEW_IGW_RULES #toronto_cd3_demo_vcn_RT1# ####
        ]
        route_rules_sgw = [
    ####ADD_NEW_SGW_RULES #toronto_cd3_demo_vcn_RT1# ####
        ]
        route_rules_ngw = [
    ####ADD_NEW_NGW_RULES #toronto_cd3_demo_vcn_RT1# ####
        ]
        route_rules_drg = [
    ####ADD_NEW_DRG_RULES #toronto_cd3_demo_vcn_RT1# ####
        ]
        route_rules_lpg = [
    ####ADD_NEW_LPG_RULES #toronto_cd3_demo_vcn_RT1# ####
        ]
        route_rules_ip = [
    ####ADD_NEW_IP_RULES #toronto_cd3_demo_vcn_RT1# ####
        ]
        defined_tags = {
                "n"= ""
        }
        freeform_tags = {}
      },
  # End of #toronto_cd3_demo_vcn_RT1# #
##Add New Route Tables for toronto here##
}