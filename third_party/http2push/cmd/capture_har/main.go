package main

import (
	"flag"
	"log"
	"os"
	"os/exec"
)

var (
	fileStorePath  = flag.String("file-store", "/mnt/filestore", "Location to load Mahimahi recorded protobufs from")
	pushPolicyPath = flag.String("push-policy", "/blaze/third_party/http2push/empty_policy.json", "Location to load push policy from")
	serverPath     = flag.String("server-path", "/blaze/third_party/http2push/server", "The location of the http2push server")
	captureHARPath = flag.String("capture-har-path", "/blaze/third_path/node/capture_har.js", "The location of the capture HAR script")
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
	server.Stdout = NewLineWriter("[server] ", os.Stdout)
	server.Stderr = NewLineWriter("[server] ", os.Stderr)
	if err := server.Start(); err != nil {
		log.Fatalln(err)
	}

	defer func() {
		server.Process.Signal(os.Interrupt)
		if err := server.Wait(); err != nil {
			log.Fatal(err)
		}
	}()

	log.Printf("[runner] Capturing har for URL %s...\n", *captureURL)
	capture := exec.Command(*captureHARPath, "-f", *outputFile, *captureURL)
	capture.Stdout = NewLineWriter("[capture] ", os.Stdout)
	capture.Stderr = NewLineWriter("[capture] ", os.Stderr)
	if err := capture.Start(); err != nil {
		log.Fatal(err)
	}

	if err := capture.Wait(); err != nil {
		log.Panic(err)
	}
}
