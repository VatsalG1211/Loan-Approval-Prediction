
document.addEventListener('DOMContentLoaded', async function() {
    // Fetch data from the backend API
    try {
        const response = await fetch('/get-loan-data');
        const loanData = await response.json();

        // Process and display data in the table
        const table = document.getElementById('data-table');
        loanData.forEach(item => {
            const row = table.insertRow();
            Object.values(item).forEach(text => {
                const cell = row.insertCell();
                cell.textContent = text;
            });
        });

        // Prepare data for charts
        const approvalStatusCounts = {
            Approved: 0,
            Rejected: 0
        };
        const incomeByEducation = {};

        loanData.forEach(item => {
            // Count approval status
            approvalStatusCounts[item.loan_status]++;

            // Sum incomes by education level
            if (!incomeByEducation[item.education]) {
                incomeByEducation[item.education] = 0;
            }
            incomeByEducation[item.education] += item.income_annum;
        });

        // Create the Pie Chart
        const ctxPie = document.getElementById('pieChart').getContext('2d');
        new Chart(ctxPie, {
            type: 'pie',
            data: {
                labels: Object.keys(approvalStatusCounts),
                datasets: [{
                    data: Object.values(approvalStatusCounts),
                    backgroundColor: ['#4CAF50', '#F44336'], // Colors for Approved and Rejected
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });

        // Create the Bar Chart
        const ctxBar = document.getElementById('barChart').getContext('2d');
        new Chart(ctxBar, {
            type: 'bar',
            data: {
                labels: Object.keys(incomeByEducation),
                datasets: [{
                    label: 'Total Income by Education Level',
                    data: Object.values(incomeByEducation),
                    backgroundColor: '#2196F3'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error fetching data:', error);
    }
});


document.getElementById('loanForm').addEventListener('submit', async function(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = {};
    formData.forEach((value, key) => data[key] = value);

    try {
        const response = await axios.post('http://localhost:8000/predict', data, {
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const modal = document.getElementById('resultModal');
        const modalContent = document.getElementById('modalContent');
        const messageDiv = document.getElementById('message');
        const congratsGif = document.getElementById('congratsGif');
        modal.style.display = "block";
        if (response.data.prediction === "Approved") {
            
            messageDiv.innerHTML = `<span class="approved">Approved</span>`;
            congratsGif.classList.remove('hidden');
            messageDiv.innerHTML += "<p></p>";
            setTimeout(()=>{
                modal.style.display = "none";
            },4000)
        } else {
            messageDiv.innerHTML = `<span class="rejected">Rejected</span>`;
            congratsGif.classList.add('hidden');
            setTimeout(()=>{
                modal.style.display = "none";
            },4000)
        }

        modal.classList.remove('hidden');
        modal.classList.add('modal-popup');

        setTimeout(() => {
            modal.classList.add('modal-fadeout');
        }, 3500); // Start fadeout after 3.5 seconds

        setTimeout(() => {
            modal.classList.add('hidden');
            modal.classList.remove('modal-popup', 'modal-fadeout');
        }, 4000); // Hide modal after 4 seconds
    } catch (error) {
        console.error('Error making prediction:', error);
    }
});

document.getElementById('resultModal').addEventListener('click', function() {
    const modal = document.getElementById('resultModal');
    modal.classList.add('hidden');
    modal.classList.remove('modal-popup', 'modal-fadeout');
});
