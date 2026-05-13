/**
 * take_poll.js — Conditional Logic & Progress Tracker for Poll Taking
 * SondagePro
 *
 * Handles:
 *   - Showing/hiding questions based on conditional logic (depends_on)
 *   - Disabling/enabling inputs for hidden questions
 *   - Real-time progress bar update
 */

'use strict';

/* ══ Conditional Logic ════════════════════════════════════ */

/**
 * Evaluates all conditional rules and shows/hides question cards.
 * Called on every radio/checkbox change.
 */
function evaluateLogic() {
    const wrappers = document.querySelectorAll('.question-card');

    // Build a set of currently selected choice IDs
    const selectedChoiceIds = new Set();
    document.querySelectorAll('input[type="radio"]:checked, input[type="checkbox"]:checked')
        .forEach(el => {
            if (el.dataset.choiceId) selectedChoiceIds.add(el.dataset.choiceId);
        });

    wrappers.forEach(wrap => {
        const depQ      = wrap.dataset.dependsOnQ;
        const depChoice = wrap.dataset.dependsOnChoice;

        if (depQ && depChoice) {
            setQuestionVisible(wrap, selectedChoiceIds.has(depChoice));
        } else {
            setQuestionVisible(wrap, true);
        }
    });

    updateProgress();
}

/**
 * Shows or hides a question card and enables/disables its inputs.
 * @param {HTMLElement} wrap  - the .question-card element
 * @param {boolean}     show  - whether to show it
 */
function setQuestionVisible(wrap, show) {
    if (show) {
        wrap.style.opacity        = '1';
        wrap.style.pointerEvents  = 'auto';
        wrap.style.transform      = 'scale(1)';
        wrap.querySelectorAll('input, textarea, select').forEach(el => {
            el.disabled = false;
            if (el.dataset.wasRequired === 'true') el.required = true;
        });
    } else {
        wrap.style.opacity        = '0.3';
        wrap.style.pointerEvents  = 'none';
        wrap.style.transform      = 'scale(0.97)';
        wrap.querySelectorAll('input, textarea, select').forEach(el => {
            el.dataset.wasRequired = String(el.required);
            el.required            = false;
            el.disabled            = true;
        });
    }
}

/* ══ Progress Tracker ═════════════════════════════════════ */

/**
 * Counts visible questions and how many have been answered,
 * then updates the progress bar width.
 */
function updateProgress() {
    const allCards = document.querySelectorAll('.question-card');
    let visible  = 0;
    let answered = 0;

    allCards.forEach(wrap => {
        // Skip hidden cards
        if (parseFloat(wrap.style.opacity || '1') < 0.5) return;
        visible++;

        const qId   = wrap.dataset.qId;
        const radios = wrap.querySelectorAll(`input[name="question_${qId}"]:checked`);
        const textarea = wrap.querySelector(`textarea[name="question_${qId}"]`);

        const hasRadio    = radios.length > 0;
        const hasTextarea = textarea && textarea.value.trim().length > 0;

        if (hasRadio || hasTextarea) answered++;
    });

    const pct = visible > 0 ? Math.round((answered / visible) * 100) : 0;
    const bar = document.getElementById('progressFill');
    if (bar) bar.style.width = pct + '%';
}

/* ══ Init ═════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {
    evaluateLogic();

    // Update progress as user types in text areas
    document.querySelectorAll('textarea').forEach(ta => {
        ta.addEventListener('input', updateProgress);
    });
});
