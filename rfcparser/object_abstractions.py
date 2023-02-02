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
        self._path = path
        self.query = query
        self.fragment = fragment

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, newvalue):
        if newvalue and not newvalue.startswith('/'):
            newvalue = '/' + newvalue
        self._path = newvalue

    def get_domain(self):
        if self.ip:
            return self.ip
        return '.'.join(self.host)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            raise TypeError()

        return all(
            (self.scheme == other.scheme,
             self.ip == other.ip,
             self.port == other.port,
             self.host == other.host,
             self.userinfo == other.userinfo,
             self.path == other.path,
             self.query == other.query,
             self.fragment == other.fragment)
        )

    def __str__(self):
        hostname = self.ip or ".".join(self.host)
        port = f":{self.port}" if self.port else ""
        path = self.path if self.path else "/"
        userinfo = f"{self.userinfo}@" if self.userinfo else ""
        fragment = f"#{self.fragment}" if self.fragment else ""
        attrs = ("?" + '&'.join([f"{key}={value}" for key, value in self.query.items()])) if self.query else ""
        return f"{self.scheme}://{userinfo}{hostname}{port}{path}{attrs}{fragment}"

    def __repr__(self):
        return f"<Uri3986 {str(self)}>"
