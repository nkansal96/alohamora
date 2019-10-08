package main

import (
	"flag"
	"log"
	"math/rand"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"http2push"
)

var (
	fileStorePath  = flag.String("file-store", "/mnt/filestore", "Location to load Mahimahi recorded protobufs from")
	pushPolicyPath = flag.String("push-policy", "/blaze/third_party/http2push/empty_policy.json", "Location to load push policy from")
	certFile       = flag.String("cert", "/blaze/third_party/http2push/certs/server.cert", "Location of server certificate")
	keyFile        = flag.String("key", "/blaze/third_party/http2push/certs/server.key", "Location of server private key")
)

func handleRequest(fs http2push.FileStore, push http2push.PushPolicy) func(w http.ResponseWriter, r *http.Request) {
	return func(w http.ResponseWriter, r *http.Request) {
		// Lookup file for given request
		f := fs.LookupRequest(r.Method, r.RequestURI)
		if f == nil {
			w.WriteHeader(404)
			log.Printf("[%s] %s   404 0", r.Method, r.RequestURI)
			return
		}

		// Lookup push resources for given file
		if pusher, ok := w.(http.Pusher); ok {
			pushResList := push.GetPushResources(r.RequestURI)
			for _, pushRes := range pushResList {
				if err := pusher.Push(pushRes, nil); err != nil {
					log.Printf("Failed to push: %v", err)
				} else {
					log.Printf("[PUSH] %s -> %s", r.RequestURI, pushRes)
				}
			}
		}

		// Set headers for the requested file
		for _, header := range f.Response.Header {
			w.Header().Set(string(header.Key), string(header.Value))
		}
		w.Write(f.Response.Body)
		log.Printf("[%s] %s   200 %d", r.Method, r.RequestURI, len(f.Response.Body))
	}
}

func main() {
	flag.Parse()

	fs, err := http2push.NewFileStore(*fileStorePath)
	if err != nil {
		log.Fatal(err)
	}

	push, err := http2push.NewPushPolicy(*pushPolicyPath)
	if err != nil {
		log.Fatal(err)
	}

	now := time.Now().UnixNano()
	source := rand.NewSource(now)
	random := rand.New(source)

	interfaceManager, err := http2push.NewInterfaceManagerWithHosts(fs.GetHosts(), random)
	defer interfaceManager.DeleteInterfaces()
	if err != nil {
		log.Fatal(err)
	}

	dnsmasq := http2push.NewDNSMasq(interfaceManager.GetInterfaces())
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

	log.Printf("Serving on https://0.0.0.0:443")
	log.Fatal(srv.ListenAndServeTLS(*certFile, *keyFile))
}
