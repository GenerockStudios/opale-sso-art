await fetch(
  "https://api.kombicar.app/api/v1/vtc-test/heatmap-simulation?targetPassengerId=A0010000-0000-0000-0000-000000000001&lat=3.8661&lng=11.5154",
  {
    headers: {
      accept: "*/*",
      "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
      "cache-control": "no-cache",
      pragma: "no-cache",
      priority: "u=1, i",
      "sec-ch-ua":
        '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": '"Windows"',
      "sec-fetch-dest": "empty",
      "sec-fetch-mode": "cors",
      "sec-fetch-site": "same-origin",
    },
    referrer: "https://api.kombicar.app/swagger/index.html",
    body: null,
    method: "POST",
    mode: "cors",
    credentials: "omit",
  },
).then((v) => {
  console.log(v);
});

fetch(
  "https://api.kombicar.app/api/v1/vtc-test/macros/heatmap-simulation?targetPassengerId=A0010000-0000-0000-0000-000000000001&lat=3.8661&lng=11.5154",
  {
    headers: {
      accept: "*/*",
      "accept-language": "en-US,en;q=0.9,fr-FR;q=0.8,fr;q=0.7",
      "cache-control": "no-cache",
      pragma: "no-cache",
      priority: "u=1, i",
      "sec-ch-ua":
        '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": '"Windows"',
      "sec-fetch-dest": "empty",
      "sec-fetch-mode": "cors",
      "sec-fetch-site": "same-origin",
    },
    referrer: "https://api.kombicar.app/swagger/index.html",
    body: null,
    method: "POST",
    mode: "cors",
    credentials: "omit",
  },
).then((v) => {
  console.log(v);
});
