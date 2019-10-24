from typing import Dict, List, Optional


class Block:
    def __init__(
        self,
        indent_level: int,
        block_name: str,
        block_name_args: Optional[List[str]] = None,
        block_args: Optional[Dict[str, str]] = None,
        sub_blocks: Optional[List["Block"]] = None,
    ):
        self.indent_level = indent_level
        self.block_name = block_name
        self.block_name_args = block_name_args or []
        self.block_args = block_args or {}
        self.sub_blocks = sub_blocks or []

    def _header(self):
        args_str = " ".join(self.block_name_args) if self.block_name_args else " "
        return f"{self.block_name}{args_str}{{"

    def _body_lines(self):
        if not self.block_args:
            return []
        key_len = max(map(len, self.block_args.keys())) + 1
        return [f"{k:<{key_len}} {v};" for k, v in self.block_args.items()]

    def _trailer(self):
        return "}"

    def __str__(self):
        lines = [
            ("\t" * self.indent_level) + self._header(),
            *[("\t" * (self.indent_level + 1)) + line for line in self._body_lines()],
            *list(map(str, self.sub_blocks)),
            ("\t" * self.indent_level) + self._trailer(),
        ]
        return "\n".join(lines)


class ServerBlock(Block):
    def __init__(self, indent_level: int, server_name: str, server_addr: str, cert_path: str, key_path: str):
        super().__init__(
            indent_level=indent_level,
            block_name="server",
            block_args={
                "listen": f"{server_addr}:443 ssl",
                "server_name": server_name,
                "ssl_certificate": cert_path,
                "ssl_certificate_key": key_path,
            },
        )


class HttpBlock(Block):
    def __init__(self, indent_level: int):
        super().__init__(indent_level=indent_level, block_name="http", block_args={"sendfile": "on"})

    def add_server(self, server_name: str, server_addr: str, cert_path: str, key_path: str) -> ServerBlock:
        block = ServerBlock(
            indent_level=self.indent_level + 1,
            server_name=server_name,
            server_addr=server_addr,
            cert_path=cert_path,
            key_path=key_path,
        )
        self.sub_blocks.append(block)
        return block


class Config(Block):
    def __init__(self):
        super().__init__(indent_level=0, block_name="", block_args={"worker_processes": "auto"})
        self._http_block = None

    @property
    def http_block(self) -> HttpBlock:
        if not self._http_block:
            self._http_block = HttpBlock(indent_level=0)
            self.sub_blocks.append(self._http_block)
        return self._http_block

    def __str__(self):
        return "\n".join(self._body_lines()) + "\n" + "\n\n".join(map(str, self.sub_blocks))


###################################################################################################
# TESTING SECTION
c = Config()
s = c.http_block.add_server("test", "192.168.1.1", "/etc/cert", "/etc/key")
print(str(c))
###################################################################################################
