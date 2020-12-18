

# Build

`docker build -t <user_name>/design_cloud .`

eg: `docker build -t aneeshep/design_cloud .`


# RUN

`docker run --name design-cloud -e "REQUESTS_CA_BUNDLE=/app/design_cloud/misc/ca-certificates.crt" -e "DOMAIN_NAME=design-cloud.local" -e "PREFERRED_URL_SCHEME=http" -e "DEX_CLIENT_ID=example-app1" -e "DEX_CLIENT_SECRET=ZXhhbXBsZS1hcHAtc2VjcmV2"  -p 80:5000  <username>/design_cloud`

Note: Access the app in browser, add the below line to /etc/hosts

``` 127.0.0.1 design-cloud.local ```


Now you can access the dashboard via http://design-cloud.local