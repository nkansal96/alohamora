package main

import (
	"flag"
	"log"
	"os"
	"os/exec"
)

const (
	pathPrefix = "/blaze/third_party"
	defaultPolicyPath = pathPrefix + "/http2push/empty_policy.json"
	defaultServerPath = pathPrefix + "/http2push/server"
	defaultCaptureHarPath = pathPrefix + "/node/capture_har.js"
)

func stopProcess(proc *exec.Cmd) {
	proc.Process.Signal(os.Interrupt)
	if err := proc.Wait(); err != nil {
		log.Fatal(err)
	}
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
	server.Stdout = newLineWriter("[server] ", os.Stdout)
	server.Stderr = newLineWriter("[server] ", os.Stderr)
	if err := server.Start(); err != nil {
		log.Fatalln(err)
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
	capture.Stdout = newLineWriter("[capture] ", os.Stdout)
	capture.Stderr = newLineWriter("[capture] ", os.Stderr)
	if err := capture.Start(); err != nil {
		log.Fatal(err)
	}

	if err := capture.Wait(); err != nil {
		log.Panic(err)
	}
}
