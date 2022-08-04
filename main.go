package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strconv"
	"time"
)

// ChuckResponse takes a JSON response from chucknorris.io
// and populates the fields.
type ChuckResponse struct {
	IconURL string `json:"icon_url"`
	ID      string `json:"id"`
	URL     string `json:"url"`
	Value   string `json:"value"`
}

func getJoke(w http.ResponseWriter, r *http.Request) {
	var url string
	category := os.Getenv("CHUCK_CATEGORY")
	if category == "" {
		url = "https://api.chucknorris.io/jokes/random"
	} else {
		url = "https://api.chucknorris.io/jokes/random?category=" + category
	}
	chuckresp := ChuckResponse{}
	err := getJson(url, &chuckresp)
	if err != nil {
		log.Fatalf("could not parse JSON: %s", err)
	}

	io.WriteString(w, chuckresp.Value)
}

func getJson(url string, target interface{}) error {
	var myClient = &http.Client{Timeout: 10 * time.Second}
	r, err := myClient.Get(url)
	if err != nil {
		return err
	}
	defer r.Body.Close()

	return json.NewDecoder(r.Body).Decode(target)
}

func main() {
	http.HandleFunc("/", getJoke)
	listenPort := "3333"
	port := os.Getenv("CHUCK_PORT")
	if port != "" {
		if _, err := strconv.Atoi(port); err == nil {
			listenPort = port
		}
	}
	fmt.Println("Starting the charming Chuck...")
	http.ListenAndServe(":"+listenPort, nil)
}
