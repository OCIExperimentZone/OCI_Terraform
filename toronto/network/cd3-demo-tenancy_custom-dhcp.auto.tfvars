# Copyright (c) 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
############################
# Network
# Custom DHCP - tfvars
# Allowed Values:
# vcn_id can be the ocid or the key of vcns (map)
# compartment_id can be the ocid or the name of the compartment hierarchy delimited by double hiphens "--"
# Example : compartment_id = "ocid1.compartment.oc1..aaaaaaaahwwiefb56epvdlzfic6ah6jy3xf3c" or compartment_id = "Network--Prod" where "Network" is the parent of "Prod" compartment
# Sample import command for Custom DHCP:
# terraform import "module.custom-dhcps[\"<<custom_dhcp terraform variable name>>\"].oci_core_dhcp_options.custom_dhcp_option" <<custom dhcp ocid>>
############################
custom_dhcps = {
        cd3_demo_vcn_dhcp-interna = {
            compartment_id           = "root"
            server_type              = "VcnLocalPlusInternet"
            display_name     = "dhcp-interna"
            vcn_id           = "cd3_demo_vcn"
            search_domain        =  {
                names = ["oci.com"]
            }
    },
}