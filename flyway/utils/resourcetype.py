__author__ = 'hydezhang'
from enum import Enum


class ResourceType(Enum):
    user = "user"
    tenant = "tenant"
    image = "image"
    resource = "resource"
    flavor = "flavor"
    vm = "vm"
    default = "unknown"
