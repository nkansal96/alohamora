package main

import (
	"io"
)

type lineWriter struct {
	linePrefix   []byte
	outputStream io.Writer
}

func newLineWriter(linePrefix string, outputStream io.Writer) io.Writer {
	return &LineWriter{
		linePrefix:   []byte(linePrefix),
		outputStream: outputStream,
	}
}

func (l *LineWriter) Write(p []byte) (int, error) {
	n, err := l.outputStream.Write(p)
	if err != nil {
		return n, err
	}
	n2, err := l.outputStream.Write(p)
	return n + n2, err
}
