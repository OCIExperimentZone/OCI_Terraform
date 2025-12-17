# Copyright (c) 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
############################
# Network
# Major Objects - Default Route Table - tfvars
# Sample import command for Default Route Table:
# terraform import "module.default-route-tables[\"<<default_route_table terraform variable name>>\"].oci_core_default_route_table.default_route_table" <<default route table ocid>>
############################
default_route_tables = {
  # Route Table map #
  # Start of #toronto_cd3_demo_vcn_Default-Route-Table-for-cd3_demo_vcn# #
    cd3_demo_vcn_Default-Route-Table-for-cd3_demo_vcn = {
        compartment_id = "root"
        vcn_id     = "cd3_demo_vcn"
        display_name     = "Default Route Table for cd3_demo_vcn"
        ### gateway_route_table for #toronto_cd3_demo_vcn_Default-Route-Table-for-cd3_demo_vcn# ##
        route_rules_igw = [
    ####ADD_NEW_IGW_RULES #toronto_cd3_demo_vcn_Default-Route-Table-for-cd3_demo_vcn# ####
        ]
        route_rules_sgw = [
    ####ADD_NEW_SGW_RULES #toronto_cd3_demo_vcn_Default-Route-Table-for-cd3_demo_vcn# ####
        ]
        route_rules_ngw = [
    ####ADD_NEW_NGW_RULES #toronto_cd3_demo_vcn_Default-Route-Table-for-cd3_demo_vcn# ####
        ]
        route_rules_drg = [
    ####ADD_NEW_DRG_RULES #toronto_cd3_demo_vcn_Default-Route-Table-for-cd3_demo_vcn# ####
        ]
        route_rules_lpg = [
    ####ADD_NEW_LPG_RULES #toronto_cd3_demo_vcn_Default-Route-Table-for-cd3_demo_vcn# ####
        ]
        route_rules_ip = [
    ####ADD_NEW_IP_RULES #toronto_cd3_demo_vcn_Default-Route-Table-for-cd3_demo_vcn# ####
        ]
        defined_tags = {}
        freeform_tags = {}
      },
  # End of #toronto_cd3_demo_vcn_Default-Route-Table-for-cd3_demo_vcn# #
##Add New Default Route Tables for toronto here##
}