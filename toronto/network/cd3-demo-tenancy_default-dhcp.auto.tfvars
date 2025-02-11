# Copyright (c) 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
############################
# Network
# Major Objects - Default DHCP - tfvars
# Allowed Values:
# manage_default_resource_id can be the ocid or the key of vcns (map)
# Sample import command for Default DHCP:
# terraform import "module.default-dhcps[\"<<default_dhcps terraform variable name>>\"].oci_core_default_dhcp_options.default_dhcp_option" <<default dhcp ocid>>
############################
default_dhcps = {
    cd3_demo_vcn_Default-DHCP-Options-for-cd3_demo_vcn = {
            server_type          = "VcnLocalPlusInternet"
            manage_default_resource_id = "cd3_demo_vcn" # can be vcn name or default dhcp ocid
    },
}