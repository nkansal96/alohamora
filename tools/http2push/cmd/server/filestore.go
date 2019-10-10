package main

import (
	"http2push"
	pb "http2push/proto"

	"io/ioutil"
	"net/http"
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

// FileStoreResponse wraps a pb.RequestResponse and some metadata for easy access
type FileStoreResponse struct {
	record *pb.RequestResponse

	Host       string
	Method     string
	RequestURI string
}

// FileStore stores a map for a given request to the response that should be sent back
type FileStore interface {
	LookupRequest(request *http.Request) *pb.RequestResponse
	GetHosts() []string
}

type fileStore struct {
	store map[string]map[string]*FileStoreResponse
	hosts []string
}

// NewFileStore reads a given Mahimahi replay directory and returns a FileStore
// that maps responses to HTTP request first lines (omitting the protocol)
func NewFileStore(storeDir string) (FileStore, error) {
	files, err := ioutil.ReadDir(storeDir)
	if err != nil {
		return nil, err
	}

	fs := &fileStore{
		store: make(map[string]map[string]*FileStoreResponse),
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

		fsr := &FileStoreResponse{
			record: new(pb.RequestResponse),
		}
		if err := proto.Unmarshal(data, fsr.record); err != nil {
			return nil, err
		}

		// remove cache related headers
		headers := make([]*pb.HTTPHeader, 0)
		body := fsr.record.Response.Body
		for _, header := range fsr.record.Response.Header {
			key := strings.ToLower(string(header.Key))
			value := strings.ToLower(string(header.Value))

			// unchunk the file if it's chunked since HTTP/2 does not support chunked encoding
			if key == transferEncodingHeader && strings.Contains(value, "chunked") {
				http2push.ServerLogger.Printf("Unchunking file %s...\n", f.Name())
				body = unchunk(body)
			} else if _, shouldRemove := removeHeaders[key]; !shouldRemove {
				headers = append(headers, header)
			}
		}

		for _, header := range fsr.record.Request.Header {
			key := strings.ToLower(string(header.Key))
			value := strings.ToLower(string(header.Value))

			if key == hostHeader {
				fsr.Host = value
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
		if _, ok := fs.store[fsr.Host]; !ok {
			fs.store[fsr.Host] = make(map[string]*FileStoreResponse)
		}

		// remove the proto part of the first line
		uriParts := strings.Split(string(fsr.record.Request.FirstLine), " ")

		fsr.Method = uriParts[0]
		fsr.RequestURI = uriParts[1]
		fsr.record.Response.Header = headers
		fsr.record.Response.Body = body
		fs.store[fsr.Host][uriParts[1]] = fsr
		http2push.ServerLogger.Printf("Read %s: %s", f.Name(), uriParts[1])
	}

	for host := range fs.store {
		fs.hosts = append(fs.hosts, host)
	}

	return fs, nil
}

// LookupRequest checks the file store for a request matching the given method and URI and
// returns the matching response if any exists, or nil otherwise
func (fs *fileStore) LookupRequest(req *http.Request) *pb.RequestResponse {
	// First check if there are any resources for this host
	if _, ok := fs.store[req.Host]; !ok {
		return nil
	}

	// Then check if there is an exact match for the first line
	if res, ok := fs.store[req.Host][req.RequestURI]; ok && res.Method == req.Method {
		return res.record
	}

	// Otherwise iterate through the protos to find the best match
	reqURIParts := strings.SplitN(req.RequestURI, "?", 2)
	var bestMatch *pb.RequestResponse
	var bestScore int

	for _, res := range fs.store[req.Host] {
		if res.Method != req.Method {
			continue
		}

		uriParts := strings.SplitN(res.RequestURI, "?", 2)
		if uriParts[0] != reqURIParts[0] {
			continue
		}

		maxIndex := len(uriParts[1])
		if len(reqURIParts[1]) < maxIndex {
			maxIndex = len(reqURIParts[1])
		}

		i := 0
		for i < maxIndex && uriParts[1][i] == reqURIParts[1][i] {
			i++
		}

		if i > bestScore {
			bestScore = i
			bestMatch = res.record
		}
	}

	return bestMatch
}

func (fs *fileStore) GetHosts() []string {
	return fs.hosts
}
