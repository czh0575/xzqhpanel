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
    for (let year = startYear; year <= 2023; year++) {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        option.selected = (year === Math.min(currentEndYear, 2023)) || (year === 2023);
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
            showModal('生成失败，请联系管理员');
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
        resultArea.innerHTML = `
            <div class="result-content">
                <p>处理成功，请点击下载：</p>
                <a href="${result.meta.downloads.zip_file}" class="btn primary">
                    <i class="fas fa-download"></i> 下载文件
                </a>
            </div>
        `;
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