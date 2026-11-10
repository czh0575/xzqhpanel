// static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    initYearSelect();
    initLevelSelection();
    bindFormSubmitEvent();
});

/* 年份选择逻辑 */
function initYearSelect() {
    const startYearSelect = document.getElementById('startYear');
    const endYearSelect = document.getElementById('endYear');
    
    updateEndYearOptions(startYearSelect.value);
    startYearSelect.addEventListener('change', (e) => {
        updateEndYearOptions(e.target.value);
    });
}

function updateEndYearOptions(startYear) {
    const endYearSelect = document.getElementById('endYear');
    const currentEndYear = endYearSelect.value;
    
    endYearSelect.innerHTML = '';
    for (let year = startYear; year <= 2026; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        option.selected = (year === Math.min(currentEndYear, 2026)) || (year === 2026);
        endYearSelect.appendChild(option);
    }
}

/* 层级选择逻辑 */
function initLevelSelection() {
    document.querySelector('input[value="city"]').checked = true;
    setParentMatchDefault();
    document.querySelectorAll('.level-option input').forEach(checkbox => {
        checkbox.addEventListener('change', updateParentMatchState);
    });
}

function setParentMatchDefault() {
    const matchYes = document.querySelector('input[value="yes"]');
    matchYes.checked = true;
}

function updateParentMatchState() {
    const selectedLevels = Array.from(document.querySelectorAll('input[name="level[]"]:checked'))
                              .map(checkbox => checkbox.value);
    const matchYes = document.querySelector('input[value="yes"]');
    const matchNo = document.querySelector('input[value="no"]');

    if (selectedLevels.length === 1 && selectedLevels.includes('province')) {
        matchYes.disabled = true;
        matchNo.checked = true;
    } else {
        matchYes.disabled = false;
        if (!document.querySelector('input[name="parentMatch"]:checked')) {
            matchYes.checked = true;
        }
    }
}

/* 表单提交逻辑 */
function bindFormSubmitEvent() {
    document.getElementById('adminCodeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        try {
            const formData = {
                startYear: Number(document.getElementById('startYear').value),
                endYear: Number(document.getElementById('endYear').value),
                levels: Array.from(document.querySelectorAll('input[name="level[]"]:checked'))
                            .map(c => c.value),
                includeParent: document.querySelector('input[name="parentMatch"]:checked').value === 'yes'
            };

            if (!validateForm(formData)) return;

            setLoadingState(true);
            const response = await fetch('/xzqh/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            const result = await handleResponse(response);
            showResult(result);

        } catch (error) {
            showModal(error.message || '生成失败，请联系管理员');
        } finally {
            setLoadingState(false);
        }
    });
}

function validateForm(data) {
    if (data.startYear > data.endYear) {
        showModal('起始年份不能大于终止年份');
        return false;
    }
    if (data.levels.length === 0) {
        showModal('请至少选择一个层级');
        return false;
    }
    if (data.includeParent && data.levels.length === 1 && data.levels[0] === 'province') {
        showModal('省级行政区划不需要匹配上级');
        return false;
    }
    return true;
}

async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || '请求失败');
    }
    return response.json();
}

/* 结果展示逻辑 */
function showResult(result) {
    const resultArea = document.getElementById('result-area');

    if (result.status === 'success') {
        const downloads = result.meta.downloads;
        resultArea.innerHTML = `
            <section class="download-results">
                <div class="download-heading"><div class="download-title"><strong>面板已生成</strong><small>选择需要的文件下载，临时文件将在 30 分钟后自动清理。</small></div>
                    <button type="button" class="format-help" data-open-format>长面板和宽面板的区别 <span>ⓘ</span></button>
                    <a href="${result.meta.zip_file}" class="btn bundle">打包下载全部</a></div>
                <div class="download-groups">
                    <section class="download-group"><h3>Excel</h3><div class="download-grid">
                        <a class="download-item featured" href="${downloads.long_excel}"><svg class="file-icon excel-file" viewBox="0 0 56 64" aria-hidden="true"><path class="paper" d="M10 2h25l15 15v41a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4V6a4 4 0 0 1 4-4Z"/><path class="fold" d="M35 2v12a3 3 0 0 0 3 3h12"/><path class="sheet-grid" d="M14 28h28v22H14zM14 35h28M14 42h28M23 28v22M33 28v22"/><path class="excel-x" d="m19 33 8 12m0-12-8 12"/></svg><span class="item-title"><strong>长面板</strong><small>推荐</small></span><b>下载 ↓</b></a>
                        <a class="download-item" href="${downloads.wide_excel}"><svg class="file-icon excel-file" viewBox="0 0 56 64" aria-hidden="true"><path class="paper" d="M10 2h25l15 15v41a4 4 0 0 1-4 4H10a4 4 0 0 1-4-4V6a4 4 0 0 1 4-4Z"/><path class="fold" d="M35 2v12a3 3 0 0 0 3 3h12"/><path class="sheet-grid" d="M14 28h28v22H14zM14 35h28M14 42h28M23 28v22M33 28v22"/><path class="excel-x" d="m19 33 8 12m0-12-8 12"/></svg><span class="item-title"><strong>宽面板</strong></span><b>下载 ↓</b></a>
                    </div></section>
                    <section class="download-group"><h3>Stata</h3><div class="download-grid">
                        <a class="download-item featured" href="${downloads.long_stata}"><svg class="file-icon stata-file" viewBox="0 0 56 64" aria-hidden="true"><rect class="dta-file-bg" x="2" y="2" width="52" height="60" rx="5"/><path class="dta-corner" d="M37 2v13a3 3 0 0 0 3 3h14"/><path class="dta-corner-fold" d="m37 2 17 16H40a3 3 0 0 1-3-3z"/><g class="dta-grid"><rect x="10" y="26" width="9" height="9"/><rect x="22" y="26" width="9" height="9"/><rect x="34" y="26" width="9" height="9"/><rect x="10" y="38" width="9" height="9"/><rect x="22" y="38" width="9" height="9"/><rect x="34" y="38" width="9" height="9"/></g><text x="28" y="57" text-anchor="middle" class="dta-label">DTA</text></svg><span class="item-title"><strong>长面板</strong><small>推荐</small></span><b>下载 ↓</b></a>
                        <a class="download-item" href="${downloads.wide_stata}"><svg class="file-icon stata-file" viewBox="0 0 56 64" aria-hidden="true"><rect class="dta-file-bg" x="2" y="2" width="52" height="60" rx="5"/><path class="dta-corner" d="M37 2v13a3 3 0 0 0 3 3h14"/><path class="dta-corner-fold" d="m37 2 17 16H40a3 3 0 0 1-3-3z"/><g class="dta-grid"><rect x="10" y="26" width="9" height="9"/><rect x="22" y="26" width="9" height="9"/><rect x="34" y="26" width="9" height="9"/><rect x="10" y="38" width="9" height="9"/><rect x="22" y="38" width="9" height="9"/><rect x="34" y="38" width="9" height="9"/></g><text x="28" y="57" text-anchor="middle" class="dta-label">DTA</text></svg><span class="item-title"><strong>宽面板</strong></span><b>下载 ↓</b></a>
                    </div></section>
                </div>
            </section>`;
        resultArea.querySelector('[data-open-format]').addEventListener('click', () => {
            document.getElementById('format-modal').style.display = 'flex';
        });
        document.querySelectorAll('[data-close-format]').forEach(button => button.onclick = () => {
            document.getElementById('format-modal').style.display = 'none';
        });
        document.getElementById('format-modal').onclick = event => {
            if (event.target.id === 'format-modal') event.currentTarget.style.display = 'none';
        };
        resultArea.style.display = 'block';
    } else {
        showModal('生成失败，请联系管理员');
    }
}

// function createTableHeader(meta) {
//     return `
//         <thead>
//             <tr>
//                 <th>行政区划代码</th>
//                 <th>层级</th>
//                 <th>分类</th>
//                 ${Array.from({length: meta.endYear - meta.startYear + 1}, 
//                     (_, i) => `<th>${meta.startYear + i}</th>`).join('')}
//             </tr>
//         </thead>
//     `;
// }

// function createTableBody(data, meta) {
//     return `
//         <tbody>
//             ${data.map(item => `
//                 <tr>
//                     <td>${item.AreaCode}</td>
//                     <td>${translateLevel(item.Level)}</td>
//                     <td>${item.Catalog}</td>
//                     ${getYearCells(item, meta.startYear, meta.endYear)}
//                 </tr>
//             `).join('')}
//         </tbody>
//     `;
// }

function translateLevel(level) {
    return {
        'province': '省级',
        'city': '地级',
        'county': '县级'
    }[level] || level;
}

function getYearCells(item, start, end) {
    return Array.from({length: end - start + 1}, (_, i) => {
        return `<td>${item[`Y${start + i}`] || '-'}</td>`;
    }).join('');
}

/* 辅助功能 */
function setLoadingState(isLoading) {
    const loading = document.querySelector('.loading-indicator');
    document.querySelectorAll('select, button, input').forEach(c => c.disabled = isLoading);
    loading.classList.toggle('active', isLoading);
}

function showToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// 显示统一模态框
function showModal(message) {
    const modal = document.getElementById('modal');
    const modalMessage = document.getElementById('modal-message');
    modalMessage.textContent = message;
    modal.style.display = 'block';

    // 关闭按钮逻辑
    const closeBtn = document.querySelector('.close');
    closeBtn.onclick = () => modal.style.display = 'none';
    modal.onclick = (e) => {
        if (e.target === modal) modal.style.display = 'none';
    };
}
