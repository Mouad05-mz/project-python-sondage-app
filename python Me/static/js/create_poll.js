/**
 * create_poll.js — Poll Builder Logic
 * SondagePro
 *
 * Manages the dynamic question builder on the create poll page.
 * All interactions: add/remove questions, manage choices, conditional logic, save.
 */

'use strict';

/* ══ State ════════════════════════════════════════════════ */
let questions = [];

/* ══ Initialise from template (if cloning) ═══════════════ */
function initFromTemplate(templateData) {
    if (!templateData) return;
    document.getElementById('pollTitle').value       = (templateData.title || '') + ' (Copie)';
    document.getElementById('pollDescription').value = templateData.description || '';
    document.getElementById('isAnonymous').checked   = templateData.is_anonymous || false;
    questions = templateData.questions || [];
}

/* ══ Question Management ══════════════════════════════════ */

/**
 * Adds a new empty question of the given type.
 * @param {string} type - 'text' | 'choice_single' | 'choice_multiple' | 'scale'
 */
function addQuestion(type) {
    questions.push({
        text:          '',
        question_type: type,
        is_required:   true,
        order:         questions.length,
        choices:       type.includes('choice') ? ['Option 1', 'Option 2'] : [],
        depends_on:    null,
    });
    renderQuestions();
}

/**
 * Removes a question by index and fixes dependent logic indices.
 * @param {number} index
 */
function removeQuestion(index) {
    questions.splice(index, 1);
    questions.forEach(q => {
        if (q.depends_on && q.depends_on.question_index >= index) {
            if (q.depends_on.question_index === index) {
                q.depends_on = null;
            } else {
                q.depends_on.question_index--;
            }
        }
    });
    renderQuestions();
}

/**
 * Updates a single field on a question object.
 */
function updateQuestionField(index, field, value) {
    questions[index][field] = value;
}

/* ══ Choice Management ════════════════════════════════════ */

function addChoice(qIndex) {
    questions[qIndex].choices.push('Option ' + (questions[qIndex].choices.length + 1));
    renderQuestions();
}

function updateChoiceText(qIndex, cIndex, value) {
    questions[qIndex].choices[cIndex] = value;
}

function removeChoice(qIndex, cIndex) {
    if (questions[qIndex].choices.length > 1) {
        questions[qIndex].choices.splice(cIndex, 1);
        renderQuestions();
    }
}

/* ══ Conditional Logic ════════════════════════════════════ */

function updateConditionalQuestion(qIdx, depQIdx) {
    if (depQIdx === '') {
        questions[qIdx].depends_on = null;
    } else {
        const depQ = questions[parseInt(depQIdx)];
        questions[qIdx].depends_on = {
            question_index: parseInt(depQIdx),
            choice_text:    depQ.choices.length > 0 ? depQ.choices[0] : '',
        };
    }
    renderQuestions();
}

function updateConditionalChoice(qIdx, depQIdx, choiceText) {
    questions[qIdx].depends_on = {
        question_index: parseInt(depQIdx),
        choice_text:    choiceText,
    };
}

/* ══ Render ═══════════════════════════════════════════════ */

const TYPE_META = {
    'text':            { label: 'Texte libre',    icon: 'bi-textarea-t', cls: 'text-type'     },
    'choice_single':   { label: 'Choix unique',   icon: 'bi-ui-radios',  cls: 'single-type'   },
    'choice_multiple': { label: 'Choix multiple', icon: 'bi-ui-checks',  cls: 'multiple-type' },
    'scale':           { label: 'Échelle (1-5)',  icon: 'bi-sliders',    cls: 'scale-type'    },
};

function renderQuestions() {
    const container = document.getElementById('questionsContainer');
    container.innerHTML = '';

    if (questions.length === 0) {
        container.innerHTML = `
            <div class="empty-questions" id="emptyState">
                <i class="bi bi-question-circle display-5 d-block mb-2"></i>
                <p class="mb-0">Cliquez sur un type de question ci-dessous pour commencer.</p>
            </div>`;
        return;
    }

    questions.forEach((q, qIdx) => {
        const t = TYPE_META[q.question_type] || { label: q.question_type, icon: 'bi-question', cls: '' };
        const card = document.createElement('div');
        card.className = 'q-card';
        card.innerHTML = buildQuestionHTML(q, qIdx, t);
        container.appendChild(card);
    });
}

function buildQuestionHTML(q, qIdx, t) {
    let html = `
        <div class="q-card-header">
            <span class="q-type-tag ${t.cls}">
                <i class="bi ${t.icon}"></i>
                Q${qIdx + 1} &mdash; ${t.label}
            </span>
            <button class="remove-q-btn" onclick="removeQuestion(${qIdx})" title="Supprimer">
                <i class="bi bi-x-lg"></i>
            </button>
        </div>

        <div class="mb-2">
            <input type="text"
                   class="form-control"
                   value="${escHtml(q.text)}"
                   oninput="updateQuestionField(${qIdx}, 'text', this.value)"
                   placeholder="Intitulé de la question...">
        </div>

        <div class="form-check form-switch mb-3">
            <input class="form-check-input" type="checkbox" id="req_${qIdx}"
                   ${q.is_required ? 'checked' : ''}
                   onchange="updateQuestionField(${qIdx}, 'is_required', this.checked)">
            <label class="form-check-label" for="req_${qIdx}">Réponse obligatoire</label>
        </div>
    `;

    /* Choices */
    if (q.question_type.includes('choice')) {
        html += `<div class="mb-2"><div class="text-muted small mb-2 fw-600">Options de réponse :</div>`;
        q.choices.forEach((choice, cIdx) => {
            html += `
                <div class="choice-item">
                    <i class="bi bi-${q.question_type === 'choice_single' ? 'circle' : 'square'} text-muted" style="flex-shrink:0;"></i>
                    <input type="text"
                           value="${escHtml(choice)}"
                           oninput="updateChoiceText(${qIdx}, ${cIdx}, this.value)"
                           placeholder="Option...">
                    <button class="remove-choice-btn" onclick="removeChoice(${qIdx}, ${cIdx})">
                        <i class="bi bi-x"></i>
                    </button>
                </div>`;
        });
        html += `
            <button class="add-choice-link" onclick="addChoice(${qIdx})">
                <i class="bi bi-plus-lg me-1"></i>Ajouter une option
            </button>
        </div>`;
    }

    /* Scale preview */
    if (q.question_type === 'scale') {
        html += `
            <div class="d-flex gap-1 mb-2">
                ${[1,2,3,4,5].map(i => `
                    <div style="flex:1;text-align:center;background:rgba(16,185,129,0.08);
                                border:1px solid rgba(16,185,129,0.2);border-radius:8px;
                                padding:0.4rem;color:var(--success);font-weight:700;">${i}</div>
                `).join('')}
            </div>
            <div class="d-flex justify-content-between text-muted" style="font-size:0.72rem;">
                <span>Pas du tout d'accord</span><span>Tout à fait d'accord</span>
            </div>`;
    }

    /* Conditional logic */
    if (qIdx > 0) {
        const prevChoiceQs = questions
            .slice(0, qIdx)
            .map((pq, pi) => ({ idx: pi, q: pq }))
            .filter(x => x.q.question_type.includes('choice'));

        if (prevChoiceQs.length > 0) {
            html += `
                <div style="border-top:1px solid var(--border);margin-top:0.75rem;padding-top:0.75rem;">
                    <div class="text-muted small fw-600 mb-2">
                        <i class="bi bi-arrow-left-right me-1"></i>Logique conditionnelle (optionnel)
                    </div>
                    <div class="d-flex gap-2 align-items-center flex-wrap">
                        <span class="text-muted small">Afficher si</span>
                        <select class="logic-select" onchange="updateConditionalQuestion(${qIdx}, this.value)">
                            <option value="">— Toujours afficher —</option>
                            ${prevChoiceQs.map(x => `
                                <option value="${x.idx}" ${q.depends_on && q.depends_on.question_index === x.idx ? 'selected' : ''}>
                                    Q${x.idx + 1}: ${escHtml(x.q.text || 'Question')}
                                </option>`).join('')}
                        </select>`;

            if (q.depends_on !== null) {
                const depQ = questions[q.depends_on.question_index];
                if (depQ) {
                    html += `
                        <span class="text-muted small">vaut</span>
                        <select class="logic-select" onchange="updateConditionalChoice(${qIdx}, ${q.depends_on.question_index}, this.value)">
                            ${depQ.choices.map(c => `
                                <option value="${escHtml(c)}" ${q.depends_on.choice_text === c ? 'selected' : ''}>${escHtml(c)}</option>
                            `).join('')}
                        </select>`;
                }
            }
            html += `</div></div>`;
        }
    }

    return html;
}

/* ══ Save Poll (POST JSON to Django) ══════════════════════ */

async function savePoll() {
    const title = document.getElementById('pollTitle').value.trim();

    if (!title) {
        alert('Le titre du sondage est obligatoire.');
        document.getElementById('pollTitle').focus();
        return;
    }
    if (questions.length === 0) {
        alert('Veuillez ajouter au moins une question.');
        return;
    }
    for (let i = 0; i < questions.length; i++) {
        if (!questions[i].text.trim()) {
            alert(`La question ${i + 1} n'a pas de texte.`);
            return;
        }
    }

    const payload = {
        title:          title,
        description:    document.getElementById('pollDescription').value,
        is_anonymous:   document.getElementById('isAnonymous').checked,
        is_template:    document.getElementById('isTemplate').checked,
        password:       document.getElementById('pollPassword').value,
        expires_at:     document.getElementById('expiresAt').value || null,
        limit_per_ip:   parseInt(document.getElementById('limitPerIp').value)   || 0,
        limit_per_user: parseInt(document.getElementById('limitPerUser').value) || 1,
        questions:      questions.map((q, i) => ({ ...q, order: i })),
    };

    const btn = document.getElementById('btnSave');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Publication...';

    try {
        const resp = await fetch(window.CREATE_POLL_URL, {
            method:  'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken':  window.CSRF_TOKEN,
            },
            body: JSON.stringify(payload),
        });

        const result = await resp.json();

        if (result.status === 'success') {
            window.location.href = window.DASHBOARD_URL;
        } else {
            alert('Erreur : ' + result.message);
            btn.disabled = false;
            btn.innerHTML = '<i class="bi bi-send-fill me-2"></i>Publier le sondage';
        }
    } catch (err) {
        console.error(err);
        alert('Erreur de connexion. Veuillez réessayer.');
        btn.disabled = false;
        btn.innerHTML = '<i class="bi bi-send-fill me-2"></i>Publier le sondage';
    }
}

/* ══ Utility ══════════════════════════════════════════════ */

function escHtml(str) {
    return String(str)
        .replace(/&/g,  '&amp;')
        .replace(/</g,  '&lt;')
        .replace(/>/g,  '&gt;')
        .replace(/"/g,  '&quot;');
}

/* ══ Bootstrap: init on DOMContentLoaded ══════════════════ */
document.addEventListener('DOMContentLoaded', () => {
    if (questions.length === 0) {
        addQuestion('text');
    } else {
        renderQuestions();
    }
});
