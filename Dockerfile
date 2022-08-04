# syntax=docker/dockerfile:1

FROM golang:1.18-alpine

WORKDIR /app

COPY go.mod ./

#Currently no external libraries are used, hence this is not needed
#COPY go.sum ./
#RUN go mod download

COPY *.go ./

RUN go build -o /charmed-norris

EXPOSE 3333

CMD [ "/charmed-norris" ]
