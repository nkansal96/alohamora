package main

import (
	"flag"
	"log"
	"os"
	"os/exec"
	"os/signal"
	"syscall"
)

const (
	pathPrefix = "/opt"
	defaultPolicyPath = pathPrefix + "/http2push/empty_policy.json"
	defaultServerPath = pathPrefix + "/http2push/server"
	defaultCaptureHarPath = pathPrefix + "/capture_har/capture_har.js"
)

func stopProcess(proc *exec.Cmd) {
	proc.Process.Signal(os.Interrupt)
	proc.Wait()
}

var (
	fileStorePath  = flag.String("file-store", "/mnt/filestore", "Location to load Mahimahi recorded protobufs from")
	pushPolicyPath = flag.String("push-policy", defaultPolicyPath, "Location to load push policy from")
	serverPath     = flag.String("server-path", defaultServerPath, "The location of the http2push server")
	captureHARPath = flag.String("capture-har-path", defaultCaptureHarPath, "The location of the capture HAR script")
	captureURL     = flag.String("capture-url", "", "URL to capture the HAR for")
	outputFile     = flag.String("output-file", "/mnt/har.json", "Output file where HAR is stored")
)

func main() {
	flag.Parse()
	if captureURL == nil || len(*captureURL) == 0 {
		log.Fatal("[runner] The capture URL must be specified")
	}

	log.Printf("[runner] Starting server %s...", *serverPath)
	server := exec.Command(*serverPath, "-file-store", *fileStorePath, "-push-policy", *pushPolicyPath)
	server.Stdout = os.Stdout
	server.Stderr = os.Stderr
	if err := server.Start(); err != nil {
		log.Fatalf("Error starting server: %v", err)
	}

	defer stopProcess(server)

	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt, syscall.SIGINT, syscall.SIGTERM, syscall.SIGKILL)
	go func() {
		<-c
		stopProcess(server)
		os.Exit(1)
	}()

	log.Printf("[runner] Capturing har for URL %s...\n", *captureURL)
	capture := exec.Command(*captureHARPath, "-f", *outputFile, *captureURL)
	capture.Stdout = os.Stdout
	capture.Stderr = os.Stderr
	if err := capture.Start(); err != nil {
		log.Fatalf("Error starting HAR capturer: %v", err)
	}

	if err := capture.Wait(); err != nil {
		log.Panic("Error running HAR capturer: %v", err)
	}
}
