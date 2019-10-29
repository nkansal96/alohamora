from typing import List, Tuple, Optional

QUERY_REPLACE = "__._._.__"


def quote(s: str) -> str:
    return "'" + s.replace("\\", "\\\\").replace("'", "\\'").replace("$", "") + "'"


class Block:
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
    def __init__(
        self,
        *,
        indent_level: int,
        uri: str,
        file_name: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        content_type: Optional[str] = None,
        exact_match: bool = True,
    ):
        uri = quote(uri.replace("?", QUERY_REPLACE))
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
        )

    def add_header(self, key: str, value: str):
        self.block_args.append(("add_header", quote(key), quote(value)))

    def add_push(self, uri: str):
        self.block_args.append(("http2_push", quote(uri)))

    def add_preload(self, uri: str, as_type: str):
        type_map = {"CSS": "style", "SCRIPT": "script", "FONT": "font", "IMAGE": "image", "HTML": "document"}
        as_type = type_map.get(as_type, "other")
        self.block_args.append(("add_header", quote("Link"), quote(f"<{uri}>; rel=preload; as={as_type}; nopush")))


class TypesBlock(Block):
    def __init__(self, *, indent_level: int):
        super().__init__(indent_level=indent_level, block_name="types")


class RedirectByLuaBlock(Block):
    def __init__(self, *, indent_level: int, lua_script: str):
        self.lua_script = lua_script
        super().__init__(indent_level=indent_level, block_name="redirect_by_lua_block")

    def _body_lines(self):
        return self.lua_script.strip().split("\n")


class ServerBlock(Block):
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
        # Rewrite all incoming URLs to not contain a `?`
        self.sub_blocks.append(
            RedirectByLuaBlock(
                indent_level=self.indent_level + 1,
                lua_script=f"""
local uri, n, err = ngx.re.gsub(ngx.unescape_uri(ngx.var.request_uri), "\\?", "{QUERY_REPLACE}")
ngx.log(ngx.NOTICE, "rewrote uri: ", ngx.var.request_uri, " --> ", uri)
ngx.req.set_uri(uri, true)""",
            )
        )
        # Create a catch-all block that will try to match URIs based on longest-prefix if no exact match exists
        self.sub_blocks.append(LocationBlock(indent_level=self.indent_level + 1, uri="/", exact_match=False))

    def add_location_block(self, **kwargs):
        block = LocationBlock(indent_level=self.indent_level + 1, **kwargs)
        self.sub_blocks.append(block)
        return block


class HttpBlock(Block):
    def __init__(self, *, indent_level: int):
        super().__init__(indent_level=indent_level, block_name="http", block_args=[("sendfile", "on")])

    def add_server(self, *, server_name: str, server_addr: str, **kwargs) -> ServerBlock:
        block = ServerBlock(
            indent_level=self.indent_level + 1, server_name=server_name, server_addr=server_addr, **kwargs
        )
        self.sub_blocks.append(block)
        return block


class EventsBlock(Block):
    def __init__(self, *, indent_level: int, worker_connections: int = 1024):
        super().__init__(
            indent_level=indent_level, block_name="events", block_args=[("worker_connections", str(worker_connections))]
        )


class Config(Block):
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
