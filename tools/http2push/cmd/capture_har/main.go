package main

import (
	"flag"
	"log"
	"os"
	"os/exec"
	"os/signal"
	"strconv"
	"syscall"
)

const (
	pathPrefix            = "/opt"
	defaultPolicyPath     = pathPrefix + "/http2push/empty_policy.json"
	defaultServerPath     = pathPrefix + "/http2push/server"
	defaultCaptureHarPath = pathPrefix + "/capture_har/capture_har.js"
	defaultFileStorePath  = "/mnt/filestore"
	defaultOutputFilePath = "/mnt/har.json"
)

var (
	fileStorePath  = flag.String("file-store", defaultFileStorePath, "Location to load Mahimahi recorded protobufs from")
	pushPolicyPath = flag.String("push-policy", defaultPolicyPath, "Location to load push policy from")
	serverPath     = flag.String("server-path", defaultServerPath, "The location of the http2push server")

	captureHARPath = flag.String("capture-har-path", defaultCaptureHarPath, "The location of the capture HAR script")
	outputFile     = flag.String("output-file", defaultOutputFilePath, "Output file where HAR is stored")
	captureURL     = flag.String("capture-url", "", "URL to capture the HAR for")

	linkTracePath = flag.String("link-trace-path", "", "Path to Mahimahi trace file for mm-link")
	linkLatencyMs = flag.Uint64("link-latency-ms", 0, "Round trip latency to simulate using mm-delay")
)

func startProcess(name string, args []string) *exec.Cmd {
	log.Printf("[runner] Starting %s: %v...", name, args)
	proc := exec.Command(args[0], args[1:]...)
	proc.Stdout = os.Stdout
	proc.Stderr = os.Stderr
	if err := proc.Start(); err != nil {
		log.Fatalf("Error starting %s: %v", name, err)
	}

	stop := make(chan os.Signal)
	signal.Notify(stop, os.Interrupt, syscall.SIGINT, syscall.SIGTERM, syscall.SIGKILL)
	go func() {
		<-stop
		proc.Process.Signal(os.Interrupt)
		proc.Wait()
	}()

	return proc
}

func main() {
	// Parse and validate flags
	flag.Parse()
	if captureURL == nil || len(*captureURL) == 0 {
		log.Fatal("[runner] The capture URL must be specified")
	}
	if linkLatencyMs != nil && *linkLatencyMs > 1000 {
		log.Fatal("[runner] latency-ms must be less than 1000ms")
	}

	// Create the server command and start the server
	serverCmd := []string{"sudo", *serverPath, "-file-store", *fileStorePath, "-push-policy", *pushPolicyPath}
	startProcess("server", serverCmd)

	captureHARCmd := []string{}
	if linkTracePath != nil && len(*linkTracePath) > 0 {
		captureHARCmd = append(captureHARCmd, "mm-link", *linkTracePath, *linkTracePath, "--")
	}
	if linkLatencyMs != nil && *linkLatencyMs > 0 {
		captureHARCmd = append(captureHARCmd, "mm-delay", strconv.FormatUint(*linkLatencyMs, 10))
	}
	captureHARCmd = append(captureHARCmd, *captureHARPath, "-f", *outputFile, *captureURL)
	captureProc := startProcess("capture HAR", captureHARCmd)
	captureProc.Wait()
}
