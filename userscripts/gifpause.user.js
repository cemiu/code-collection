// ==UserScript==
// @name         GifPause: Pause and Resume annoying GIF Animations on Right Click
// @author       cemiu
// @namespace    https://cemiu.net/
// @license      MIT
// @version      1.4
// @description  Pause and resume GIF and WebP animations on right-click
// @match        *://*/*
// @grant        none
// ==/UserScript==

(function() {
    'use strict';

    const ORIGINAL_SRC_ATTR = 'data-original-src';

    function isAnimatedImage(target) {
        return target.hasAttribute(ORIGINAL_SRC_ATTR) || target.src.endsWith('.gif') || target.src.endsWith('.webp');
    }

    async function toggleAnimation(target) {
        if (target.hasAttribute(ORIGINAL_SRC_ATTR)) {
            target.src = target.getAttribute(ORIGINAL_SRC_ATTR);
            target.removeAttribute(ORIGINAL_SRC_ATTR);
        } else {
            let response = await fetch(target.src, { mode: 'cors' });
            let blob = await response.blob();
            let img = new Image();
            img.src = URL.createObjectURL(blob);

            img.onload = () => {
                let canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;
                canvas.getContext('2d').drawImage(img, 0, 0);
                target.setAttribute(ORIGINAL_SRC_ATTR, target.src);
                target.src = canvas.toDataURL('image/png');
                URL.revokeObjectURL(img.src);
            };
        }
    }

    document.addEventListener('contextmenu', event => {
        let target = event.target;
        if (target.tagName === 'IMG' && isAnimatedImage(target)) {
            event.preventDefault();
            toggleAnimation(target);
        }
    }, false);
})();
