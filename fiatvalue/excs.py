class APIError(Exception):
    def __init__(self, message, response):
        super(APIError, self).__init__(message)
        self.response = response
