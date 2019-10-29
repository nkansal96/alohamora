"""
This module implements the syntax and composition of NGINX configuration blocks. It also implements
helper functions to help compose those blocks and automatically generate the resulting configuration.
"""

from typing import List, Tuple, Optional


def quote(s: str) -> str:
    """
    Quotes a string and escapes special characters inside the string. It also removes $ from the string
    since those are not allowed in NGINX strings (unless referencing a variable).

    :param s: The string to quote
    :return: The quoted string
    """
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'").replace("$", "") + "'"


class Block:
    """
    Defines the base Block class, which implements the functions to generate each block of the nginx configuration
    """

    def __init__(
        self,
        *,
        indent_level: int,
        block_name: str,
        block_name_args: Optional[List[str]] = None,
        block_args: Optional[List[Tuple[str, ...]]] = None,
        sub_blocks: Optional[List["Block"]] = None,
    ):
        self.indent_level = indent_level
        self.block_name = block_name
        self.block_name_args = block_name_args or []
        self.block_args = block_args or []
        self.sub_blocks = sub_blocks or []

    def _header(self):
        args_str = " ".join(self.block_name_args) if self.block_name_args else " "
        return f"{self.block_name}{args_str}{{"

    def _body_lines(self):
        if not self.block_args:
            return []
        key_len = max(map(len, [a[0] for a in self.block_args])) + 1
        return [f"{k:<{key_len}} {' '.join(v)};" for k, *v in self.block_args if v and all(v)]

    def _trailer(self):
        return "}"

    def __str__(self):
        lines = [
            ("\t" * self.indent_level) + self._header(),
            *["\t" * (self.indent_level + 1) + line for line in self._body_lines()],
            *["\n" + str(block) for block in self.sub_blocks],
            ("\t" * self.indent_level) + self._trailer(),
        ]
        return "\n".join(lines)


class LocationBlock(Block):
    """
    Defines a location block
    """

    def __init__(
        self,
        *,
        indent_level: int,
        uri: str,
        file_name: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        content_type: Optional[str] = None,
        exact_match: bool = True,
        sub_blocks: Optional[List[Block]] = None,
    ):
        """
        :param indent_level: The indentation level to place this block
        :param uri: The URI that this block should match
        :param file_name: The file to send as a response for this block
        :param redirect_uri: The URI to redirect to for this block
        :param content_type: The content type to return for the file sent from this block
        :param exact_match: Whether or not this block should perform an exact match
        :param sub_blocks: Any sub-blocks to add inside this block
        """
        uri = quote(uri)
        matcher = " = " if exact_match else " "
        file_name = "/" + file_name if file_name else "$uri"
        content_type = quote(content_type) if content_type else None
        redirect_uri = quote(redirect_uri) if redirect_uri else None

        super().__init__(
            indent_level=indent_level,
            block_name=f"location{matcher}{uri}",
            block_args=[
                ("default_type", content_type),
                ("try_files", f"{file_name} =404" if not redirect_uri else None),
                ("return", f"301 {redirect_uri}" if redirect_uri else None),
            ],
            sub_blocks=sub_blocks,
        )

    def add_header(self, key: str, value: str):
        """
        Adds a header to the response for this block

        :param key: The header name
        :param value: The header value
        """
        self.block_args.append(("add_header", quote(key), quote(value)))

    def add_push(self, uri: str):
        """
        Pushes the given URI along with the response for this block

        :param uri: The URI to push
        """
        self.block_args.append(("http2_push", quote(uri)))

    def add_preload(self, uri: str, as_type: str):
        """
        Adds a Link rel=preload header for this block

        :param uri: The URL to preload
        :param as_type: The type of the object being preloaded (see ResourceType)
        """
        type_map = {"CSS": "style", "SCRIPT": "script", "FONT": "font", "IMAGE": "image", "HTML": "document"}
        as_type = type_map.get(as_type, "other")
        self.block_args.append(("add_header", quote("Link"), quote(f"<{uri}>; rel=preload; as={as_type}; nopush")))


class TypesBlock(Block):
    """
    Defines an empty `types` block to override the default mime types and allow us to set arbitary content types
    through the Content-type header
    """

    def __init__(self, *, indent_level: int):
        super().__init__(indent_level=indent_level, block_name="types")


class RedirectByLuaBlock(Block):
    """
    Implements redirection using LUA since NGINX does not give us the exact matching we need
    """

    def __init__(self, *, indent_level: int):
        super().__init__(indent_level=indent_level, block_name="rewrite_by_lua_block")
        self.rewrite_rules = {}
        self.script_template = [
            "local function common_prefix_len(a, b)",
            [
                "local m = math.min(string.len(a), string.len(b))",
                "for i=0,m do",
                ["if a[i] ~= b[i] then", ["return i"], "end"],
                "end",
                "return m",
            ],
            "end",
            "",
            "local uri_map = {",
            self._generate_lua_rewrite_rules,
            "}",
            "local uri = ngx.unescape_uri(ngx.var.request_uri)",
            "for k, v in pairs(uri_map) do",
            ["if k == uri then", ["ngx.log(ngx.INFO, 'exact redirect ', uri, ' ', v)", "ngx.exec(v)", "return"], "end"],
            "end",
            "",
            "local best_match = nil",
            "local match_len = 0",
            "for k, v in pairs(uri_map) do",
            [
                "if string.match(k, '^.*%?') == string.match(uri, '^.*%?') then",
                [
                    "local l = common_prefix_len(k, uri)",
                    "if l > match_len then",
                    ["match_len = l", "best_match = v"],
                    "end",
                ],
                "end",
            ],
            "end",
            "",
            "if best_match then",
            ["ngx.log(ngx.INFO, 'best match redirect ', uri, ' ', best_match)", "ngx.exec(best_match)"],
            "end",
        ]

    def add_rewrite_rule(self, from_uri: str, to_uri: str):
        """
        Add a rewrite rule implemented in Lua

        :param from_uri: The original URI
        :param to_uri: The URI to map to
        """
        self.rewrite_rules[from_uri] = to_uri

    def _body_lines(self):
        def expand(rules: List, level: int):
            expanded = []
            for rule in rules:
                if callable(rule):
                    expanded.extend((level, rule()))
                else:
                    expanded.append((level, rule))
            return expanded

        s = list(reversed(expand(self.script_template, 0)))
        script_lines = []

        while s:
            (lev, curr) = s.pop()
            if isinstance(curr, str):
                script_lines.append(("\t" * lev) + curr)
            elif isinstance(curr, list):
                s.extend(reversed(expand(curr, lev + 1)))
            else:
                s.extend(reversed(expand([curr], lev)))

        return script_lines

    def _generate_lua_rewrite_rules(self):
        return [f"[ngx.unescape_uri('{k}')] = '{v}'," for k, v in self.rewrite_rules.items()]


class ServerBlock(Block):
    """
    Implements a virtual server block and provides functions to add Location blocks. It also
    maintains the state of the RewriteByLuaBlock to ensure correct URI rewriting
    """

    def __init__(
        self,
        *,
        indent_level: int,
        server_name: str,
        server_addr: str,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        root: Optional[str] = None,
    ):
        super().__init__(
            indent_level=indent_level,
            block_name="server",
            block_args=[
                ("listen", f"{server_addr}:443 ssl http2"),
                ("server_name", server_name),
                ("ssl_certificate", cert_path),
                ("ssl_certificate_key", key_path),
                ("root", root),
            ],
        )

        # Create an empty types block so that we can manually set the content type using the proto headers
        self.sub_blocks.append(TypesBlock(indent_level=self.indent_level + 1))

        # Create a catch-all block that will try to match the incoming request to the correct response using Lua
        self.lua_block = RedirectByLuaBlock(indent_level=self.indent_level + 2)
        self.sub_blocks.append(
            LocationBlock(indent_level=self.indent_level + 1, uri="/", exact_match=False, sub_blocks=[self.lua_block])
        )

    def add_location_block(self, **kwargs) -> LocationBlock:
        """
        Adds a Location block with an internal URI and configures Lua to route requests to the given URI to the
        internal one
        :param kwargs: The arguments to `Location()`
        :return: The created LocationBlock
        """
        # Create a URI mapping first
        new_uri = f"/_internal_{len(self.sub_blocks)}"
        self.lua_block.add_rewrite_rule(kwargs["uri"], new_uri)
        kwargs.pop("uri")
        # Then create the location block
        block = LocationBlock(indent_level=self.indent_level + 1, uri=new_uri, **kwargs)
        self.sub_blocks.append(block)
        return block


class HttpBlock(Block):
    """
    Implements the http block and provides a convenience function to add virtual servers
    """

    def __init__(self, *, indent_level: int):
        super().__init__(
            indent_level=indent_level,
            block_name="http",
            block_args=[
                ("sendfile", "on"),
                ("access_log", "/var/log/nginx/access.log"),
                ("error_log", "/var/log/nginx/error.log", "info"),
            ],
        )

    def add_server(self, *, server_name: str, server_addr: str, **kwargs) -> ServerBlock:
        """
        Add a virtual server

        :param server_name: The domain name for this server to handle requests for
        :param server_addr: The IP address to bind on
        :param kwargs: Additional arguments to pass to `Server()`
        :return: The created ServerBlock
        """
        block = ServerBlock(
            indent_level=self.indent_level + 1, server_name=server_name, server_addr=server_addr, **kwargs
        )
        self.sub_blocks.append(block)
        return block


class EventsBlock(Block):
    """
    Implements an events block to configure nginx to run asynchronously (required)
    """

    def __init__(self, *, indent_level: int, worker_connections: int = 1024):
        super().__init__(
            indent_level=indent_level, block_name="events", block_args=[("worker_connections", str(worker_connections))]
        )


class Config(Block):
    """
    The top-level NGINX configuration block with special functions to generate the configuration
    """

    def __init__(self):
        super().__init__(
            indent_level=0,
            block_name="",
            block_args=[("daemon", "off"), ("worker_processes", "auto"), ("user", "root")],
        )
        self.http_block = HttpBlock(indent_level=0)
        self.sub_blocks.append(EventsBlock(indent_level=0))
        self.sub_blocks.append(self.http_block)

    def __str__(self):
        return "\n".join(self._body_lines()) + "\n" + "\n\n".join(map(str, self.sub_blocks))
