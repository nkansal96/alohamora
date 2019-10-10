package http2push

import (
	"log"
	"os"
)

var (
	// ServerLogger is the logger for the server
	ServerLogger = log.New(os.Stdout, "[server] ", log.LstdFlags)
	// RunnerLogger is the logger for the runner
	RunnerLogger = log.New(os.Stdout, "[runner] ", log.LstdFlags)
)
