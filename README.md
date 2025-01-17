# Project Document-AI

This project provides an Intelligent Document Processing (IDP) solution to extract key information from invoices, such as invoice number, date, vendor name, total amount, and tax amount. The solution is containerized using Docker for easy deployment.

## Requirements

Linux Environment
Python 3.9 or later
Docke

## Docker Deployment

sudo docker-compose build
sudo docker-compose up

## API Usage

Upload Endpoint

    URL: http://<server-ip>:8000/upload/
    Method: POST
    Description: Upload an invoice image to extract details.

Curl Request

## Use the following curl command to test the API:

curl -X POST "http://127.0.0.1:8000/upload/" -F "file=@/path/to/invoice.jpg"
