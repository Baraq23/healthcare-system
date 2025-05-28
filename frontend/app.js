const API_BASE_URL = 'http://localhost:8000';
let patientId = 0;
let currentUser = null; // { token, id, type, name, email }
let specializationsCache = []; // Cache for specializations
let doctorsCache = []; // Cache for doctors by specialization
let token = "";
// DOM Elements
const views = {
    login: document.getElementById('login-view'),
    register: document.getElementById('register-view'),
    patientDashboard: document.getElementById('patient-dashboard-view'),
    doctorDashboard: document.getElementById('doctor-dashboard-view'),
};

const authNav = document.getElementById('auth-nav');
const userNav = document.getElementById('user-nav');
const userGreeting = document.getElementById('user-greeting');
const logoutBtn = document.getElementById('logout-btn');
const showLoginBtn = document.getElementById('show-login-btn');
const showRegisterBtn = document.getElementById('show-register-btn');

const loginForm = document.getElementById('login-form');
const registerUserTypeRadios = document.querySelectorAll('input[name="userType"]');
const registerPatientForm = document.getElementById('register-patient-form');
const registerDoctorForm = document.getElementById('register-doctor-form');
const doctorSpecializationSelect = document.getElementById('doctor-specialization');

const scheduleAppointmentForm = document.getElementById('schedule-appointment-form');
const apptSpecializationSelect = document.getElementById('appt-specialization');
const apptDoctorSelect = document.getElementById('appt-doctor');
const apptDateInput = document.getElementById('appt-date');
const timeSlotsContainer = document.getElementById('time-slots-container');
const bookAppointmentBtn = document.getElementById('book-appointment-btn');
const apptTimeInput = document.getElementById('appt-time');

const loadingIndicator = document.getElementById('loading-indicator');
const errorMessageArea = document.getElementById('error-message-area');

// Utility Functions
function showLoading(show) {
    loadingIndicator.classList.toggle('hidden', !show);
}

function displayError(message) {
    errorMessageArea.textContent = message;
    errorMessageArea.classList.remove('hidden');
    setTimeout(() => errorMessageArea.classList.add('hidden'), 5000);
}

function clearError() {
    errorMessageArea.classList.add('hidden');
    errorMessageArea.textContent = '';
}

async function apiCall(endpoint, method = 'GET', body = null, requiresAuth = false, isFormData = false) {
    showLoading(true);
    clearError();
    const headers = {};

    if (requiresAuth && currentUser && currentUser.token) {
        headers['Authorization'] = `Bearer ${currentUser.token}`;
    }

    const config = {
        method,
        headers,
    };

    if (body) {
        if (isFormData) {
            const formContent = Object.fromEntries(body.entries());
            console.log("FORMCONTENT", formContent);
            config.body = JSON.stringify(formContent);
            headers['Content-Type'] = 'application/json';
        } else {
            config.body = body;
            headers['Content-Type'] = 'application/json';
        }

    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        const responseData = await response.json()
        console.log("API CALL RESPONSE DATA: ", responseData);
        if (!response.ok) {
            let errorData = responseData;
            
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }
        if (response.status === 204) { // No content
            return null;
        }
        return responseData;
    } catch (error) {
        console.error('MY API  Error Response:', error.detail);
        displayError(error.message || 'An unexpected error occurred.');
        throw error; // Re-throw to handle in calling function if needed
    } finally {
        showLoading(false);
    }
}

function showView(viewId) {
    Object.values(views).forEach(view => view.classList.add('hidden'));
    if (views[viewId]) {
        views[viewId].classList.remove('hidden');
    } else {
        console.error(`View with id ${viewId} not found.`);
    }
}

function updateNav() {
    if (currentUser) {
        authNav.classList.add('hidden');
        userNav.classList.remove('hidden');
        userGreeting.textContent = `Welcome, ${currentUser.name || currentUser.email}! (${currentUser.type})`;
    } else {
        authNav.classList.remove('hidden');
        userNav.classList.add('hidden');
        userGreeting.textContent = '';
    }
}

// Authentication and Registration
async function handleLogin(event) {
    event.preventDefault();
    const body = new FormData(loginForm);
    // FastAPI OAuth2PasswordRequestForm expects 'username' and 'password'
    console.log(Object.fromEntries(body.entries()));
    try {
        const data = await apiCall('/patients/login', 'POST', body, false, true); // isFormData = true for URLSearchParams

        patientId = data.patient_id;
        token = data.access_token;
        // localStorage.setItem('accessToken', data.access_token);
        await fetchCurrentUser(); // This will set currentUser and update UI
    } catch (error) {
        // Error already displayed by apiCall
    }
}

async function fetchCurrentUser() {
    // const token = localStorage.getItem('accessToken');
    // if (!token) {
    //     logout(); // Ensure clean state if no token
    //     return;
    // }
    // currentUser = { token }; // Temporarily set token for apiCall
    try {
        const userData = await apiCall(`/patients/${patientId}`, 'GET', true); 
        currentUser = {
            token,
            id: userData.id,
            gender: userData.gender,
            first_name: userData.first_name,
            email: userData.email,
            name: `${userData.first_name} ${userData.last_name}`,
            last_name: userData.last_name,
            address: userData.address,
            created_at: userData. created_at,
            type: "patient"
        };
        localStorage.setItem('currentUser', JSON.stringify({id: currentUser.id, name: currentUser.name, type: currentUser.type, email: currentUser.email}));
        updateNav();
        if (currentUser.type === 'patient') {
            showView('patientDashboard');
            loadPatientDashboardData();
        } else if (currentUser.type === 'doctor') {
            showView('doctorDashboard');
            loadDoctorDashboardData();
        } else {
            logout(); // Unknown user type
            displayError("Unknown user type.");
        }
    } catch (error) {
        logout(); // Token might be invalid or expired
        displayError("Session expired or invalid. Please login again.");
    }
}

function logout() {
    currentUser = null;
    localStorage.removeItem('accessToken');
    localStorage.removeItem('currentUser');
    updateNav();
    showView('login');
    // Clear dashboard data if any
    clearDashboardData();
}

function clearDashboardData() {
    // Patient Dashboard
    apptSpecializationSelect.innerHTML = '<option value="">Select Specialization</option>';
    apptDoctorSelect.innerHTML = '<option value="">Select Doctor</option>';
    apptDoctorSelect.disabled = true;
    apptDateInput.value = '';
    apptDateInput.disabled = true;
    timeSlotsContainer.innerHTML = '<p>Please select a doctor and date to see availability.</p>';
    bookAppointmentBtn.disabled = true;
    document.getElementById('patient-upcoming-appointments').innerHTML = '';
    document.getElementById('patient-completed-appointments').innerHTML = '';
    document.getElementById('patient-cancelled-appointments').innerHTML = '';

    // Doctor Dashboard
    document.getElementById('doctor-upcoming-appointments').innerHTML = '';
    document.getElementById('doctor-completed-appointments').innerHTML = '';
    document.getElementById('doctor-cancelled-appointments').innerHTML = '';
}

async function handleRegister(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // Convert dob to ISO string if not already
    if (data.dob) {
        // Ensure it's a valid date string before converting to avoid issues with empty or malformed dates
        try {
            data.date_of_birth = new Date(data.dob).toISOString().split('T')[0];
        } catch (e) {
            displayError("Invalid Date of Birth format.");
            return;
        }
        delete data.dob; // remove original dob field
    }

    const userType = form.id === 'register-patient-form' ? 'patient' : 'doctor';
    const endpoint = userType === 'patient' ? '/patients' : '/doctors';

    // Map form fields to expected API fields if necessary
    // e.g. specializationId for doctors
    if (userType === 'doctor' && data.specializationId) {
        data.specialization_id = parseInt(data.specializationId, 10);
        delete data.specializationId;
    }

    try {
        await apiCall(endpoint, 'POST', data, false);
        displayError(`Registration successful as ${userType}. Please login.`); // Use displayError for success temporarily
        showView('login');
        loginForm.reset();
        form.reset(); // Reset the specific registration form
    } catch (error) {
        // Error already displayed
    }
}

async function loadSpecializations() {
    try {
        specializationsCache = await apiCall('/specializations', 'GET', null, false); 
        doctorSpecializationSelect.innerHTML = '<option value="">Select Specialization</option>';
        apptSpecializationSelect.innerHTML = '<option value="">Select Specialization</option>';
        specializationsCache.forEach(spec => {
            const option = new Option(spec.name, spec.id);
            doctorSpecializationSelect.add(option.cloneNode(true));
            apptSpecializationSelect.add(option);
        });
    } catch (error) {
        displayError('Failed to load specializations.');
        doctorSpecializationSelect.innerHTML = '<option value="">Error loading</option>';
        apptSpecializationSelect.innerHTML = '<option value="">Error loading</option>';
    }
}

// Patient Dashboard
async function loadPatientDashboardData() {
    await loadSpecializationsForBooking(); 
    await fetchPatientAppointments();
    setupPatientTabs();
}

async function loadSpecializationsForBooking() {
    if (apptSpecializationSelect.options.length <= 1 || specializationsCache.length === 0) {
        await loadSpecializations(); 
    }
}

async function handleApptSpecializationChange() {
    const specializationId = apptSpecializationSelect.value;
    apptDoctorSelect.innerHTML = '<option value="">Loading doctors...</option>';
    apptDoctorSelect.disabled = true;
    apptDateInput.disabled = true;
    timeSlotsContainer.innerHTML = '<p>Please select a doctor and date.</p>';
    bookAppointmentBtn.disabled = true;

    if (!specializationId) {
        apptDoctorSelect.innerHTML = '<option value="">Select Doctor</option>';
        return;
    }

    try {
        doctorsCache = await apiCall(`/doctors?specialization_id=${specializationId}`, 'GET');
        apptDoctorSelect.innerHTML = '<option value="">Select Doctor</option>';
        doctorsCache.forEach(doc => {
            const option = new Option(`${doc.first_name} ${doc.last_name}`, doc.id);
            apptDoctorSelect.add(option);
        });
        apptDoctorSelect.disabled = false;
    } catch (error) {
        displayError('Failed to load doctors for this specialization.');
        apptDoctorSelect.innerHTML = '<option value="">Error loading doctors</option>';
    }
}

function handleApptDoctorChange() {
    apptDateInput.disabled = !apptDoctorSelect.value;
    timeSlotsContainer.innerHTML = '<p>Please select a date.</p>';
    bookAppointmentBtn.disabled = true;
}

async function handleApptDateChange() {
    const doctorId = apptDoctorSelect.value;
    const date = apptDateInput.value;
    timeSlotsContainer.innerHTML = 'Loading slots...';
    bookAppointmentBtn.disabled = true;
    apptTimeInput.value = '';


    if (!doctorId || !date) {
        timeSlotsContainer.innerHTML = '<p>Please select a doctor and date.</p>';
        return;
    }

    try {
        const availability = await apiCall(`/appointments/availability/${doctorId}?date=${date}`, 'GET');
        timeSlotsContainer.innerHTML = '';
        
        const fixedSlots = ["09:00:00", "10:00:00", "11:00:00", "12:00:00", "13:00:00", "14:00:00", "15:00:00", "16:00:00"];
        
        if (availability && availability.length > 0) {
            const availableSlotsMap = new Map(availability.map(slot => [slot.time, slot.is_available]));

            fixedSlots.forEach(timeStr => {
                const isAvailable = availableSlotsMap.get(timeStr) !== false; 
                const slotButton = document.createElement('button');
                slotButton.type = 'button';
                slotButton.classList.add('time-slot-button');
                slotButton.textContent = timeStr.substring(0, 5); 
                slotButton.dataset.time = timeStr;

                if (!isAvailable) {
                    slotButton.classList.add('booked');
                    slotButton.disabled = true;
                } else {
                    slotButton.addEventListener('click', selectTimeSlot);
                }
                timeSlotsContainer.appendChild(slotButton);
            });
        } else {
            fixedSlots.forEach(timeStr => {
                const slotButton = document.createElement('button');
                slotButton.type = 'button';
                slotButton.classList.add('time-slot-button');
                slotButton.textContent = timeStr.substring(0, 5);
                slotButton.dataset.time = timeStr;
                slotButton.addEventListener('click', selectTimeSlot);
                timeSlotsContainer.appendChild(slotButton);
            });
        }

        if (timeSlotsContainer.children.length === 0) {
            timeSlotsContainer.innerHTML = '<p>No available slots for this day.</p>';
        }

    } catch (error) {
        displayError('Failed to load time slots.');
        timeSlotsContainer.innerHTML = '<p>Error loading slots.</p>';
    }
}

function selectTimeSlot(event) {
    document.querySelectorAll('.time-slot-button.selected').forEach(btn => btn.classList.remove('selected'));
    event.target.classList.add('selected');
    apptTimeInput.value = event.target.dataset.time;
    bookAppointmentBtn.disabled = false;
}

async function handleBookAppointment(event) {
    event.preventDefault();
    const doctorId = apptDoctorSelect.value;
    const date = apptDateInput.value;
    const time = apptTimeInput.value;

    if (!doctorId || !date || !time) {
        displayError("Please select doctor, date, and time.");
        return;
    }

    const appointmentDateTime = `${date}T${time}`; 

    try {
        await apiCall('/appointments', 'POST', {
            doctor_id: parseInt(doctorId),
            appointment_time: appointmentDateTime
        });
        displayError('Appointment booked successfully!'); 
        scheduleAppointmentForm.reset();
        apptDoctorSelect.disabled = true;
        apptDateInput.disabled = true;
        timeSlotsContainer.innerHTML = '<p>Please select a doctor and date.</p>';
        bookAppointmentBtn.disabled = true;
        fetchPatientAppointments(); 
    } catch (error) {
        // Error already displayed
    }
}

async function fetchPatientAppointments() {
    if (!currentUser || !currentUser.id) {
        displayError('User not identified. Cannot fetch appointments.');
        return;
    }
    try {
        const appointments = await apiCall(`/appointments/patient/${currentUser.id}`, 'GET');
        renderAppointments(appointments, 'patient');
    } catch (error) {
        displayError('Failed to fetch patient appointments.');
    }
}

async function cancelAppointment(appointmentId) {
    if (!confirm("Are you sure you want to cancel this appointment?")) return;
    try {
        await apiCall(`/appointments/${appointmentId}`, 'PUT', { status: 'cancelled' });
        displayError('Appointment cancelled.'); 
        if (currentUser.type === 'patient') {
            fetchPatientAppointments();
        } else if (currentUser.type === 'doctor') {
            fetchDoctorAppointments();
        }
    } catch (error) {
        displayError('Failed to cancel appointment.');
    }
}

// Doctor Dashboard
async function loadDoctorDashboardData() {
    await fetchDoctorAppointments();
    setupDoctorTabs();
}

async function fetchDoctorAppointments() {
    if (!currentUser || !currentUser.id) {
        displayError('User not identified. Cannot fetch appointments.');
        return;
    }
    try {
        const appointments = await apiCall(`/appointments/doctors/${currentUser.id}`, 'GET');
        renderAppointments(appointments, 'doctor');
    } catch (error) {
        displayError('Failed to fetch doctor appointments.');
    }
}

async function markAppointmentCompleted(appointmentId) {
    if (!confirm("Mark this appointment as completed?")) return;
    try {
        await apiCall(`/appointments/${appointmentId}`, 'PUT', { status: 'completed' });
        displayError('Appointment marked as completed.'); 
        fetchDoctorAppointments(); 
    } catch (error) {
        displayError('Failed to mark appointment as completed.');
    }
}

async function viewPatientDetails(patientId) {
    try {
        const patient = await apiCall(`/patients/${patientId}`, 'GET'); 
        alert(`Patient Details:\nName: ${patient.first_name} ${patient.last_name}\nEmail: ${patient.email}\nPhone: ${patient.phone_number}\nDOB: ${patient.date_of_birth}`);
    } catch (error) {
        displayError('Failed to fetch patient details.');
    }
}

// Common Appointment Rendering Logic
function renderAppointments(appointments, userType) {
    const upcomingList = document.getElementById(`${userType}-upcoming-appointments`);
    const completedList = document.getElementById(`${userType}-completed-appointments`);
    const cancelledList = document.getElementById(`${userType}-cancelled-appointments`);

    upcomingList.innerHTML = '';
    completedList.innerHTML = '';
    cancelledList.innerHTML = '';

    if (!appointments || appointments.length === 0) {
        upcomingList.innerHTML = '<li>No upcoming appointments.</li>';
        completedList.innerHTML = '<li>No completed appointments.</li>';
        cancelledList.innerHTML = '<li>No cancelled appointments.</li>';
        return;
    }
    
    let hasUpcoming = false, hasCompleted = false, hasCancelled = false;

    appointments.forEach(appt => {
        const item = document.createElement('li');
        const details = document.createElement('div');
        details.classList.add('details');
        const apptDate = new Date(appt.appointment_time);
        const dateString = apptDate.toLocaleDateString();
        const timeString = apptDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        if (userType === 'patient') {
            details.innerHTML = `
                <strong>Doctor:</strong> ${appt.doctor_first_name} ${appt.doctor_last_name} (${appt.doctor_specialization_name})<br>
                <strong>Date:</strong> ${dateString} <strong>Time:</strong> ${timeString}
            `;
        } else { // doctor
            details.innerHTML = `
                <strong>Patient:</strong> ${appt.patient_first_name} ${appt.patient_last_name}<br>
                <strong>Date:</strong> ${dateString} <strong>Time:</strong> ${timeString}
            `;
        }
        item.appendChild(details);

        const actions = document.createElement('div');
        actions.classList.add('actions');

        if (appt.status === 'scheduled') {
            if (userType === 'patient') {
                const cancelBtn = document.createElement('button');
                cancelBtn.textContent = 'Cancel';
                cancelBtn.classList.add('button', 'danger', 'small');
                cancelBtn.onclick = () => cancelAppointment(appt.id);
                actions.appendChild(cancelBtn);
            } else { // doctor
                const completeBtn = document.createElement('button');
                completeBtn.textContent = 'Mark Completed';
                completeBtn.classList.add('button', 'primary', 'small');
                completeBtn.onclick = () => markAppointmentCompleted(appt.id);
                actions.appendChild(completeBtn);

                const viewPatientBtn = document.createElement('button');
                viewPatientBtn.textContent = 'View Patient';
                viewPatientBtn.classList.add('button', 'secondary', 'small');
                viewPatientBtn.onclick = () => viewPatientDetails(appt.patient_id);
                actions.appendChild(viewPatientBtn);
            }
            item.appendChild(actions);
            upcomingList.appendChild(item);
            hasUpcoming = true;
        } else if (appt.status === 'completed') {
            if (userType === 'doctor' && appt.patient_id) { 
                 const viewPatientBtn = document.createElement('button');
                viewPatientBtn.textContent = 'View Patient';
                viewPatientBtn.classList.add('button', 'secondary', 'small');
                viewPatientBtn.onclick = () => viewPatientDetails(appt.patient_id);
                actions.appendChild(viewPatientBtn);
                item.appendChild(actions);
            }
            completedList.appendChild(item);
            hasCompleted = true;
        } else if (appt.status === 'cancelled') {
            cancelledList.appendChild(item);
            hasCancelled = true;
        }
    });
    
    if (!hasUpcoming) upcomingList.innerHTML = '<li>No upcoming appointments.</li>';
    if (!hasCompleted) completedList.innerHTML = '<li>No completed appointments.</li>';
    if (!hasCancelled) cancelledList.innerHTML = '<li>No cancelled appointments.</li>';
}

function setupTabs(containerSelector) {
    const tabButtons = document.querySelectorAll(`${containerSelector} .tab-button`);
    const tabContents = document.querySelectorAll(`${containerSelector} .tab-content`);

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            tabButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            tabContents.forEach(content => content.classList.add('hidden'));
            const targetTabId = button.dataset.tab;

            let contentIdToFind = targetTabId;
            if (!targetTabId.endsWith('-appointments')) { 
                 const prefix = containerSelector.includes('patient') ? 'patient' : 'doctor';
                 contentIdToFind = `${prefix}-${targetTabId}-appointments`;
            }

            const targetContent = document.getElementById(contentIdToFind);
            if (targetContent) {
                targetContent.classList.remove('hidden');
            } else {
                document.getElementById(targetTabId).classList.remove('hidden');
            }

        });
    });
}

function setupPatientTabs() {
    setupTabs('#patient-dashboard-view');
}
function setupDoctorTabs() {
    setupTabs('#doctor-dashboard-view');
}

// Event Listeners
function setupEventListeners() {
    showLoginBtn.addEventListener('click', () => { clearError(); showView('login'); });
    showRegisterBtn.addEventListener('click', () => { clearError(); showView('register'); loadSpecializations(); }); 
    logoutBtn.addEventListener('click', logout);

    loginForm.addEventListener('submit', handleLogin);
    registerPatientForm.addEventListener('submit', handleRegister);
    registerDoctorForm.addEventListener('submit', handleRegister);

    registerUserTypeRadios.forEach(radio => {
        radio.addEventListener('change', (event) => {
            if (event.target.value === 'patient') {
                registerPatientForm.classList.remove('hidden');
                registerDoctorForm.classList.add('hidden');
            } else {
                registerPatientForm.classList.add('hidden');
                registerDoctorForm.classList.remove('hidden');
                if (doctorSpecializationSelect.options.length <= 1) { 
                    loadSpecializations();
                }
            }
        });
    });

    apptSpecializationSelect.addEventListener('change', handleApptSpecializationChange);
    apptDoctorSelect.addEventListener('change', handleApptDoctorChange);
    apptDateInput.addEventListener('change', handleApptDateChange);
    scheduleAppointmentForm.addEventListener('submit', handleBookAppointment);

}

// Initialization
function initApp() {
    setupEventListeners();
    const storedUser = localStorage.getItem('currentUser');
    const token = localStorage.getItem('accessToken');

    if (token && storedUser) {
        try {
            currentUser = JSON.parse(storedUser);
            currentUser.token = token; 
            fetchCurrentUser(); 
        } catch(e) {
            console.error("Error parsing stored user, logging out.");
            logout();
        }
    } else {
        updateNav();
        showView('login');
    }
}

document.addEventListener('DOMContentLoaded', initApp);