from datetime import datetime


def default_path(uri):
    uri_path = uri.path

    if uri_path is None:
        return "/"
    if uri_path.count("/") == 1:
        return "/"
    return ''.join(uri_path.split('/')[:-1])


class SetCookie6265:
    def __init__(self,
                 key,
                 value,
                 uri,
                 attrs):
        self.key = key
        self.value = value
        self.creation_time = self.last_access_time = datetime.now()
        self.persistent_flag = False
        self.expiry_time = None
        self.domain = attrs.get('Domain', "")

        max_age = attrs.get('Max-Age', None)
        if max_age:
            self.persistent_flag = True
            self.expiry_time = max_age
        else:
            expires = attrs.get('Expires', None)
            if expires:
                self.persistent_flag = True
                self.expiry_time = expires

        path = attrs.get("Path", None)
        if path:
            self.path = path
        else:
            self.path = default_path(uri)
        secure = attrs.get('Secure', False)
        self.secure_only_flag = secure
        httponly = attrs.get("HttpOnly", False)
        self.http_only_flag = httponly

    def __str__(self):
        return f"{self.key}={self.value}"

    def __repr__(self):
        return f"<SetCookie6265 {str(self)} {self.creation_time=} {self.expiry_time=} {self.path=} " \
               f"{self.persistent_flag=} {self.http_only_flag=} {self.domain=} {self.last_access_time=}>" \
               f"{self.secure_only_flag=}"


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

    def updated_relative_ref(self, value):
        hostname = self.ip or ".".join(self.host)
        port = f":{self.port}" if self.port else ""
        userinfo = f"{self.userinfo}@" if self.userinfo else ""

        if value.startswith('//'):
            return f"{self.scheme}:{value}"
        else:
            return f"{self.scheme}://{userinfo}{hostname}{port}{value}"

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
