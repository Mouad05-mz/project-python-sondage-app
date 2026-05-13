/**
 * dashboard.js — Dashboard interactivity
 * SondagePro
 *
 * Handles the "copy share link" toast notification on the dashboard.
 */

'use strict';

/**
 * Copies the given URL to the clipboard and shows a success toast.
 * @param {string} url - the full share URL to copy
 */
function copyShareLink(url) {
    const fullUrl = window.location.protocol + '//' + url;

    navigator.clipboard.writeText(fullUrl)
        .then(() => {
            const toastEl = document.getElementById('shareToast');
            if (!toastEl) return;
            const toast = new bootstrap.Toast(toastEl, { delay: 2500 });
            toast.show();
        })
        .catch(() => {
            // Fallback for browsers that block clipboard API
            prompt('Copiez ce lien :', fullUrl);
        });
}
