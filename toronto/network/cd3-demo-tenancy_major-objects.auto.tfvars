# Copyright (c) 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
############################
# Network
# Major Objects - VCNs, IGW, NGW, SGW, LPG, DRG - tfvars
# Allowed Values:
# compartment_id can be the ocid or the name of the compartment hierarchy delimited by double hiphens "--"
# Example : compartment_id = "ocid1.compartment.oc1..aaaaaaaahwwiefb56epvdlzfic6ah6jy3xf3c" or compartment_id = "Network--Prod" where "Network" is the parent of "Prod" compartment
# Sample import command for VCN:
# terraform import "module.vcns[\"<<vcns terraform variable name>>\"].oci_core_vcn.vcn" <<vcn ocid>>
############################
vcns = {
  cd3_demo_vcn = {
        compartment_id = "root"
        cidr_blocks      = ["192.168.0.0/24"]
        display_name     = "cd3_demo_vcn"
        dns_label      = "cd3demovcn"
      },
}
############################
# Network
# Major Objects - IGW - tfvars
# Allowed Values:
# vcn_id can be the ocid or the key of vcns (map)
# compartment_id can be the ocid or the name of the compartment hierarchy delimited by double hiphens "--"
# Example : compartment_id = "ocid1.compartment.oc1..aaaaaaaahwwiefb56epvdlzfic6ah6jy3xf3c" or compartment_id = "Network--Prod" where "Network" is the parent of "Prod" compartment
# Sample import command for IGW:
# terraform import "module.igws[\"<<igws terraform variable name>>\"].oci_core_internet_gateway.internet_gateway" <<igw ocid>>
############################
igws = {
  cd3_demo_vcn_cd3_demo_vcn_igw = {
        compartment_id = "root"
        vcn_id     = "cd3_demo_vcn"
        igw_name   = "cd3_demo_vcn_igw"
      },
}
############################
# Network
# Major Objects - NGW - tfvars
# Allowed Values:
# vcn_id can be the ocid or the key of vcns (map)
# compartment_id can be the ocid or the name of the compartment hierarchy delimited by double hiphens "--"
# Example : compartment_id = "ocid1.compartment.oc1..aaaaaaaahwwiefb56epvdlzfic6ah6jy3xf3c" or compartment_id = "Network--Prod" where "Network" is the parent of "Prod" compartment
# Sample import command for NGW:
# terraform import "module.ngws[\"<<ngws terraform variable name>>\"].oci_core_nat_gateway.nat_gateway" <<nat gateway ocid>>
############################
ngws = {
  cd3_demo_vcn_cd3_demo_vcn_ngw = {
        compartment_id = "root"
        vcn_id     = "cd3_demo_vcn"
        ngw_name     = "cd3_demo_vcn_ngw"
      },
}
############################
# Network
# Major Objects - SGW - tfvars
# Allowed Values:
# vcn_id can be the ocid or the key of vcns (map)
# compartment_id can be the ocid or the name of the compartment hierarchy delimited by double hiphens "--"
# Example : compartment_id = "ocid1.compartment.oc1..aaaaaaaahwwiefb56epvdlzfic6ah6jy3xf3c" or compartment_id = "Network--Prod" where "Network" is the parent of "Prod" compartment
# Sample import command for SGW:
# terraform import "module.sgws[\"<<sgws terraform variable name>>\"].oci_core_service_gateway.service_gateway" <<sgw ocid>>
############################
sgws = {
 }
############################
# Network
# Major Objects - LPG - tfvars
# Allowed Values:
# vcn_id can be the ocid or the key of vcns (map)
# compartment_id can be the ocid or the name of the compartment hierarchy delimited by double hiphens "--"
# Example : compartment_id = "ocid1.compartment.oc1..aaaaaaaahwwiefb56epvdlzfic6ah6jy3xf3c" or compartment_id = "Network--Prod" where "Network" is the parent of "Prod" compartment
# Sample import command for LPG:
# terraform import "module.hub-lpgs[\"<<lpgs terraform variable name>>\"].oci_core_local_peering_gateway.local_peering_gateway" <<lpg ocid>>
# terraform import "module.spoke-lpgs[\"<<lpgs terraform variable name>>\"].oci_core_local_peering_gateway.local_peering_gateway" <<lpg ocid>>
# terraform import "module.peer-lpgs[\"<<lpgs terraform variable name>>\"].oci_core_local_peering_gateway.local_peering_gateway" <<lpg ocid>>
# terraform import "module.none-lpgs[\"<<lpgs terraform variable name>>\"].oci_core_local_peering_gateway.local_peering_gateway" <<lpg ocid>>
# terraform import "module.exported-lpgs[\"<<lpgs terraform variable name>>\"].oci_core_local_peering_gateway.local_peering_gateway" <<lpg ocid>>
############################
lpgs = {
    hub-lpgs = {
                },
    spoke-lpgs = {
                },
    peer-lpgs = {
                },
    none-lpgs  = {
                },
    exported-lpgs = {
                },
}