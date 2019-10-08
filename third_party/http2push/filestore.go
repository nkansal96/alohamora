package http2push

import (
	pb "http2push/proto"

	"fmt"
	"io/ioutil"
	"log"
	"path"
	"strings"

	"github.com/golang/protobuf/proto"
)

var (
	hostHeader             = "host"
	transferEncodingHeader = "transfer-encoding"
	removeHeaders          = map[string]bool{
		"access-control-allow-origin": true,
		"strict-transport-security":   true,
		"cache-control":               true,
		"expires":                     true,
		"last-modified":               true,
		"date":                        true,
		"age":                         true,
		"etag":                        true,
	}
)

// FileStore stores a map for a given request to the response that should be sent back
type FileStore interface {
	LookupRequest(method string, requestURI string) *pb.RequestResponse
	GetHosts() []string
}

type fileStore struct {
	store map[string]*pb.RequestResponse
	hosts []string
}

// NewFileStore reads a given Mahimahi replay directory and returns a FileStore
// that maps responses to HTTP request first lines (omitting the protocol)
func NewFileStore(storeDir string) (FileStore, error) {
	files, err := ioutil.ReadDir(storeDir)
	if err != nil {
		return nil, err
	}

	hostMap := map[string]bool{}
	fs := &fileStore{
		store: make(map[string]*pb.RequestResponse),
		hosts: make([]string, 0),
	}

	for _, f := range files {
		if f.IsDir() {
			continue
		}

		data, err := ioutil.ReadFile(path.Join(storeDir, f.Name()))
		if err != nil {
			return nil, err
		}

		rr := pb.RequestResponse{}
		if err := proto.Unmarshal(data, &rr); err != nil {
			return nil, err
		}

		// remove the proto part of the first line
		uriParts := strings.Split(string(rr.Request.FirstLine), " ")
		uri := strings.Join(uriParts[0:len(uriParts)-1], " ")

		// remove cache related headers
		headers := make([]*pb.HTTPHeader, 0)
		body := rr.Response.Body
		host := ""
		for _, header := range rr.Response.Header {
			key := strings.ToLower(string(header.Key))
			value := strings.ToLower(string(header.Value))

			// unchunk the file if it's chunked since HTTP/2 does not support chunked encoding
			if key == transferEncodingHeader && strings.Contains(value, "chunked") {
				log.Printf("Unchunking file %s...\n", f.Name())
				body = unchunk(body)
			} else if _, shouldRemove := removeHeaders[key]; !shouldRemove {
				headers = append(headers, header)
			}
		}

		for _, header := range rr.Request.Header {
			key := strings.ToLower(string(header.Key))
			value := strings.ToLower(string(header.Value))

			if key == hostHeader {
				host = value
			}
		}

		// Add cache-control header and access-control-allow-origin headers
		headers = append(headers, &pb.HTTPHeader{
			Key:   []byte("Cache-Control"),
			Value: []byte("3600"),
		}, &pb.HTTPHeader{
			Key:   []byte("Access-Control-Allow-Origin"),
			Value: []byte("*"),
		})

		// add host if does not exist already
		if len(host) > 0 {
			hostMap[host] = true
		}

		rr.Response.Header = headers
		rr.Response.Body = body
		fs.store[uri] = &rr
		log.Printf("Read %s: %s\n", f.Name(), uri)
	}

	for host := range hostMap {
		fs.hosts = append(fs.hosts, host)
	}

	return fs, nil
}

// LookupRequest checks the file store for a request matching the given method and URI and
// returns the matching response if any exists, or nil otherwise
func (fs *fileStore) LookupRequest(method string, requestURI string) *pb.RequestResponse {
	firstLinePrefix := fmt.Sprintf("%s %s", method, requestURI)
	if proto, ok := fs.store[firstLinePrefix]; ok {
		return proto
	}
	return nil
}

func (fs *fileStore) GetHosts() []string {
	return fs.hosts
}
