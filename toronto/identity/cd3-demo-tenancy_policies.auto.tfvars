# Copyright (c) 2024, Oracle and/or its affiliates. All rights reserved.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl.
#
############################
# Identity
# Policies - tfvars
# Test workflow trigger
# Allowed Values:
# compartment_id can be the ocid or the name of the compartment hierarchy delimited by double hiphens "--"
# Example : compartment_id = "ocid1.compartment.oc1..aaaaaaaahwwiefb56epvdlzfic6ah6jy3xf3c" or compartment_id = "Security--Prod" where "Security" is the parent of "Prod" compartment
# Sample import command for Policies:
# terraform import "module.iam-policies[\"<<policies terraform variable name>>\"].oci_identity_policy.policy" <<policy ocid>>
############################
policies = {
   Demo-Policy = {
        name        = "Demo-Policy"
        compartment_id = "root"
        policy_description = "Demo Policy - Test Trigger"
        policy_statements = [ "allow group demo-group to read all-resources in tenancy"  ]
            },
 }

 

