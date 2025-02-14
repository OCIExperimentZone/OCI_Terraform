variable "tenancy_ocid" {
  description = "The OCID of your tenancy"
  type        = string
}

variable "user_ocid" {
  description = "The OCID of the user"
  type        = string
}

variable "fingerprint" {
  description = "The fingerprint of the key"
  type        = string
}

variable "private_key_path" {
  description = "The path to the private key"
  type        = string
}

variable "region" {
  description = "The region to provision resources in"
  type        = string
}
