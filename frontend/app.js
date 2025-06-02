// import api from './ignore/apicalls.js';


const API_BASE_URL = 'http://localhost:8000';

let currentUser = null; // { token, id, type, name, email }
let specializationsCache = []; // Cache for specializations
let allDoctors = [];
let doctorsCache = []; // Cache for doctors by specialization
let token = "";
let myAppointments = [];
let userRole="";


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
const loginUserTypeRadios = document.getElementById('');
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

function displaySuccess(message) {
    errorMessageArea.textContent = message;
    errorMessageArea.classList.add('success-message');
    errorMessageArea.classList.remove('hidden');
    setTimeout(() => errorMessageArea.classList.add('hidden'), 5000);
    setTimeout(() => errorMessageArea.classList.remove('success-message'), 10000);
}

function clearError() {
    errorMessageArea.classList.add('hidden');
    errorMessageArea.textContent = '';
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
        userGreeting.textContent = `${currentUser.name.toUpperCase()}  |   ${userRole.toUpperCase()}`;
    } else {
        authNav.classList.remove('hidden');
        userNav.classList.add('hidden');
        userGreeting.textContent = '';
    }
}

async function CommonApiCall(endpoint, method = 'GET', body = null, requiresAuth = false, isFormData = false) {
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
            // config.body = JSON.stringify(formContent);
            headers['Content-Type'] = 'application/json';
            
        } else {
            config.body = JSON.stringify(body);
            headers['Content-Type'] = 'application/json';
        }

    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

        const responseData = await response.json()
        if (!response.ok) {
            
            throw new Error(responseData.detail || `HTTP error! status: ${response.status}`);
        }
       
        return responseData;
    } catch (error) {
        console.error('MY API  Error Response:', error);
        displayError(error.message || 'An unexpected error occurred.');
        throw error; // Re-throw to handle in calling function if needed
    } finally {
        showLoading(false);
    }
}


// Authentication and Registration
async function handleLogin(event) {
    event.preventDefault();
    const body = new FormData(loginForm);
    const loginObject = Object.fromEntries(body.entries());
    // FastAPI OAuth2PasswordRequestForm expects 'email' and 'password'
    try {
        if (userRole == "") {
            throw new Error("Please select user: patient / doctor...")
        }
        const responseData = await userLogin(loginObject);

        token = responseData.access_token;

        sessionStorage.setItem('accessToken', token);
        sessionStorage.setItem('userRole', userRole);
        await fetchCurrentUser(); // This will set currentUser and update UI

        startDoctorsPolling();
        sessionStorage.setItem('doctorsPollingActive', 'true');

    } catch (error) {

        displayError(error.message || 'An unexpected error occurred.');

    } finally {
        showLoading(false);
    }
}


// -----------------UPDATE INFORMATION REGULARLY AFTER LOGIN---------------

let doctorsPollingInterval = null;


function startDoctorsPolling() {
    // Fetch immediately, then every 30 seconds
    fetchAndUpdateDoctors();
    doctorsPollingInterval = setInterval(fetchAndUpdateDoctors, 30000); // 30 seconds
}

function stopDoctorsPolling() {
    if (doctorsPollingInterval) clearInterval(doctorsPollingInterval);
    sessionStorage.removeItem('doctorsPollingActive');
}

async function fetchAndUpdateDoctors() {
    try {
        allDoctors = await getAllDoctors();
        console.log("udated list of doctors")        
    } catch (e) {
        console.warn("Failed to update doctors list", e.message);
    }
}

// PERSIST THE DOCTORS LOADING
window.addEventListener('load', () => {
    if (sessionStorage.getItem('doctorsPollingActive') === 'true') {
        startDoctorsPolling();
    }
});

// Login user
async function userLogin(loginObject) {
   
    try {
        
        const formBody = new URLSearchParams(loginObject);
        const response = await fetch(`${API_BASE_URL}/${userRole}s/login`, {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: formBody.toString()
        });

        const responseData = await response.json();

        if (!response.ok) throw new Error(responseData.detail);

        return responseData;
    } catch (error) {
      throw error;
    }      
}

// Get all doctors (protected)
async function getAllDoctors() {
  try {

    const response = await fetch(`${API_BASE_URL}/doctors/`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    }

  });

    const responseData = await response.json();

    if (!response.ok) throw new Error(responseData.detail);

    return responseData;
  } catch (error) {
      throw error;
  }
}

async function getUserDetails() {
  try {
    const response = await fetch(`${API_BASE_URL}/${userRole}s/me`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    }

  });

    const responseData = await response.json();
   

    if (!response.ok) throw new Error(responseData.detail);
    return responseData;
  } catch (error) {

  }
}

async function fetchCurrentUser() {
    try {
        const userData = await getUserDetails(); 

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
            type: userRole
        };

        sessionStorage.setItem('currentUser', JSON.stringify({
            id: currentUser.id,
            name: currentUser.name,
            type: userRole,
            email: currentUser.email
        }));
        updateNav();
        if (userRole === 'patient') {
            showView('patientDashboard');
            loadPatientDashboardData();
        } else if (userRole === 'doctor') {
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
    // Clear sessionStorage

    sessionStorage.clear();

    stopDoctorsPolling();
    currentUser = null;
    userRole = "";
    token = "";
    myAppointments = [];

    
    updateNav();
    showView('login');
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
    const formData  = new FormData(form);
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

        const select = document.getElementById('doctor-specialization');
        const selectedOption = select.options[select.selectedIndex];
        const selectedText = selectedOption.textContent; // or .innerText

        console.log(selectedText);

        data.specialization_name = selectedText;
        delete data.specializationId;
    }


    try {
        await CommonApiCall(endpoint, 'POST', data, false, false);
        displaySuccess(`Registration successful as ${userType}. Please login.`); // Use displayError for success temporarily
        showView('login');
        loginForm.reset();
        form.reset(); // Reset the specific registration form
    } catch (error) {
        // Error already displayed
    }
}

function filterDoctorsBySpecialization(specializationId) {
  return allDoctors.filter(doctor => doctor.specialization?.id === specializationId);
}

async function loadSpecializations() {
    try {
        specializationsCache = await CommonApiCall('/specializations', 'GET', null, false); 
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
    const specializationId = parseInt(apptSpecializationSelect.value);

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

       
        doctorsCache = filterDoctorsBySpecialization(specializationId);
        if (doctorsCache.length === 0) {
            throw new Error("Currently, there are no available doctors in this field of specialization.");
            
        }

        apptDoctorSelect.innerHTML = '<option value="">Select Doctor</option>';
        doctorsCache.forEach(doc => {
            const option = new Option(`Name: ${doc.first_name} ${doc.last_name}        
                 Age: ${calculateAge(doc.date_of_birth)}yrs                             Spec: ${doc.specialization.name}`, doc.id);
            apptDoctorSelect.add(option);
        });
        apptDoctorSelect.disabled = false;
    } catch (error) {
        displayError(error.message);
        apptDoctorSelect.innerHTML = `<option value="">${error.message}</option>`;
    }
}

function padString(str, length) {
  return str.padEnd(length, ' ');
}

function handleApptDoctorChange() {
    apptDateInput.disabled = !apptDoctorSelect.value;
    timeSlotsContainer.innerHTML = '<p>Please select a date.</p>';
    bookAppointmentBtn.disabled = true;
}

// -------------TIME SLOTS RALTIME UPDATES (wip)---------

// handle event of new date selected.
async function handleApptDateChange() {
    const doctorId = parseInt(apptDoctorSelect.value);
    const date = apptDateInput.value;
    timeSlotsContainer.innerHTML = 'Loading slots...';
    bookAppointmentBtn.disabled = true;
    apptTimeInput.value = '';

    const body = `${date}T00:00:00.000Z`;


    if (!doctorId || !date) {
        timeSlotsContainer.innerHTML = '<p>Please select a doctor and date.</p>';
        return;
    }

    try {
        const bookedSlots = await CommonApiCall(`/appointments/doctor/${doctorId}/${date}`, 'GET', null, true);
        console.log("BOOKED TIME SLOTS: ", bookedSlots);

        timeSlotsContainer.innerHTML = '';
        
        // Define fixed slots outside conditions
        const fixedSlots = ["09:00:00", "10:00:00", "11:00:00", "12:00:00", "13:00:00", "14:00:00", "15:00:00", "16:00:00"];
        
        if (Array.isArray(bookedSlots) && bookedSlots.length > 0) {
            const bookedTimesSet = new Set(
                bookedSlots.map(dateTimeStr => {
                    const timePart = dateTimeStr.split('T')[1];
                    return timePart ? timePart.substring(0, 8) : null;
                }).filter(Boolean)
            );

            fixedSlots.forEach(timeStr => {
                const slotButton = document.createElement('button');
                slotButton.type = 'button';
                slotButton.classList.add('time-slot-button');
                slotButton.textContent = timeStr.substring(0, 5); // "HH:mm"
                slotButton.dataset.time = timeStr;

                console.log("time STR: ", timeStr);

                const now = new Date();
                const currentTimeStr = now.toTimeString().substring(0, 8);
                const today = new Date().toISOString().slice(0, 10); // "YYYY-MM-DD"

                const currentDate = new Date(`${today}T${currentTimeStr}`);
                const compareDate = new Date(`${date}T${timeStr}`);

                console.log("currentTime string", currentTimeStr);

                
                if (bookedTimesSet.has(timeStr)) {
                    slotButton.classList.add('booked');
                    slotButton.disabled = true;
                } else if ((currentDate > compareDate)) {
                    slotButton.classList.add('booked');
                    slotButton.disabled = true;
                } else {
                    slotButton.addEventListener('click', selectTimeSlot);
                }

                timeSlotsContainer.appendChild(slotButton);
            });
        } else {


            const now = new Date();
            const currentTimeStr = now.toTimeString().substring(0, 8);
            const today = new Date().toISOString().slice(0, 10); // "YYYY-MM-DD"

            

            // No booked slots, render all as available
            fixedSlots.forEach(timeStr => {

                const currentDate = new Date(`${today}T${currentTimeStr}`);
                const compareDate = new Date(`${date}T${timeStr}`);

                const slotButton = document.createElement('button');
                slotButton.type = 'button';
                slotButton.classList.add('time-slot-button');
                if ((currentDate > compareDate)) {
                    slotButton.classList.add('booked');
                    slotButton.disabled = true;
                }
                slotButton.textContent = timeStr.substring(0, 5);
                slotButton.dataset.time = timeStr;
                slotButton.addEventListener('click', selectTimeSlot);
                timeSlotsContainer.appendChild(slotButton);
            });
        }

        // Show message if no buttons created
        if (timeSlotsContainer.children.length === 0) {
            timeSlotsContainer.innerHTML = '<p>No available slots for this day.</p>';
        }


    } catch (error) {
        displayError(error.message);
        timeSlotsContainer.innerHTML = '<p>Times lots unavailabel.</p>';
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

    const appointmentDateTime = `${date}T${time}Z`; 

    try {

        await CommonApiCall('/appointments', 'POST', {
            doctor_id: parseInt(doctorId),
            patient_id: currentUser.id,
            scheduled_datetime: appointmentDateTime
        }, true);
        displaySuccess('Appointment booked successfully!'); 
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
        const appointments = await getMyAppointmets();
        myAppointments = await bindAppts(appointments);
        renderAppointments(myAppointments, 'patient');
    } catch (error) {
        displayError(error.message);
    }
}

// get appiontments
async function getMyAppointmets() {

  try {
    const response = await fetch(`${API_BASE_URL}/appointments/${userRole}/${currentUser.id}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    }
  });

    const responseData = await response.json();
  
    if (!response.ok) throw new Error(responseData.detail);

    return responseData;

  } catch (error) {
      throw error;
  }
}

async function bindAppts(appointments) {
    if (!Array.isArray(appointments)) {
        console.error('bindDocs expects an array of appointments');
        return [];
    }

    let fullApptPromises;
    // user is doctor, bind patients to appointments. if user is patient, bind doctors to appointments

    try {
         fullApptPromises = appointments.map(async (appointment) => {
            try {
                let data = {};
                if (userRole == "patient" ) {
                    data = await CommonApiCall(`/doctors/${appointment.doctor_id}`, 'GET', null, true);
                    return { ...appointment, doctor: data };
                } else if (userRole == "doctor") {
                    data = await CommonApiCall(`/patients/${appointment.patient_id}`, 'GET', null, true);
                    return { ...appointment, patient: data };
                } else {
                    return appointment;
                }
            } catch (error) {
                console.error(`Error binding doctor-patient for appointment ${appointment.id}:`, error.message);
                return appointment
            }
        });

        const completeApptList = await Promise.all(fullApptPromises);
           
        return completeApptList;
        
    } catch (error) {
        console.error('Unexpected error in bindDocs:', error.message);
        displayError(error.message);
        return [];
    }
}

async function cancelAppointment(appointmentId) {
    if (!confirm("Are you sure you want to cancel this appointment?")) return;
    try {
        await CommonApiCall(`/appointments/${appointmentId}/cancel`, 'PUT', { status: 'cancelled' }, true, false);
        displayError('Appointment cancelled.'); 
        if (userRole === 'patient') {
            fetchPatientAppointments();
        } else if (userRole === 'doctor') {
            fetchDoctorAppointments();
        }
    } catch (error) {
        displayError('Unexpected error: Failed to cancel appointment.');
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
        const appointments = await getMyAppointmets();
        myAppointments = await bindAppts(appointments);

        renderAppointments(myAppointments, 'doctor');
    } catch (error) {
        displayError('Failed to fetch doctor appointments.');
    }
}

async function markAppointmentCompleted(appointmentId) {
    if (!confirm("Mark this appointment as completed?")) return;
    try {
        await CommonApiCall(`/appointments/${appointmentId}/complete`, 'PUT', { status: 'completed' }, true, false);
        displaySuccess('Appointment marked as completed.'); 
        fetchDoctorAppointments(); 
    } catch (error) {
        displayError(error.message);
    }
}

async function viewPatientDetails(patientId) {
    try {
        const patient = await CommonApiCall(`/patients/${patientId}`, 'GET'); 
        alert(`Patient Details:\nName: ${patient.first_name} ${patient.last_name}\nEmail: ${patient.email}\nPhone: ${patient.phone}\nAge: ${calculateAge(patient.date_of_birth)}yrs`);
    } catch (error) {
        displayError(error.message);
    }
}

// Common Appointment Rendering Logic
function renderAppointments(promAppointments, userType) {

    let appointments = Array.from(promAppointments);

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
        const apptDate = new Date(appt.scheduled_datetime);
        const dateString = apptDate.toLocaleDateString();
        const timeString = apptDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        if (userType === 'patient') {
            details.innerHTML = `
                <strong>Doctor:</strong> ${appt.doctor.first_name} ${appt.doctor.last_name} (${appt.doctor.specialization.name})<br>
                <strong>Date:</strong> ${dateString} <strong>Time:</strong> ${timeString}
            `;
        } else { // doctor
            details.innerHTML = `
                <strong>Patient:</strong> ${appt.patient.first_name} ${appt.patient.last_name}  (${calculateAge(appt.patient.date_of_birth)}yrs)<br>
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
                cancelBtn.onclick = () => cancelAppointment(parseInt(appt.id));
                actions.appendChild(cancelBtn);
            } else { // doctor
                const completeBtn = document.createElement('button');
                completeBtn.textContent = 'Mark Completed';
                completeBtn.classList.add('button', 'primary', 'small');
                completeBtn.onclick = () => markAppointmentCompleted(parseInt(appt.id));
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
            
            contentIdToFind = `${targetTabId}-appointments`;



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

    // login radios
    const container = document.getElementById('loginUserTypeRadios');
    const radios = container.querySelectorAll('input[type="radio"][name="userType"]');
    radios.forEach(radio => {
        radio.addEventListener('change', (event) => {
            userRole = event.target.value;
        });
    });

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

function calculateAge(birthDateString) {
  const today = new Date();
  const birthDate = new Date(birthDateString);
  let age = today.getFullYear() - birthDate.getFullYear();

  // Adjust if birthday hasn't occurred yet this year
  const monthDiff = today.getMonth() - birthDate.getMonth();
  const dayDiff = today.getDate() - birthDate.getDate();
  if (monthDiff < 0 || (monthDiff === 0 && dayDiff < 0)) {
    age--;
  }

  return `${age}`;
}

// Initialization
async function initApp() {
    setupEventListeners();

    // Retrieve stored data
    const storedToken = sessionStorage.getItem('accessToken');
    const storedUser = sessionStorage.getItem('currentUser');
    const storedRole = sessionStorage.getItem('userRole');

    if (storedToken && storedUser && storedRole) {
        try {
            token = storedToken;
            userRole = storedRole;
            currentUser = JSON.parse(storedUser);

            fetchCurrentUser(); 

            if (userRole === 'patient') {
            allDoctors = await getAllDoctors();
      }
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