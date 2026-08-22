// Cloudflare Worker: serve Matrix .well-known on example.com / www.example.com
// Dashboard → Workers → Create → paste this → add route:
//   example.com/.well-known/matrix/*
//   www.example.com/.well-known/matrix/*

const MATRIX_CLIENT = {
  "m.homeserver": {
    "base_url": "https://matrix.example.com"
  },
  "org.matrix.msc4143.rtc_foci": [
    {
      "type": "livekit",
      "livekit_service_url": "https://livekit-jwt.call.matrix.org"
    }
  ]
};

export default {
  async fetch(request) {
    const url = new URL(request.url);

    if (url.pathname === "/.well-known/matrix/client") {
      return new Response(JSON.stringify(MATRIX_CLIENT), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
      });
    }

    if (url.pathname === "/.well-known/matrix/server") {
      return new Response(JSON.stringify({ "m.server": "matrix.example.com:443" }), {
        headers: {
          "Content-Type": "application/json",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }

    return fetch(request);
  },
};
