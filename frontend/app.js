// import api from './ignore/apicalls.js';


const API_BASE_URL = 'http://localhost:8000';
let userID = 0;
let currentUser = null; // { token, id, type, name, email }
let specializationsCache = []; // Cache for specializations
let allDoctors = [];
let doctorsCache = []; // Cache for doctors by specialization
let token = "";
let myAppointments = [];
let  userRole = "patient";
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

function displaySuccess(message) {
    errorMessageArea.textContent = message;
    errorMessageArea.classList.add('success-message');
    errorMessageArea.classList.remove('hidden');
    setTimeout(() => errorMessageArea.classList.add('hidden'), 5000);
    setTimeout(() => errorMessageArea.classList.remove('success-message'), 5000);
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
        userGreeting.textContent = `Welcome, ${currentUser.name || currentUser.email}! (${currentUser.type})`;
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
        // console.log("API CALL RESPONSE DATA: ", responseData);
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
    // console.log(Object.fromEntries(body.entries()));
    try {
        const responseData = await api.loginPatient(loginObject);
        patientId = responseData.patient_id;
        token = responseData.access_token;
        await fetchCurrentUser(); // This will set currentUser and update UI
        allDoctors = await api.getAllDoctors();
        // console.log("ACCESS TOKENS: ", token);

    } catch (error) {

        displayError(error || 'An unexpected error occurred.');

    } finally {
        showLoading(false);
    }
}

async function getUserDetails() {
  try {
    const response = await fetch(`${API_BASE_URL}/patients/${patientId}`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    }

  });

    const responseData = await response.json();
    console.log("CURRENT USER", responseData);

    if (!response.ok) throw new Error(responseData.detail);

    return responseData;
  } catch (error) {
      console.log("Failed to fetch patients details:", error)

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
    const formData  = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    console.log(" before dob print.");
    // Convert dob to ISO string if not already
    if (data.dob) {
        // Ensure it's a valid date string before converting to avoid issues with empty or malformed dates
        console.log("dob before conversion", data.dob);
        try {
            data.date_of_birth = new Date(data.dob).toISOString().split('T')[0];
            console.log("dob after conversion", data.date_of_birth);
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

    console.log("REGISTRATION DATA: ", data)

    try {
        await CommonApiCall(endpoint, 'POST', data, false, false);
        displayError(`Registration successful as ${userType}. Please login.`); // Use displayError for success temporarily
        showView('login');
        loginForm.reset();
        form.reset(); // Reset the specific registration form
    } catch (error) {
        // Error already displayed
    }
}

function filterDoctorsBySpecialization(specializationId, allDoctors) {
    console.log("typ of specialization id: (in filtering)", typeof(specializationId));
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

        // console.log("ALL DOCTORS: ", allDoctors);
        // console.log("spec id: ", specializationId);
        // console.log("typ of specialization id: (in sp change)", typeof(specializationId));

        // console.log("filtered docs",  filterDoctorsBySpecialization(specializationId, allDoctors));
        doctorsCache = filterDoctorsBySpecialization(specializationId, allDoctors);
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
        apptDoctorSelect.innerHTML = '<option value="">Error loading doctors</option>';
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

async function handleApptDateChange() {
    const doctorId = parseInt(apptDoctorSelect.value);
    const date = apptDateInput.value;
    timeSlotsContainer.innerHTML = 'Loading slots...';
    bookAppointmentBtn.disabled = true;
    apptTimeInput.value = '';

    const body = `${date}T00:00:00.000Z`;
    console.log("INPUTE DATE: ", body);


    if (!doctorId || !date) {
        timeSlotsContainer.innerHTML = '<p>Please select a doctor and date.</p>';
        return;
    }

    try {
        const availability = await CommonApiCall(`/appointments/doctor/${doctorId}/${date}`, 'GET', null, true);
        console.log("AVAILABILITY: ", availability);
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
        displayError(error.message);
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

    const appointmentDateTime = `${date}T${time}Z`; 
    console.log("APPOINTMENT DATETIME: ", appointmentDateTime);

    try {

        await CommonApiCall('/appointments', 'POST', {
            doctor_id: parseInt(doctorId),
            patient_id: patientId,
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
        const appointments = await api.getMyAppointmets();
        
        myAppointments = await bindDocs(appointments);
        if (myAppointments.length == 0) {
            throw new Error("Unexpected error occured while retrieving your appointments.")
        }
        console.log("FULL APPOINTMENTS: ", myAppointments);
        renderAppointments(myAppointments, 'patient');
    } catch (error) {
        displayError(error.message);
    }
}

async function bindDocs(appointments) {
    if (!Array.isArray(appointments)) {
        console.error('bindDocs expects an array of appointments');
        return [];
    }

    let fullApptPromises;
    try {
        const fullApptPromises = appointments.map(async (appointment) => {
            try {
                const getDoc = await CommonApiCall(`/doctors/${appointment.doctor_id}`, 'GET', null, true);
                return { ...appointment, doctor: getDoc };
            } catch (error) {
                console.error(`Error fetching doctor for appointment ${appointment.id}:`, error.message);
                return { ...appointment, doctor: null };
            }
        });

        const completeApptList = await Promise.all(fullApptPromises);
            console.log("FULL APPOINTMENTS(BINDING FUN) befor return: ", typeof(completeApptList));
            console.log("FULL APPOINTMENTS(BINDING FUN) befor return: ", completeApptList);

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
        if (currentUser.type === 'patient') {
            fetchPatientAppointments();
        } else if (currentUser.type === 'doctor') {
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
function renderAppointments(promAppointments, userType) {

    let appointments = Array.from(promAppointments);
    console.log("APPOINTMENTS IN RENDER APPOINTMENTS typez", typeof(appointments));
    console.log("APPOINTMENTS IN RENDER APPOINTMENTS1", appointments);
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
            // console.log("CONTENT TO FIND: ", JSON.stringify(contentIdToFind));
            
            // const prefix = containerSelector.includes('patient') ? 'patient' : 'doctor';
            contentIdToFind = `${targetTabId}-appointments`;
            // console.log("CONTENT ID TO FIND: ", JSON.stringify(contentIdToFind));



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