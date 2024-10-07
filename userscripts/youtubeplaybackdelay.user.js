// ==UserScript==
// @name        Delay YouTube Playback
// @namespace   DelayYoutubeNonSubPlayback
// @match       https://www.youtube.com/*
// @grant       none
// @version     1.0
// @author      cemiu
// @description Makes it impossible to playback a video for a full minute after clicking on it.
// ==/UserScript==

(function() {
  'use strict';

  // settings
  let allowSubbedContent = false;
  let seconds = 60;

  // housekeeping
  let freq = 10; // times a second to update
  let countdown = seconds * freq;
  let displayVisible = false;
  let looper;

  // Create a display element for current speed
  const displayElement = document.createElement('div');
  displayElement.style.position = 'fixed';
  displayElement.style.background = 'white';
  displayElement.style.zIndex = '5100';
  displayElement.style.opacity = '0';
  displayElement.style.fontSize = '14px';
  document.body.appendChild(displayElement);

  const delay = (delayInms) => {
    return new Promise(resolve => setTimeout(resolve, delayInms));
  };

  async function isSubscribed() {
    let delayres = await delay(500);
    const subStr = document.getElementById("subscribe-button").querySelector('.yt-core-attributed-string').textContent;
    console.log(subStr);
    return subStr === "Subscribed" || subStr === "Manage";
  }

  async function runScript() {
    let isSub = await isSubscribed();
    if (allowSubbedContent && isSub) return;  // subscribed to channel, abort

    displayElement.style.opacity = '1';
    looper = setInterval(function(){
      countdown--;

      let video = document.querySelector('.html5-video-player');

      video.pauseVideo();
      if (video.getCurrentTime() > 0)
        video.seekToStreamTime(0);

      displayElement.textContent = `Countdown: ${(countdown / freq).toFixed(0)}s`;

      if (countdown < 0) {
          clearInterval(looper);
          displayElement.style.opacity = '0';
      }

    }, 1000 / freq);
  }

  runScript();
  let lastpath = location.pathname + location.search;

  setInterval(function(){
    if (location.pathname !== '/watch') return;
    let newpath = location.pathname + location.search;
    if (lastpath === newpath) return;
    lastpath = newpath;

    try {clearInterval(looper);} catch(error) {}
    countdown = seconds * freq;
    displayElement.style.opacity = '0';

    runScript();
  }, 500);

})();

