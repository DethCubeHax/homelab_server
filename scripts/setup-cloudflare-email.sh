#!/usr/bin/env bash
# Configure Postfix to send mail via Cloudflare Email Sending (smtp.mx.cloudflare.net:465).
# Usage: sudo ./setup-cloudflare-email.sh <CLOUDFLARE_API_TOKEN> [alert_recipient]
set -euo pipefail

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo $0 <API_TOKEN> [alert_recipient]" >&2
  exit 1
fi

if [[ $# -lt 1 || -z "${1}" ]]; then
  echo "Usage: sudo $0 <CLOUDFLARE_API_TOKEN> [alert_recipient]" >&2
  echo "  alert_recipient defaults to you@example.com" >&2
  exit 1
fi

CF_TOKEN="$1"
ALERT_TO="${2:-you@example.com}"
FROM_ADDR="alerts@example.com"
RELAY="[smtp.mx.cloudflare.net]:465"

install -m 600 /dev/null /etc/postfix/sasl_passwd
printf '%s    api_token:%s\n' "${RELAY}" "${CF_TOKEN}" > /etc/postfix/sasl_passwd
postmap /etc/postfix/sasl_passwd
chmod 600 /etc/postfix/sasl_passwd /etc/postfix/sasl_passwd.db

cat > /etc/postfix/sender_canonical <<EOF
root              ${FROM_ADDR}
Dreadnought-NAS   ${FROM_ADDR}
EOF
postmap /etc/postfix/sender_canonical

postconf -e "relayhost=${RELAY}"
postconf -e 'smtp_sasl_auth_enable=yes'
postconf -e 'smtp_sasl_password_maps=hash:/etc/postfix/sasl_passwd'
postconf -e 'smtp_sasl_security_options=noanonymous'
postconf -e 'smtp_tls_wrappermode=yes'
postconf -e 'smtp_tls_security_level=encrypt'
postconf -e 'smtp_use_tls=no'
postconf -e 'inet_protocols=ipv4'
postconf -e 'sender_canonical_maps=hash:/etc/postfix/sender_canonical'

# Update smartd alert recipient if lines exist
if grep -q '^/dev/' /etc/smartd.conf; then
  sed -i "s/-m [^ ]*/-m ${ALERT_TO}/g" /etc/smartd.conf
  systemctl restart smartd
fi

systemctl reload postfix
postqueue -f

echo "Sending test message from ${FROM_ADDR} to ${ALERT_TO}..."
echo "Cloudflare Email Sending test from $(hostname) at $(date)" \
  | mail -s "NAS disk alerts: Cloudflare SMTP test" -a "From: ${FROM_ADDR}" "${ALERT_TO}"

sleep 3
echo
echo "=== Mail queue ==="
mailq | tail -5
echo
echo "=== Recent mail log ==="
tail -5 /var/log/mail.log
echo
echo "Done. If queue is empty and log shows 'status=sent', check ${ALERT_TO} inbox."
