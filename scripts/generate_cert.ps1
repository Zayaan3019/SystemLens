param(
  [string]$CertFile = "cert.pem",
  [string]$KeyFile = "key.pem"
)

if (-not (Get-Command openssl -ErrorAction SilentlyContinue)) {
  Write-Host "OpenSSL is required to generate a self-signed cert." -ForegroundColor Yellow
  exit 1
}

openssl req -x509 -newkey rsa:4096 -keyout $KeyFile -out $CertFile -days 365 -nodes -subj "/CN=systemlens.local"
Write-Host "Generated $CertFile and $KeyFile"
