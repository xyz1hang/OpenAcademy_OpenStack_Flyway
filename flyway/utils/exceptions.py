from utils.resourcetype import ResourceType


class ResourceNotFoundException(Exception):

    def __init__(self, resource_type=ResourceType.default, resource_id="",
                 cloud=None):
        Exception.__init__(self, self.__class__.__name__)
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.cloud = cloud

    def __str__(self):
        return "{0:s} not found. [id: {1:s}] [cloud: {2:s}]".format(
            self.resource_type,
            self.resource_id or "?",
            self.cloud or "?")


class HttpRequestException(Exception):

    def __init__(self, code, state, response_body):
        self.exception_message = "[HTTP {0}]: {1} \n" + "Details: {2}"\
            .format(code, state, response_body)

    def __str__(self):
        return self.exception_message