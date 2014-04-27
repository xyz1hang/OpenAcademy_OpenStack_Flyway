__author__ = 'hydezhang'
from enum import Enum


class ResourceType(Enum):
    user = "user"
    tenant = "tenant"
    image = "image"
    keypair = "keypair"
    resource = "resource"
    flavor = "flavor"
    vm = "VM"
    default = "unknown resource"
