def unchunk(body: bytes):
    """
    Unchunks a Transfer-encoding: chunked HTTP response

    :param body: The bytes of the chunked response
    :return: The unchunked response
    """
    # new_body will have unchunked response
    new_body = b""

    # iterate through chunks until we hit the last chunk
    crlf_loc = body.find(b"\r\n")
    chunk_size = int(body[:crlf_loc], 16)
    body = body[crlf_loc + 2 :]
    while chunk_size != 0:
        # add chunk content to new body and remove from old body
        new_body += body[0:chunk_size]
        body = body[chunk_size:]

        # remove CRLF trailing chunk
        body = body[2:]

        # get chunk size
        crlf_loc = body.find(b"\r\n")
        chunk_size = int(body[:crlf_loc], 16)
        body = body[crlf_loc + 2 :]

    return new_body


def quote(s: str) -> str:
    return "'" + s.replace("'", "\\'") + "'"
