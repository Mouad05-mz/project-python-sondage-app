/**
 * poll_results.js — Chart.js Visualisations for the Results page
 * SondagePro
 *
 * Reads the `window.CHARTS_DATA` array (injected by Django template)
 * and renders a Chart.js doughnut or bar chart for each question.
 */

'use strict';

/* ══ Chart.js Global Defaults ═════════════════════════════ */
Chart.defaults.color       = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';

/* ══ Colour Palette ═══════════════════════════════════════ */
const PALETTE = [
    'rgba(99,102,241,0.85)',   // indigo
    'rgba(6,182,212,0.85)',    // cyan
    'rgba(16,185,129,0.85)',   // green
    'rgba(245,158,11,0.85)',   // amber
    'rgba(239,68,68,0.8)',     // red
    'rgba(168,85,247,0.8)',    // purple
    'rgba(251,191,36,0.8)',    // yellow
];

/* ══ Chart Builders ═══════════════════════════════════════ */

/**
 * Renders a doughnut chart for choice-based questions.
 * @param {HTMLCanvasElement} canvas
 * @param {string[]} labels
 * @param {number[]} data
 */
function buildDoughnutChart(canvas, labels, data) {
    const colors = labels.map((_, i) => PALETTE[i % PALETTE.length]);

    new Chart(canvas, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors,
                borderColor:     '#1e293b',
                borderWidth:     3,
                hoverOffset:     8,
            }],
        },
        options: {
            responsive: true,
            cutout:     '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 16, boxWidth: 12 },
                },
            },
        },
    });
}

/**
 * Renders a bar chart for scale (1–5) questions.
 * @param {HTMLCanvasElement} canvas
 * @param {string[]} labels
 * @param {number[]} data
 */
function buildBarChart(canvas, labels, data) {
    const colors = [
        'rgba(239,68,68,0.8)',
        'rgba(245,158,11,0.8)',
        'rgba(6,182,212,0.8)',
        'rgba(99,102,241,0.8)',
        'rgba(16,185,129,0.8)',
    ];

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label:           'Réponses',
                data,
                backgroundColor: colors,
                borderRadius:    8,
                borderSkipped:   false,
            }],
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    grid:  { color: 'rgba(255,255,255,0.06)' },
                    ticks: { stepSize: 1 },
                },
                x: { grid: { display: false } },
            },
            plugins: { legend: { display: false } },
        },
    });
}

/* ══ Init: render all charts from window.CHARTS_DATA ══════ */

document.addEventListener('DOMContentLoaded', () => {
    if (!window.CHARTS_DATA || !Array.isArray(window.CHARTS_DATA)) return;

    window.CHARTS_DATA.forEach(cfg => {
        const canvas = document.getElementById(cfg.id);
        if (!canvas) return;

        if (cfg.type === 'doughnut') {
            buildDoughnutChart(canvas, cfg.labels, cfg.data);
        } else if (cfg.type === 'bar') {
            buildBarChart(canvas, cfg.labels, cfg.data);
        }
    });
});
