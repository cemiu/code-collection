// helper for searching VFS appointment slots, and sending telegram message when available

async function sendTelegramMessage(message) {
  const chat_id = <telegram user chat id; get by messaging @RawDataBot, should be an integer>;
  const token = "<telegram bot API token>";
  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  const data = { chat_id, text: message };
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  alert(message);
  return response.json();
}

function handleVfsResponse(response) {
    if (!response.ok) {
      sendTelegramMessage("VFS request failed");
      return;
    }
    response.json().then(data => {
      if (data.earliestDate !== null) {
        sendTelegramMessage(JSON.stringify(data));
      } else if (data.error && data.error.description) {
        // sendTelegramMessage(data.error.description);
      } else {
        sendTelegramMessage("VFS request failed: " + JSON.stringify(data));
      }
    });
  }

const VFS_INTERVAL_MIN = 60;
const VFS_INTERVAL_MAX = 180;

function fetchVfsData() {
  /////////// START ///////////
  fetch("https://lift-api.vfsglobal.com/appointment/CheckIsSlotAvailable", {
  "headers": {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-GB,en;q=0.9,de;q=0.8",
    "authorize": "randomkey",
    "content-type": "application/json;charset=UTF-8",
    "route": "gbr/en/nld",
    "sec-ch-ua": "\"Google Chrome\";v=\"113\", \"Chromium\";v=\"113\", \"Not-A.Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"macOS\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site"
  },
  "referrer": "https://visa.vfsglobal.com/",
  "referrerPolicy": "strict-origin-when-cross-origin",
  "body": "{\"countryCode\":\"gbr\",\"missionCode\":\"nld\",\"vacCode\":\"NAKN\",\"visaCategoryCode\":\"TA\",\"roleName\":\"Individual\",\"loginUser\":\"email\"}",
  "method": "POST",
  "mode": "cors",
  "credentials": "omit"
})
  //////////// END ////////////
    .then(response => handleVfsResponse(response))
    .catch(error => sendTelegramMessage(error));
}

function startVfsInterval() {
  const interval = Math.floor(Math.random() * (VFS_INTERVAL_MAX - VFS_INTERVAL_MIN + 1)) + VFS_INTERVAL_MIN;
  setInterval(fetchVfsData, interval * 1000);
}

startVfsInterval();

