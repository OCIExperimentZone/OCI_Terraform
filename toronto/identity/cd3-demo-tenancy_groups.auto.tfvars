# Copyright (c) 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
############################
# Identity
# Groups - tfvars
# Sample import command for groups:
# terraform import "module.groups[\"<<groups terraform variable name>>\"].oci_identity_domains_group.group[0]" idcsEndpoint/<<idcsEndpoint>>/groups/<<groupId>>
# terraform import "module.groups[\"<<dynamic group terraform variable name>>\"].oci_identity_domains_dynamic_resource_group.dynamic_group[0]" idcsEndpoint/<<idcsEndpoint>>/dynamicResourceGroups/<<dynamicResourceGroupId>>
############################
identity_domain_groups = {
  DEFAULT_demo-group = {
        group_name        = "demo-group"
        group_description = "Group for CD3 test"
        idcs_endpoint = "DEFAULT"
        domain_compartment_id = "root"
    },
  }