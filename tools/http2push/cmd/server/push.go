package main

import (
	"http2push"

	"encoding/json"
	"os"
)

var (
	emptyList = []string{}
)

// PushPolicy defines a type that returns the resources to push for a given resource
type PushPolicy interface {
	GetPushResources(requestURI string) []string
}

type policyEntry struct {
	URL string `json:"url"`
}

type pushPolicy struct {
	policy map[string][]string
}

// NewPushPolicy reads the given JSON push policy file and returns a PushPolicy
// object, stripping out the hostname and schemes from each URL
func NewPushPolicy(file string) (PushPolicy, error) {
	f, err := os.Open(file)
	if err != nil {
		return nil, err
	}

	var policy map[string][]policyEntry
	if err := json.NewDecoder(f).Decode(&policy); err != nil {
		return nil, err
	}

	policyMap := make(map[string][]string)
	for source, entries := range policy {
		pushURLs := []string{}
		sourceURL := stripHost(source)
		for _, push := range entries {
			pushURL := stripHost(push.URL)
			pushURLs = append(pushURLs, pushURL)
			http2push.ServerLogger.Printf("Loaded push: %s --> %s", sourceURL, pushURL)
		}
		policyMap[sourceURL] = pushURLs
	}

	return &pushPolicy{policyMap}, nil
}

// GetPushResources returns the list of resources to push for a given URI. The
// returned list is empty if there are no resources to push
func (p *pushPolicy) GetPushResources(requestURI string) []string {
	if push, ok := p.policy[requestURI]; ok {
		return push
	}
	return emptyList
}
