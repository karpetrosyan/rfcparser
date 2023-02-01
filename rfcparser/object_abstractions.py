class SetCookie6265:
    def __init__(self, key, value, attrs):
        self.key = key
        self.value = value
        self.attrs = attrs


class Uri3986:
    def __init__(self, scheme, ip, port, host, userinfo, path, query, fragment):
        self.scheme = scheme
        self.ip = ip
        self.port = port
        self.host = host
        self.userinfo = userinfo
        self.path = path
        self.query = query
        self.fragment = fragment

    def __str__(self):
        hostname = self.ip or ".".join(self.host)
        port = f":{self.port}" if self.port else ""
        path = self.path if self.path else ""
        return f"<Uri3986 {self.scheme}://{hostname}{port}{path}>"
