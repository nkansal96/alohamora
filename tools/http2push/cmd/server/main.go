package main

import (
	"http2push"

	"flag"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"
)

const (
	pathPrefix        = "/opt/http2push"
	defaultPolicyPath = pathPrefix + "/empty_policy.json"
	defaultServerPath = pathPrefix + "/server"
	defaultCertsPath  = pathPrefix + "/certs"
)

var (
	fileStorePath  = flag.String("file-store", "/mnt/filestore", "Location to load Mahimahi recorded protobufs from")
	pushPolicyPath = flag.String("push-policy", defaultPolicyPath, "Location to load push policy from")
	certFile       = flag.String("cert", defaultCertsPath+"/server.cert", "Location of server certificate")
	keyFile        = flag.String("key", defaultCertsPath+"/server.key", "Location of server private key")
)

func handleRequest(fs FileStore, push PushPolicy) func(w http.ResponseWriter, r *http.Request) {
	return func(w http.ResponseWriter, r *http.Request) {
		// Lookup file for given request
		f := fs.LookupRequest(r)
		if f == nil {
			w.WriteHeader(404)
			http2push.ServerLogger.Printf("[%s] %s   404 0", r.Method, r.RequestURI)
			return
		}

		// Prevent recursive pushing
		if r.Header.Get("X-Pushed") != "1" {
			// Check if push is supported
			if pusher, ok := w.(http.Pusher); ok {
				// Lookup push resources for given file
				pushResList := push.GetPushResources(r.RequestURI)
				for _, pushRes := range pushResList {
					err := pusher.Push(pushRes, &http.PushOptions{
						// Add a header indicating this object is being pushed and the server
						// should not attempt to push more objects for this object
						Header: http.Header{
							"X-Pushed": []string{"1"},
						},
					})
					if err != nil {
						http2push.ServerLogger.Printf("Failed to push: %v", err)
					} else {
						http2push.ServerLogger.Printf("[PUSH] %s -> %s", r.RequestURI, pushRes)
					}
				}
			}
		}

		// Set headers for the requested file
		for _, header := range f.Response.Header {
			w.Header().Set(string(header.Key), string(header.Value))
		}
		w.Write(f.Response.Body)
		http2push.ServerLogger.Printf("[%s] %s   200 %d", r.Method, r.RequestURI, len(f.Response.Body))
	}
}

func main() {
	flag.Parse()

	fs, err := NewFileStore(*fileStorePath)
	if err != nil {
		http2push.ServerLogger.Fatal(err)
	}

	push, err := NewPushPolicy(*pushPolicyPath)
	if err != nil {
		http2push.ServerLogger.Fatal(err)
	}

	now := time.Now().UnixNano()
	source := rand.NewSource(now)
	random := rand.New(source)

	interfaceManager, err := NewInterfaceManagerWithHosts(fs.GetHosts(), random)
	defer interfaceManager.DeleteInterfaces()
	if err != nil {
		http2push.ServerLogger.Fatal(err)
	}

	dnsmasq := NewDNSMasq(interfaceManager.GetInterfaces())
	dnsmasq.Start()
	defer dnsmasq.Stop()

	c := make(chan os.Signal)
	signal.Notify(c, os.Interrupt, syscall.SIGINT, syscall.SIGTERM, syscall.SIGKILL)
	go func() {
		<-c
		dnsmasq.Stop()
		interfaceManager.DeleteInterfaces()
		os.Exit(1)
	}()

	srv := &http.Server{
		Addr:    ":443",
		Handler: http.HandlerFunc(handleRequest(fs, push)),
	}

	http2push.ServerLogger.Printf("Serving on https://0.0.0.0:443")
	http2push.ServerLogger.Fatal(srv.ListenAndServeTLS(*certFile, *keyFile))
}
