package main

import (
	"bytes"
	"net/url"
	"os/exec"
	"strconv"
)

var (
	crlf = []byte("\r\n")
)

func stripHost(in string) string {
	u, err := url.Parse(in)
	if err != nil {
		return in
	}
	u.Scheme = ""
	u.User = nil
	u.Host = ""
	return u.String()
}

func unchunk(body []byte) []byte {
	newBody := []byte{}
	crlfLoc := bytes.Index(body, crlf)
	chunkSize, _ := strconv.ParseInt(string(body[:crlfLoc]), 16, 0)
	body = body[crlfLoc+2:]

	for chunkSize != 0 {
		newBody = append(newBody, body[:chunkSize]...)
		body = body[chunkSize+2:]

		crlfLoc = bytes.Index(body, crlf)
		chunkSize, _ = strconv.ParseInt(string(body[:crlfLoc]), 16, 0)
		body = body[crlfLoc+2:]
	}

	return newBody
}

func run(name string, args ...string) error {
	return exec.Command(name, args...).Run()
}
