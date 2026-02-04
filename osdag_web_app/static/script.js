function addPointLoad() {
    const container = document.getElementById('loads-container');
    const div = document.createElement('div');
    div.className = 'load-item point-load';
    div.innerHTML = `
        <button class="remove-btn" onclick="this.parentElement.remove()">×</button>
        <div class="row"><strong>Point Load</strong></div>
        <div class="row">
            <div class="input-group">
                <label>Force (kN)</label>
                <input type="number" class="val-mag" value="10">
            </div>
            <div class="input-group">
                <label>Position (m)</label>
                <input type="number" class="val-pos" value="5">
            </div>
        </div>
    `;
    container.appendChild(div);
}

function addUDL() {
    const container = document.getElementById('loads-container');
    const div = document.createElement('div');
    div.className = 'load-item udl-load';
    div.innerHTML = `
        <button class="remove-btn" onclick="this.parentElement.remove()">×</button>
        <div class="row"><strong>UDL</strong></div>
        <div class="row">
            <div class="input-group">
                <label>Force (kN/m)</label>
                <input type="number" class="val-mag" value="5">
            </div>
            <div class="input-group">
                <label>Start (m)</label>
                <input type="number" class="val-start" value="0">
            </div>
            <div class="input-group">
                <label>End (m)</label>
                <input type="number" class="val-end" value="4">
            </div>
        </div>
    `;
    container.appendChild(div);
}

function analyzeBeam() {
    // 1. Gather Data
    const loads = [];
    document.querySelectorAll('.load-item').forEach(item => {
        const mag = item.querySelector('.val-mag').value;

        if (item.classList.contains('point-load')) {
            const pos = item.querySelector('.val-pos').value;
            loads.push({ type: 'point', mag: mag, pos: pos });
        } else {
            const start = item.querySelector('.val-start').value;
            const end = item.querySelector('.val-end').value;
            loads.push({ type: 'udl', mag: mag, start: start, end: end });
        }
    });

    // 2. Send to Server
    fetch('/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ loads: loads })
    })
        .then(response => response.json())
        .then(data => {
            // 3. Update UI
            document.getElementById('welcome-message').style.display = 'none';
            document.getElementById('results-content').style.display = 'block';

            document.getElementById('val-ra').innerText = data.ra + " kN";
            document.getElementById('val-rb').innerText = data.rb + " kN";

            document.getElementById('sfd-img').src = "data:image/png;base64," + data.sfd;
            document.getElementById('bmd-img').src = "data:image/png;base64," + data.bmd;
        })
        .catch(err => alert("Error analyzing: " + err));
}
