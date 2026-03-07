const API_BASE = 'http://localhost:8000/api/v1';

async function loadRequirements() {
    const search = document.getElementById('searchInput').value;
    const status = document.getElementById('statusFilter').value;
    const priority = document.getElementById('priorityFilter').value;
    
    let url = `${API_BASE}/requirements?search=${encodeURIComponent(search)}`;
    if (status) url += `&status=${status}`;
    if (priority) url += `&priority=${priority}`;
    
    try {
        const response = await fetch(url);
        const requirements = await response.json();
        
        const tbody = document.getElementById('requirementsTable');
        tbody.innerHTML = '';
        
        requirements.forEach(req => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td><strong>${req.req_id}</strong></td>
                <td>${req.title}</td>
                <td class="priority-${req.priority}">${req.priority}</td>
                <td><span class="status-badge status-${req.status}">${req.status}</span></td>
                <td>${req.source || '-'}</td>
                <td>${new Date(req.updated_at).toLocaleDateString()}</td>
                <td class="actions">
                    <button class="btn-sm" onclick="viewRequirement('${req.req_id}')">👁️</button>
                    <button class="btn-sm" onclick="editRequirement('${req.req_id}')">✏️</button>
                    <button class="btn-sm" onclick="createLink('${req.req_id}')">🔗</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        alert('Не удалось загрузить требования');
    }
}

async function createRequirement(event) {
    event.preventDefault();
    
    const data = {
        title: document.getElementById('title').value,
        description: document.getElementById('description').value,
        priority: document.getElementById('priority').value,
        source: document.getElementById('source').value
    };
    
    try {
        const response = await fetch(`${API_BASE}/requirements`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            document.getElementById('createForm').reset();
            loadRequirements();
            alert('Требование создано!');
        } else {
            alert('Ошибка создания требования');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Ошибка соединения с сервером');
    }
}

async function exportRTM() {
    try {
        const response = await fetch(`${API_BASE}/rtm/export`);
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `rtm_export_${new Date().toISOString().split('T')[0]}.xlsx`;
        a.click();
        window.URL.revokeObjectURL(url);
    } catch (error) {
        console.error('Ошибка экспорта:', error);
        alert('Не удалось экспортировать RTM');
    }
}

function viewRequirement(reqId) {
    alert(`Просмотр требования: ${reqId}\n(Функция в разработке)`);
}

function editRequirement(reqId) {
    alert(`Редактирование требования: ${reqId}\n(Функция в разработке)`);
}

function createLink(reqId) {
    const artifactId = prompt('ID связанного артефакта:');
    if (!artifactId) return;
    
    const artifactType = prompt('Тип артефакта (Requirement/Task/TestCase):', 'Requirement');
    const linkType = prompt('Тип связи (Derives/Satisfies/Verifies/Depends):', 'Derives');
    
    fetch(`${API_BASE}/requirements/${reqId}/links`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            to_artifact_id: parseInt(artifactId),
            artifact_type: artifactType,
            link_type: linkType
        })
    }).then(r => {
        if (r.ok) alert('Связь создана!');
        else alert('Ошибка создания связи');
    });
}

document.addEventListener('DOMContentLoaded', loadRequirements);