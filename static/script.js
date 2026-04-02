// ============================================================
// EasyCert Barangay Certificate System — v3.0
// ============================================================

let allRequests = []
let currentCertificateType = ""
let currentRequestForReview = null
let monthlyChartInstance = null
let typeChartInstance = null
let weeklyChartInstance = null
let isAdminLoggedIn = false
let currentAdminRole = ""
let csrfToken = ""
let adminRefreshInterval = null
const ADMIN_REFRESH_MS = 30000 // auto-refresh every 30 seconds

// ============================================================
// CERTIFICATE TYPES
// ============================================================
const certificateTypes = [
    { name: "Cedula", icon: "📋", color: "#00B894", desc: "Community tax certificate." },
    { name: "Barangay Clearance", icon: "🛡️", color: "#2C7BE5", desc: "For employment, permits, and clearance." },
    { name: "Barangay Residency", icon: "🏠", color: "#00B894", desc: "Proof of residency within the barangay." },
    { name: "Barangay Indigency", icon: "🤝", color: "#2C7BE5", desc: "For financial assistance and social services." },
    { name: "Certificate of Low Income", icon: "💼", color: "#00B894", desc: "For applicants with low monthly income." },
    { name: "Certificate for No Income", icon: "📄", color: "#2C7BE5", desc: "For applicants with no source of income." },
    { name: "Business Permit", icon: "🏪", color: "#2C7BE5", desc: "Required for barangay business operations." },
    { name: "Barangay Identification", icon: "🪪", color: "#00B894", desc: "Official barangay ID card." }
]

// ============================================================
// PURPOSE OPTIONS (for certs that include a purpose section)
// ============================================================
const purposeOptions = [
    { value: "Employment", icon: "fa-briefcase", label: "Employment" },
    { value: "Scholarship", icon: "fa-graduation-cap", label: "Scholarship" },
    { value: "Identification", icon: "fa-id-card", label: "ID / Renewal" },
    { value: "Business Requirement", icon: "fa-store", label: "Business Permit" },
    { value: "Loan Application", icon: "fa-money-bill-wave", label: "Loan Application" },
    { value: "Travel Abroad", icon: "fa-plane", label: "Travel Abroad" },
    { value: "Other", icon: "fa-ellipsis", label: "Other" }
]

// ============================================================
// FORM SCHEMAS — one per certificate type
// ============================================================
const formSchemas = {

    "Cedula": [
        {
            title: "PERSONAL INFORMATION",
            fields: [
                { id: "last-name", label: "Last Name", type: "text", req: true, ph: "Dela Cruz", col: 1 },
                { id: "first-name", label: "First Name", type: "text", req: true, ph: "Juan", col: 1 },
                { id: "middle-name", label: "Middle Name", type: "text", req: false, ph: "Reyes", col: 1 },
                { id: "address", label: "Address", type: "text", req: true, ph: "123 Sampaguita St., Sitio Central", col: 2 },
                { id: "age", label: "Age", type: "number", req: true, ph: "30", col: 1 },
                { id: "birthday", label: "Birthday", type: "date", req: true, ph: "", col: 1 },
                { id: "birthplace", label: "Birthplace", type: "text", req: true, ph: "Cebu City", col: 1 },
                { id: "income", label: "Annual Income (₱)", type: "number", req: true, ph: "120000", col: 1 }
            ]
        }
    ],

    "Barangay Clearance": [
        {
            title: "PERSONAL INFORMATION",
            fields: [
                { id: "last-name", label: "Last Name", type: "text", req: true, ph: "Dela Cruz", col: 1 },
                { id: "first-name", label: "First Name", type: "text", req: true, ph: "Juan", col: 1 },
                { id: "middle-name", label: "Middle Name", type: "text", req: false, ph: "Reyes", col: 1 },
                { id: "sitio", label: "Sitio / Zone", type: "text", req: true, ph: "e.g. Sitio Central", col: 1 },
                { id: "gender", label: "Gender", type: "select", req: true, opts: ["Male", "Female", "Prefer not to say"], col: 1 }
            ]
        },
        { title: "PURPOSE OF REQUEST", fields: [{ type: "purpose", withScholarship: false }] }
    ],

    "Barangay Residency": [
        {
            title: "PERSONAL INFORMATION",
            fields: [
                { id: "last-name", label: "Last Name", type: "text", req: true, ph: "Dela Cruz", col: 1 },
                { id: "first-name", label: "First Name", type: "text", req: true, ph: "Juan", col: 1 },
                { id: "middle-name", label: "Middle Name", type: "text", req: false, ph: "Reyes", col: 1 },
                { id: "sitio", label: "Sitio / Zone", type: "text", req: true, ph: "e.g. Sitio Central", col: 1 },
                { id: "years-of-living", label: "Years of Living", type: "number", req: true, ph: "5", col: 1 }
            ]
        },
        { title: "PURPOSE OF REQUEST", fields: [{ type: "purpose", withScholarship: true }] }
    ],

    "Barangay Indigency": [
        {
            title: "PERSONAL INFORMATION",
            fields: [
                { id: "last-name", label: "Last Name", type: "text", req: true, ph: "Dela Cruz", col: 1 },
                { id: "first-name", label: "First Name", type: "text", req: true, ph: "Juan", col: 1 },
                { id: "middle-name", label: "Middle Name", type: "text", req: false, ph: "Reyes", col: 1 },
                { id: "sitio", label: "Sitio / Zone", type: "text", req: true, ph: "e.g. Sitio Central", col: 1 },
                { id: "gender", label: "Gender", type: "select", req: true, opts: ["Male", "Female", "Prefer not to say"], col: 1 }
            ]
        },
        { title: "PURPOSE OF REQUEST", fields: [{ type: "purpose", withScholarship: true }] }
    ],

    "Certificate of Low Income": [
        {
            title: "PERSONAL INFORMATION",
            fields: [
                { id: "last-name", label: "Last Name", type: "text", req: true, ph: "Dela Cruz", col: 1 },
                { id: "first-name", label: "First Name", type: "text", req: true, ph: "Juan", col: 1 },
                { id: "middle-name", label: "Middle Name", type: "text", req: false, ph: "Reyes", col: 1 },
                { id: "sitio", label: "Sitio / Zone", type: "text", req: true, ph: "e.g. Sitio Central", col: 1 },
                { id: "monthly-income", label: "Monthly Income (₱)", type: "number", req: true, ph: "5000", col: 1 },
                { id: "work", label: "Occupation / Work", type: "text", req: true, ph: "e.g. Farmer, Driver", col: 1 }
            ]
        },
        { title: "PURPOSE OF REQUEST", fields: [{ type: "purpose", withScholarship: true }] }
    ],

    "Certificate for No Income": [
        {
            title: "PERSONAL INFORMATION",
            fields: [
                { id: "last-name", label: "Last Name", type: "text", req: true, ph: "Dela Cruz", col: 1 },
                { id: "first-name", label: "First Name", type: "text", req: true, ph: "Juan", col: 1 },
                { id: "middle-name", label: "Middle Name", type: "text", req: false, ph: "Reyes", col: 1 },
                { id: "address", label: "Address", type: "text", req: true, ph: "123 Sampaguita St., Sitio Central", col: 2 }
            ]
        },
        { title: "PURPOSE OF REQUEST", fields: [{ type: "purpose", withScholarship: true }] }
    ],

    "Business Permit": [
        {
            title: "OWNER INFORMATION",
            fields: [
                { id: "last-name", label: "Last Name", type: "text", req: true, ph: "Dela Cruz", col: 1 },
                { id: "first-name", label: "First Name", type: "text", req: true, ph: "Juan", col: 1 },
                { id: "middle-name", label: "Middle Name", type: "text", req: false, ph: "Reyes", col: 1 },
                { id: "sitio", label: "Store Address / Sitio", type: "text", req: true, ph: "Address of your store", col: 1 },
                {
                    id: "permit-type", label: "Application Type", type: "radio-cards", req: true, col: 2,
                    opts: [
                        { value: "New", icon: "fa-star", label: "New", desc: "First time application" },
                        { value: "Renewal", icon: "fa-rotate", label: "Renewal", desc: "Renewing existing permit" }
                    ]
                }
            ]
        },
        {
            title: "BUSINESS DETAILS",
            fields: [
                { id: "business-type", label: "Business Type", type: "text", req: true, ph: "e.g. Sari-sari Store, Salon", col: 1 },
                { id: "business-name", label: "Business Name", type: "text", req: true, ph: "e.g. Juan's Store", col: 1 },
                { id: "capital", label: "Capital Amount (₱)", type: "number", req: true, ph: "50000", col: 1 },
                { id: "gross-income", label: "Gross Income (₱)", type: "number", req: true, ph: "120000", col: 1 }
            ]
        }
    ],

    "Barangay Identification": [
        {
            title: "PERSONAL INFORMATION",
            fields: [
                { id: "last-name", label: "Last Name", type: "text", req: true, ph: "Dela Cruz", col: 1 },
                { id: "first-name", label: "First Name", type: "text", req: true, ph: "Juan", col: 1 },
                { id: "middle-name", label: "Middle Name", type: "text", req: false, ph: "Reyes", col: 1 },
                { id: "sitio", label: "Sitio / Zone", type: "text", req: true, ph: "e.g. Sitio Central", col: 1 },
                { id: "age", label: "Age", type: "number", req: true, ph: "30", col: 1 },
                { id: "birthday", label: "Birthday", type: "date", req: true, ph: "", col: 1 }
            ]
        }
    ]
}

// ============================================================
// FORM RENDERERS
// ============================================================
function renderField(f) {
    const reqMark = f.req
        ? `<span class="text-red-400">*</span>`
        : `<span class="text-[#333333]/40 text-xs">(optional)</span>`
    const spanClass = f.col === 2 ? ' sm:col-span-2' : ''

    if (f.type === 'purpose') {
        return renderPurposeSection(f.withScholarship)
    }
    if (f.type === 'radio-cards') {
        return renderRadioCards(f)
    }
    if (f.type === 'select') {
        const opts = f.opts.map(o => `<option value="${o}">${o}</option>`).join('')
        return `
            <div class="${spanClass}">
                <label class="block text-sm mb-2 font-medium">${f.label} ${reqMark}</label>
                <select id="${f.id}" ${f.req ? 'required' : ''} class="form-input w-full">
                    <option value="">Select...</option>${opts}
                </select>
            </div>`
    }
    // default: text/number/date input
    return `
        <div class="${spanClass}">
            <label class="block text-sm mb-2 font-medium">${f.label} ${reqMark}</label>
            <input id="${f.id}" type="${f.type}" ${f.req ? 'required' : ''}
                   placeholder="${f.ph || ''}" class="form-input w-full">
        </div>`
}

function renderRadioCards(f) {
    const spanClass = f.col === 2 ? ' sm:col-span-2' : ''
    const cards = f.opts.map(o => `
        <label class="radio-card glass p-4 rounded-2xl cursor-pointer border-2 border-transparent
                      hover:border-[#2C7BE5] transition-all flex items-center gap-x-3"
               onclick="selectRadioCard(this, '${f.id}')">
            <input type="radio" name="${f.id}" value="${o.value}" class="hidden" required>
            <i class="fa-solid ${o.icon} text-[#2C7BE5] text-lg"></i>
            <div>
                <div class="font-semibold text-sm">${o.label}</div>
                ${o.desc ? `<div class="text-xs text-[#333333]/50">${o.desc}</div>` : ''}
            </div>
        </label>`).join('')
    return `
        <div class="${spanClass}">
            <label class="block text-sm mb-2 font-medium">${f.label} <span class="text-red-400">*</span></label>
            <div class="grid grid-cols-2 gap-3">${cards}</div>
        </div>`
}

function renderPurposeSection(withScholarship) {
    const tiles = purposeOptions.map(p => `
        <label class="purpose-option glass p-4 rounded-2xl cursor-pointer border-2 border-transparent
                      hover:border-[#2C7BE5] transition-all flex items-center gap-x-3"
               onclick="selectPurpose(this, '${p.value}', ${!!withScholarship})">
            <input type="radio" name="purpose-radio" value="${p.value}" class="hidden">
            <i class="fa-solid ${p.icon} text-[#2C7BE5]"></i>
            <span class="font-medium text-sm">${p.label}</span>
        </label>`).join('')

    const scholarshipBlock = withScholarship ? `
        <div id="scholarship-group" class="hidden mt-4 p-5 bg-blue-50/60 rounded-3xl border border-[#2C7BE5]/20">
            <div class="flex items-center gap-x-2 text-[#2C7BE5] text-xs font-semibold mb-4">
                <i class="fa-solid fa-graduation-cap"></i>
                <span>SCHOLARSHIP DETAILS</span>
            </div>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="sm:col-span-2">
                    <label class="block text-sm mb-2 font-medium">
                        Student's Full Name <span class="text-red-400">*</span>
                    </label>
                    <input id="student-name" type="text"
                           placeholder="Full name of the student applying for scholarship"
                           class="form-input w-full">
                </div>
                <div>
                    <label class="block text-sm mb-2 font-medium">
                        School / University <span class="text-red-400">*</span>
                    </label>
                    <input id="student-school" type="text"
                           placeholder="e.g. University of San Carlos"
                           class="form-input w-full">
                </div>
                <div>
                    <label class="block text-sm mb-2 font-medium">Year Level</label>
                    <select id="student-year" class="form-input w-full">
                        <option value="">Select year level</option>
                        <option>Grade School</option>
                        <option>High School</option>
                        <option>Senior High School</option>
                        <option>1st Year College</option>
                        <option>2nd Year College</option>
                        <option>3rd Year College</option>
                        <option>4th Year College</option>
                        <option>Graduate School</option>
                    </select>
                </div>
            </div>
        </div>` : ''

    return `
        <div class="sm:col-span-2">
            <input type="hidden" id="purpose" value="">
            <div class="grid grid-cols-2 sm:grid-cols-3 gap-3">${tiles}</div>
            ${scholarshipBlock}
            <div id="other-purpose-group" class="hidden mt-4">
                <label class="block text-sm mb-2 font-medium">
                    Please specify <span class="text-red-400">*</span>
                </label>
                <input id="other-purpose-text" type="text"
                       placeholder="Describe purpose..." class="form-input w-full">
            </div>
        </div>`
}

function renderDynamicForm(certName) {
    const schema = formSchemas[certName]
    if (!schema) return `<p class="text-red-400 text-sm p-4">Form schema not found for "${certName}".</p>`

    return schema.map(section => `
        <div>
            <h4 class="section-label">
                <span class="w-5 h-px bg-[#2C7BE5] inline-block"></span>
                ${section.title}
            </h4>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-5">
                ${section.fields.map(renderField).join('')}
            </div>
        </div>`).join('')
}

// ============================================================
// PURPOSE / RADIO CARD INTERACTION
// ============================================================
function selectPurpose(el, value, withScholarship) {
    document.querySelectorAll('.purpose-option').forEach(l => l.classList.remove('selected'))
    el.classList.add('selected')

    const hidden = document.getElementById('purpose')
    if (hidden) hidden.value = value

    // Scholarship reveal
    const sg = document.getElementById('scholarship-group')
    if (sg) {
        const show = value === 'Scholarship'
        sg.classList.toggle('hidden', !show)
        const sn = document.getElementById('student-name')
        const ss = document.getElementById('student-school')
        if (sn) sn.required = show
        if (ss) ss.required = show
    }

    // Other reveal
    const og = document.getElementById('other-purpose-group')
    if (og) og.classList.toggle('hidden', value !== 'Other')
}

function selectRadioCard(el, groupId) {
    el.closest('.grid')?.querySelectorAll('.radio-card').forEach(c => c.classList.remove('selected'))
    el.classList.add('selected')
}

// ============================================================
// CSRF
// ============================================================
function generateCSRF() {
    const arr = new Uint8Array(16)
    crypto.getRandomValues(arr)
    return Array.from(arr, b => b.toString(16).padStart(2, '0')).join('')
}

// ============================================================
// TRACKING NUMBER
// ============================================================
function generateTrackingNumber() {
    return `EC-${new Date().getFullYear()}-${Math.floor(10000 + Math.random() * 90000)}`
}

// ============================================================
// LOCAL STORAGE
// ============================================================
function saveToLocalStorage() {
    try { localStorage.setItem("easycert_requests", JSON.stringify(allRequests)) }
    catch (e) { console.warn("localStorage unavailable:", e) }
}

function loadFromLocalStorage() {
    try {
        const saved = localStorage.getItem("easycert_requests")
        if (saved) allRequests = JSON.parse(saved)
        else seedSampleData()
    } catch (e) { seedSampleData() }
}

function seedSampleData() {
    allRequests = [
        {
            tracking: "EC-2026-00123", name: "Santos, Maria R.",
            type: "Barangay Clearance", sitio: "Sitio Central",
            status: "Approved", date: "2026-03-15", purpose: "Employment", appointment: "9:00 AM",
            fields: { "last-name": "Santos", "first-name": "Maria", "middle-name": "Reyes", "sitio": "Sitio Central", "gender": "Female" }
        },
        {
            tracking: "EC-2026-00124", name: "Dela Cruz, Juan P.",
            type: "Business Permit", sitio: "45 Rizal Ave., Sitio Proper",
            status: "Pending", date: "2026-03-16", purpose: "Business Requirement", appointment: "1:30 PM",
            fields: { "last-name": "Dela Cruz", "first-name": "Juan", "middle-name": "Pedro", "sitio": "45 Rizal Ave., Sitio Proper", "permit-type": "New", "business-type": "Sari-sari Store", "business-name": "Juan's Store", "capital": "50000", "gross-income": "120000" }
        },
        {
            tracking: "EC-2026-00125", name: "Reyes, Liza A.",
            type: "Barangay Indigency", sitio: "Sitio Riverside",
            status: "Pending", date: "2026-03-17", purpose: "Scholarship", appointment: "10:30 AM",
            fields: { "last-name": "Reyes", "first-name": "Liza", "middle-name": "Andres", "sitio": "Sitio Riverside", "gender": "Female" },
            scholarshipData: { studentName: "Liza A. Reyes", school: "Cebu Normal University", yearLevel: "2nd Year College" }
        },
        {
            tracking: "EC-2026-00126", name: "Villanueva, Ana C.",
            type: "Cedula", sitio: "Sitio Central",
            status: "Approved", date: "2026-03-18", purpose: "", appointment: "7:30 AM",
            fields: { "last-name": "Villanueva", "first-name": "Ana", "middle-name": "Cruz", "address": "23 Acacia St., Sitio Central", "age": "31", "birthday": "1995-03-20", "birthplace": "Cebu City", "income": "96000" }
        }
    ]
    saveToLocalStorage()
}

// ============================================================
// RENDER CERTIFICATE CARDS
// ============================================================
function renderCertificateCards() {
    const container = document.getElementById("certificate-grid")
    if (!container) return
    container.innerHTML = ""

    certificateTypes.forEach(cert => {
        const card = document.createElement("div")
        card.className = "cert-card glass rounded-3xl p-5 sm:p-7 flex flex-col items-center text-center"
        card.setAttribute("role", "button")
        card.setAttribute("tabindex", "0")
        card.innerHTML = `
            <div class="text-5xl sm:text-7xl mb-4 sm:mb-6 cert-icon">${cert.icon}</div>
            <h4 class="font-semibold text-base sm:text-xl mb-1 sm:mb-2">${cert.name}</h4>
            <p class="text-xs text-[#333333]/50 mb-4 sm:mb-6 hidden sm:block">${cert.desc}</p>
            <button onclick="selectCertificate('${cert.name}'); event.stopImmediatePropagation()"
                    class="text-xs bg-white hover:bg-[#F2F9FF] px-5 sm:px-6 py-2 sm:py-3 rounded-2xl font-semibold
                           text-[#2C7BE5] shadow-inner border border-[#2C7BE5]/20 transition-colors">
                SELECT
            </button>`
        card.onclick = () => selectCertificate(cert.name)
        card.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') selectCertificate(cert.name) }
        container.appendChild(card)
    })

    const typeFilter = document.getElementById("type-filter")
    if (typeFilter) {
        typeFilter.innerHTML = '<option value="">All Types</option>'
        certificateTypes.forEach(c => { typeFilter.innerHTML += `<option value="${c.name}">${c.name}</option>` })
    }
}

// ============================================================
// SELECT CERTIFICATE
// ============================================================
function selectCertificate(name) {
    currentCertificateType = name
    const cert = certificateTypes.find(c => c.name === name)
    document.getElementById("modal-title").textContent = name
    document.getElementById("modal-icon").innerHTML = cert ? cert.icon : "📄"

    csrfToken = generateCSRF()
    const csrfEl = document.getElementById("csrf-token")
    if (csrfEl) csrfEl.value = csrfToken
    document.getElementById("dynamic-fields").innerHTML = renderDynamicForm(name)

    // Clear time selection
    document.querySelectorAll('input[name="time"]').forEach(r => r.checked = false)

    openModal("request-modal")
    document.querySelector('#request-modal > div')?.scrollTo(0, 0)
}

function closeRequestModal() { closeModal("request-modal") }

// ============================================================
// COLLECT FORM DATA
// ============================================================
function collectFormData() {
    const g = id => { const el = document.getElementById(id); return el ? el.value.trim() : '' }

    const ln = g('last-name'), fn = g('first-name'), mn = g('middle-name')
    const displayName = ln && fn
        ? `${ln}, ${fn}${mn ? ' ' + mn.charAt(0) + '.' : ''}`
        : 'Unknown'

    // Collect all schema fields
    const schema = formSchemas[currentCertificateType] || []
    const fields = {}
    schema.forEach(section => {
        section.fields.forEach(f => {
            if (!f.id || f.type === 'purpose') return
            if (f.type === 'radio-cards') {
                const checked = document.querySelector(`input[name="${f.id}"]:checked`)
                fields[f.id] = checked ? checked.value : ''
            } else {
                fields[f.id] = g(f.id)
            }
        })
    })

    const rawPurpose = g('purpose')
    const purpose = rawPurpose === 'Other' ? (g('other-purpose-text') || 'Other') : rawPurpose

    let scholarshipData = null
    if (rawPurpose === 'Scholarship') {
        scholarshipData = {
            studentName: g('student-name'),
            school: g('student-school'),
            yearLevel: g('student-year')
        }
    }

    const sitio = g('sitio') || g('address') || ''
    const address = g('address') || g('sitio') || ''

    return { displayName, fields, purpose, sitio, address, scholarshipData }
}

// ============================================================
// SUBMIT REQUEST
// ============================================================
function submitRequest(e) {
    e.preventDefault()

    // CSRF check
    const csrfEl = document.getElementById("csrf-token")
    if (csrfEl && csrfEl.value !== csrfToken) {
        showToast("Refresh the page and try again.", "Security Error", "error"); return
    }

    // Purpose validation (only for certs that have a purpose section)
    const purposeEl = document.getElementById("purpose")
    if (purposeEl && !purposeEl.value) {
        showToast("Please select a purpose for your request.", "Missing Field", "error"); return
    }

    // Appointment validation
    const timeEl = document.querySelector('input[name="time"]:checked')
    if (!timeEl) {
        showToast("Please select a pickup schedule.", "Missing Field", "error"); return
    }

    const { displayName, fields, purpose, sitio, address, scholarshipData } = collectFormData()
    const tracking = generateTrackingNumber()

    allRequests.unshift({
        tracking, name: displayName, type: currentCertificateType,
        sitio, address, purpose, status: "Pending",
        date: new Date().toISOString().split("T")[0],
        appointment: timeEl.value, fields, scholarshipData,
        csrfToken
    })

    saveToLocalStorage()
    closeRequestModal()
    showSuccessModal(tracking, timeEl.value)
    if (isAdminLoggedIn) refreshAdminData()
}

// ============================================================
// SUCCESS MODAL
// ============================================================
function showSuccessModal(tracking, appointment) {
    document.getElementById("success-tracking").textContent = tracking
    const apptInfo = document.getElementById("success-appointment-info")
    const apptText = document.getElementById("success-appointment-text")
    if (appointment) {
        apptText.textContent = `Pickup on next working day at ${appointment}`
        apptInfo.classList.remove("hidden")
    } else {
        apptInfo.classList.add("hidden")
    }
    openModal("success-modal")
}

function closeSuccessModal() { closeModal("success-modal") }

function copyTracking() {
    const num = document.getElementById("success-tracking").textContent
    if (navigator.clipboard) {
        navigator.clipboard.writeText(num).then(() => showToast("Tracking number copied to clipboard.", "Copied!", "success"))
    } else {
        const el = document.createElement("textarea"); el.value = num
        document.body.appendChild(el); el.select(); document.execCommand("copy")
        document.body.removeChild(el); showToast("Tracking number copied to clipboard.", "Copied!", "success")
    }
}

// ============================================================
// TRACK MODAL
// ============================================================
function showTrackModal() {
    document.getElementById("track-result").classList.add("hidden")
    document.getElementById("track-input").value = ""
    openModal("track-modal")
    setTimeout(() => document.getElementById("track-input").focus(), 150)
}

function closeTrackModal() { closeModal("track-modal") }

function trackRequest() {
    const input = document.getElementById("track-input").value.trim().toUpperCase()
    const found = allRequests.find(r => r.tracking === input)
    const resultDiv = document.getElementById("track-result")
    resultDiv.innerHTML = ""

    if (found) {
        const statusMap = {
            Approved: { html: `<span class="badge-approved">READY FOR PICKUP</span>`, icon: `<i class="fa-solid fa-circle-check text-[#00B894] text-2xl"></i>` },
            Pending: { html: `<span class="badge-pending">UNDER REVIEW</span>`, icon: `<i class="fa-solid fa-hourglass text-amber-500 text-2xl"></i>` },
            Rejected: { html: `<span class="badge-rejected">REJECTED</span>`, icon: `<i class="fa-solid fa-circle-xmark text-red-500 text-2xl"></i>` }
        }
        const s = statusMap[found.status] || statusMap.Pending
        resultDiv.innerHTML = `
            <div class="glass p-6 rounded-3xl slide-in">
                <div class="flex items-start justify-between mb-5">
                    <div>
                        <div class="text-xs font-medium text-[#333333]/50 uppercase tracking-widest">TRACKING NO.</div>
                        <div class="font-mono text-2xl sm:text-3xl text-[#2C7BE5] font-bold">${found.tracking}</div>
                    </div>
                    <div class="flex flex-col items-end gap-y-2">${s.icon}${s.html}</div>
                </div>
                <div class="grid grid-cols-2 gap-x-4 gap-y-3 text-sm mb-4">
                    <div class="font-medium text-[#333333]/50">Name</div>       <div class="font-semibold">${found.name}</div>
                    <div class="font-medium text-[#333333]/50">Certificate</div><div>${found.type}</div>
                    <div class="font-medium text-[#333333]/50">Purpose</div>    <div>${found.purpose || '—'}</div>
                    <div class="font-medium text-[#333333]/50">Appointment</div><div class="font-semibold">${found.appointment || 'Not set'}</div>
                    <div class="font-medium text-[#333333]/50">Date Filed</div> <div>${found.date}</div>
                </div>
                ${found.status === "Approved" ? `
                <button onclick="showCertificatePreview(allRequests.find(r=>r.tracking==='${found.tracking}'))"
                    class="w-full py-3 bg-[#00B894] text-white rounded-2xl text-sm font-semibold
                           flex items-center justify-center gap-x-2 hover:bg-[#00a382] transition-colors mt-2">
                    <i class="fa-solid fa-file"></i> View Certificate
                </button>` : ""}
            </div>`
    } else {
        resultDiv.innerHTML = `
            <div class="text-center py-10 text-[#333333]/40 slide-in">
                <i class="fa-solid fa-magnifying-glass text-4xl mb-4 block"></i>
                <p class="font-medium">No request found with that tracking number.</p>
                <p class="text-xs mt-1">Format: EC-YYYY-XXXXX</p>
            </div>`
    }
    resultDiv.classList.remove("hidden")
}

// ============================================================
// ADMIN LOGIN / LOGOUT
// ============================================================
function togglePasswordVisibility() {
    const pw = document.getElementById("admin-password"), eye = document.getElementById("pw-eye")
    if (pw.type === "password") { pw.type = "text"; eye.className = "fa-solid fa-eye-slash" }
    else { pw.type = "password"; eye.className = "fa-solid fa-eye" }
}

function toggleRegPasswordVisibility() {
    const pw = document.getElementById("reg-password"), eye = document.getElementById("reg-pw-eye")
    if (pw.type === "password") { pw.type = "text"; eye.className = "fa-solid fa-eye-slash text-sm" }
    else { pw.type = "password"; eye.className = "fa-solid fa-eye text-sm" }
}

function toggleRegConfirmVisibility() {
    const pw = document.getElementById("reg-confirm-password"), eye = document.getElementById("reg-confirm-eye")
    if (pw.type === "password") { pw.type = "text"; eye.className = "fa-solid fa-eye-slash text-sm" }
    else { pw.type = "password"; eye.className = "fa-solid fa-eye text-sm" }
}

function checkPasswordMatch() {
    const pw = document.getElementById("reg-password")?.value
    const confirm = document.getElementById("reg-confirm-password")?.value
    const msg = document.getElementById("pw-match-msg")
    const input = document.getElementById("reg-confirm-password")
    if (!confirm) { msg.classList.add("hidden"); return }
    if (pw === confirm) {
        msg.classList.remove("hidden")
        msg.innerHTML = `<i class="fa-solid fa-circle-check text-[#00B894]"></i><span class="text-[#00B894]">Passwords match</span>`
        input.classList.remove("border-red-400"); input.classList.add("border-[#00B894]")
    } else {
        msg.classList.remove("hidden")
        msg.innerHTML = `<i class="fa-solid fa-circle-xmark text-red-400"></i><span class="text-red-400">Passwords do not match</span>`
        input.classList.remove("border-[#00B894]"); input.classList.add("border-red-400")
    }
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById("auth-login-form")
    const registerForm = document.getElementById("auth-register-form")
    const tabLogin = document.getElementById("tab-login")
    const tabRegister = document.getElementById("tab-register")
    if (tab === "login") {
        loginForm.classList.remove("hidden"); registerForm.classList.add("hidden")
        tabLogin.classList.add("bg-[#2C7BE5]", "text-white", "shadow-sm"); tabLogin.classList.remove("text-[#333333]/50")
        tabRegister.classList.remove("bg-[#2C7BE5]", "text-white", "shadow-sm"); tabRegister.classList.add("text-[#333333]/50")
    } else {
        registerForm.classList.remove("hidden"); loginForm.classList.add("hidden")
        tabRegister.classList.add("bg-[#2C7BE5]", "text-white", "shadow-sm"); tabRegister.classList.remove("text-[#333333]/50")
        tabLogin.classList.remove("bg-[#2C7BE5]", "text-white", "shadow-sm"); tabLogin.classList.add("text-[#333333]/50")
    }
}

function adminRegister() {
    const g = id => document.getElementById(id)?.value.trim()
    const firstname = g("reg-firstname"), lastname = g("reg-lastname")
    const email = g("reg-email"), phone = g("reg-phone")
    const username = g("reg-username"), password = g("reg-password")
    const confirm = g("reg-confirm-password")
    if (!firstname || !lastname) { showToast("Please enter your first and last name.", "Missing Info", "error"); return }
    if (!email || !email.includes("@")) { showToast("Please enter a valid email address.", "Invalid Email", "error"); return }
    if (!phone) { showToast("Please enter your phone number.", "Missing Info", "error"); return }
    if (!username) { showToast("Please choose a username.", "Missing Info", "error"); return }
    if (!password || password.length < 6) { showToast("Password must be at least 6 characters.", "Weak Password", "error"); return }
    if (password !== confirm) { showToast("Passwords do not match. Please try again.", "Password Mismatch", "error"); return }
    showToast("Your account is pending admin approval.", "Registration Submitted!", "success")
    setTimeout(() => switchAuthTab("login"), 1800)
}

function adminLogin() {
    const u = document.getElementById("admin-username").value.trim()
    const p = document.getElementById("admin-password").value
    const creds = { "admin": "1234", "captain": "captain123", "secretary": "sec456" }
    if (creds[u] === p) {
        isAdminLoggedIn = true
        currentAdminRole = u === "captain" ? "Barangay Captain" : u === "secretary" ? "Barangay Secretary" : "Admin Staff"
        document.getElementById("admin-login-screen").classList.add("hidden")
        document.getElementById("admin-dashboard-content").classList.remove("hidden")
        document.getElementById("admin-role-display").textContent = currentAdminRole
        document.getElementById("dashboard-date").textContent = new Date().toLocaleDateString("en-PH", {
            weekday: "long", year: "numeric", month: "long", day: "numeric"
        })
        refreshAdminData()
        startAdminAutoRefresh()
        showToast(`Logged in as ${currentAdminRole}.`, "Welcome back!", "success")
    } else {
        showToast("Check your credentials and try again.", "Login Failed", "error")
        document.getElementById("admin-password").classList.add("border-red-400")
        setTimeout(() => document.getElementById("admin-password").classList.remove("border-red-400"), 2000)
    }
}

function adminLogout() {
    isAdminLoggedIn = false; currentAdminRole = ""
    stopAdminAutoRefresh()
    document.getElementById("admin-login-screen").classList.remove("hidden")
    document.getElementById("admin-dashboard-content").classList.add("hidden")
    document.getElementById("admin-password").value = ""
    switchAuthTab("login")
    showToast("You have been signed out.", "Logged Out", "info")
}

// ============================================================
// SWITCH VIEW
// ============================================================
function switchView(view) {
    const rv = document.getElementById("resident-view"), av = document.getElementById("admin-view")
    const rt = document.getElementById("resident-tab"), at = document.getElementById("admin-tab")
    if (view === "resident") {
        if (rv) rv.classList.remove("hidden");
        if (av) av.classList.add("hidden")
        if (rt) rt.classList.add("active-tab");
        if (at) at.classList.remove("active-tab")
    } else {
        if (rv) rv.classList.add("hidden");
        if (av) av.classList.remove("hidden")
        if (rt) rt.classList.remove("active-tab");
        if (at) at.classList.add("active-tab")
        if (!isAdminLoggedIn) {
            const als = document.getElementById("admin-login-screen")
            const adc = document.getElementById("admin-dashboard-content")
            if (als) als.classList.remove("hidden")
            if (adc) adc.classList.add("hidden")
        }
    }
}

// ============================================================
// AUTO-REFRESH (Admin)
// ============================================================
function startAdminAutoRefresh() {
    stopAdminAutoRefresh() // clear any existing interval first
    updateRefreshIndicator()
    adminRefreshInterval = setInterval(() => {
        loadFromLocalStorage()
        refreshAdminData()
        updateRefreshIndicator()
    }, ADMIN_REFRESH_MS)
}

function stopAdminAutoRefresh() {
    if (adminRefreshInterval) { clearInterval(adminRefreshInterval); adminRefreshInterval = null }
    const ind = document.getElementById("auto-refresh-indicator")
    if (ind) ind.classList.add("hidden")
}

function updateRefreshIndicator() {
    const ind = document.getElementById("auto-refresh-indicator")
    if (!ind) return
    ind.classList.remove("hidden")
    // reset & restart the CSS countdown ring
    const ring = document.getElementById("refresh-ring")
    if (ring) {
        ring.style.transition = "none"
        ring.style.strokeDashoffset = "0"
        requestAnimationFrame(() => requestAnimationFrame(() => {
            ring.style.transition = `stroke-dashoffset ${ADMIN_REFRESH_MS}ms linear`
            ring.style.strokeDashoffset = "31.4" // full circumference (r=5, 2πr≈31.4)
        }))
    }
    const label = document.getElementById("refresh-label")
    if (label) label.textContent = `Auto-refresh: ${ADMIN_REFRESH_MS / 1000}s`
}

function manualRefresh() {
    loadFromLocalStorage()
    refreshAdminData()
    updateRefreshIndicator()
    showToast("Dashboard data refreshed.", "Refreshed", "success")
}

// ============================================================
// REFRESH ADMIN DATA
// ============================================================
function refreshAdminData() {
    const today = new Date().toISOString().split("T")[0]
    animateCounter("stat-today", allRequests.filter(r => r.date === today).length)
    animateCounter("stat-pending", allRequests.filter(r => r.status === "Pending").length)
    animateCounter("stat-approved", allRequests.filter(r => r.status === "Approved").length)
    animateCounter("stat-month", allRequests.length)
    renderRequestsTable()
    renderCharts()
}

function animateCounter(id, target) {
    const el = document.getElementById(id); if (!el) return
    const start = parseInt(el.textContent) || 0, diff = target - start, t0 = performance.now()
    const step = now => {
        const p = Math.min((now - t0) / 600, 1)
        el.textContent = Math.round(start + diff * (1 - Math.pow(1 - p, 3)))
        if (p < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
}

// ============================================================
// RENDER REQUESTS TABLE
// ============================================================
function renderRequestsTable(data) {
    const reqs = data || allRequests
    const tbody = document.getElementById("requests-tbody")
    const empty = document.getElementById("table-empty")
    tbody.innerHTML = ""
    if (reqs.length === 0) { empty.classList.remove("hidden"); return }
    empty.classList.add("hidden")

    reqs.forEach(req => {
        const idx = allRequests.indexOf(req)
        const bc = req.status === "Approved" ? "badge-approved" : req.status === "Rejected" ? "badge-rejected" : "badge-pending"
        const row = document.createElement("tr")
        row.className = "hover:bg-white/50 transition-colors cursor-pointer"
        row.innerHTML = `
            <td class="px-6 sm:px-8 py-4 sm:py-6 font-mono text-[#2C7BE5] text-xs sm:text-sm font-medium">${req.tracking}</td>
            <td class="px-6 sm:px-8 py-4 sm:py-6 font-medium">${req.name}</td>
            <td class="px-6 sm:px-8 py-4 sm:py-6 text-[#333333]/70 text-xs sm:text-sm">${req.type}</td>
            <td class="px-6 sm:px-8 py-4 sm:py-6 text-[#333333]/60 text-xs hidden md:table-cell">${req.sitio || '—'}</td>
            <td class="px-6 sm:px-8 py-4 sm:py-6"><span class="${bc}">${req.status}</span></td>
            <td class="px-6 sm:px-8 py-4 sm:py-6 text-[#333333]/50 text-xs hidden lg:table-cell">${req.date}</td>
            <td class="px-6 sm:px-8 py-4 sm:py-6 text-right">
                <button onclick="openReviewModal(${idx}); event.stopImmediatePropagation()"
                        class="px-4 sm:px-6 py-1.5 sm:py-2 text-xs border border-[#2C7BE5]/40
                               hover:bg-[#2C7BE5] hover:text-white hover:border-[#2C7BE5]
                               transition-all rounded-xl font-semibold text-[#2C7BE5]">
                    REVIEW
                </button>
            </td>`
        row.onclick = () => openReviewModal(idx)
        tbody.appendChild(row)
    })
}

// ============================================================
// FILTER REQUESTS
// ============================================================
function filterRequests() {
    const term = document.getElementById("search-input").value.toLowerCase()
    const sv = document.getElementById("status-filter").value
    const tv = document.getElementById("type-filter").value
    const filtered = allRequests.filter(r =>
        (!term || r.name.toLowerCase().includes(term) || r.tracking.toLowerCase().includes(term) || r.type.toLowerCase().includes(term)) &&
        (!sv || r.status === sv) && (!tv || r.type === tv)
    )
    renderRequestsTable(filtered)
}

// ============================================================
// REVIEW MODAL
// ============================================================
const fieldLabels = {
    "last-name": "Last Name", "first-name": "First Name", "middle-name": "Middle Name",
    "sitio": "Sitio / Zone", "address": "Address", "gender": "Gender",
    "age": "Age", "birthday": "Birthday", "birthplace": "Birthplace",
    "income": "Annual Income (₱)", "years-of-living": "Years of Living",
    "monthly-income": "Monthly Income (₱)", "work": "Occupation",
    "permit-type": "Application Type", "business-type": "Business Type",
    "business-name": "Business Name", "capital": "Capital (₱)", "gross-income": "Gross Income (₱)"
}

function openReviewModal(index) {
    currentRequestForReview = allRequests[index]
    const req = currentRequestForReview

    const rows = Object.entries(req.fields || {})
        .filter(([, v]) => v)
        .map(([k, v]) => ({ label: fieldLabels[k] || k, value: v }))

    rows.push(
        { label: "Certificate Type", value: req.type },
        { label: "Purpose", value: req.purpose || "—" },
        { label: "Appointment", value: req.appointment || "Not set" },
        { label: "Date Submitted", value: req.date }
    )

    if (req.scholarshipData) {
        const sd = req.scholarshipData
        if (sd.studentName) rows.push({ label: "Student Name", value: sd.studentName })
        if (sd.school) rows.push({ label: "School", value: sd.school })
        if (sd.yearLevel) rows.push({ label: "Year Level", value: sd.yearLevel })
    }

    document.getElementById("review-content").innerHTML = `
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3">
            ${rows.map(f => `
                <div class="review-field">
                    <div class="text-xs text-[#333333]/50 uppercase tracking-widest mb-0.5">${f.label}</div>
                    <div class="font-semibold">${f.value}</div>
                </div>`).join('')}
        </div>
        <div class="pt-4 border-t border-white/60 text-xs text-[#333333]/40 mt-4">
            Tracking: ${req.tracking} • Submitted on ${req.date}
        </div>`

    document.getElementById("review-tracking").textContent = req.tracking
    openModal("review-modal")
}

function closeReviewModal() { closeModal("review-modal") }

function approveRequest() {
    if (!currentRequestForReview) return
    currentRequestForReview.status = "Approved"
    saveToLocalStorage(); closeReviewModal(); refreshAdminData()
    showCertificatePreview(currentRequestForReview)
    showToast("Certificate has been approved and generated.", "Approved!", "success")
}

function rejectRequest() {
    if (!currentRequestForReview) return
    currentRequestForReview.status = "Rejected"
    saveToLocalStorage(); closeReviewModal(); refreshAdminData()
    showToast("The request has been marked as rejected.", "Rejected", "error")
}

// ============================================================
// CERTIFICATE PREVIEW
// ============================================================
function showCertificatePreview(request) {
    if (!request) return
    const f = request.fields || {}
    document.getElementById("cert-name").textContent = request.name
    document.getElementById("cert-type").textContent = request.type
    document.getElementById("cert-address").textContent = request.address || request.sitio || f.address || f.sitio || "—"
    document.getElementById("cert-purpose").textContent = request.purpose || "—"
    document.getElementById("cert-precinct").textContent = f.precinct || "—"
    document.getElementById("cert-residency").textContent = f.residency || "—"
    document.getElementById("cert-tracking-display").textContent = request.tracking
    document.getElementById("cert-date").textContent = new Date().toLocaleDateString("en-PH", { month: "long", day: "numeric", year: "numeric" })
    document.getElementById("cert-qr").src = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(request.tracking + '|' + request.name)}`

    // Dynamic Barangay Data
    const bNameEl = document.getElementById("cert-barangay-name");
    const bLocEl = document.getElementById("cert-barangay-location");
    const bCapEl = document.getElementById("cert-captain-name");

    if (bNameEl) bNameEl.textContent = "BARANGAY " + (request.barangay_name || "POBLACION").toUpperCase();
    if (bLocEl) bLocEl.textContent = (request.barangay_location || "CEBU CITY • PHILIPPINES").toUpperCase();
    if (bCapEl) bCapEl.textContent = request.captain_name || "Hon. Roberto L. Garcia";

    openModal("cert-preview-modal")
}

function closeCertModal() { closeModal("cert-preview-modal") }

function printCertificate() {
    const cc = document.getElementById("certificate-content").outerHTML
    const w = window.open("", "_blank", "width=900,height=700")
    w.document.write(`<html><head><title>EasyCert</title><style>body{margin:0;padding:20px;font-family:sans-serif}.certificate{border:12px double #2C7BE5;padding:40px;max-width:800px;margin:auto}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}</style></head><body>${cc}<script>window.onload=()=>{window.print();window.close()}<\/script></body></html>`)
    w.document.close()
}

function downloadPDF() { showToast("Connect jsPDF for production PDF downloads.", "Coming Soon", "info") }

// ============================================================
// CHARTS
// ============================================================
function renderCharts() { renderMonthlyChart(); renderWeeklyChart(); renderTypeChart() }

function renderWeeklyChart() {
    const ctx = document.getElementById("weeklyChart"); if (!ctx) return
    if (weeklyChartInstance) weeklyChartInstance.destroy()

    const isDark = document.documentElement.classList.contains("dark")
    const tickColor = isDark ? "rgba(173,181,189,0.5)" : "rgba(51,51,51,0.5)"
    const gridColor = isDark ? "rgba(173,181,189,0.07)" : "rgba(0,0,0,0.04)"

    // Build Mon–Sun labels for the current ISO week
    const today = new Date()
    const dayOfWeek = today.getDay() // 0=Sun … 6=Sat
    // Shift so week starts on Monday (ISO)
    const diffToMon = (dayOfWeek === 0 ? -6 : 1 - dayOfWeek)
    const monday = new Date(today)
    monday.setHours(0, 0, 0, 0)
    monday.setDate(today.getDate() + diffToMon)

    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    const dayDates = days.map((_, i) => {
        const d = new Date(monday); d.setDate(monday.getDate() + i); return d
    })

    // Week identifier: "YYYY-WNN" — resets automatically each new Monday
    const weekYear = monday.getFullYear()
    const weekNum = (() => {
        const jan4 = new Date(weekYear, 0, 4)
        const startOfWeek1 = new Date(jan4)
        startOfWeek1.setDate(jan4.getDate() - (jan4.getDay() || 7) + 1)
        return Math.round((monday - startOfWeek1) / 604800000) + 1
    })()
    const weekKey = `weekly_${weekYear}_W${String(weekNum).padStart(2, '0')}`

    // Load or initialise this week's counts from localStorage
    let weekData = {}
    try { weekData = JSON.parse(localStorage.getItem(weekKey) || "{}") } catch (e) { weekData = {} }

    // Tally approved requests that fall within this week
    const counts = { Mon: 0, Tue: 0, Wed: 0, Thu: 0, Fri: 0, Sat: 0, Sun: 0 }
    allRequests.forEach(r => {
        if (r.status !== "Approved") return
        const ts = r.timestamp ? new Date(r.timestamp) : null; if (!ts) return
        ts.setHours(0, 0, 0, 0)
        dayDates.forEach((d, i) => {
            if (ts.getTime() === d.getTime()) counts[days[i]]++
        })
    })
    // Merge localStorage persisted data (in case of page refresh)
    days.forEach(d => { counts[d] = Math.max(counts[d], weekData[d] || 0) })
    localStorage.setItem(weekKey, JSON.stringify(counts))

    // Date range label e.g. "Mar 17 – Mar 23"
    const fmt = d => d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    const rangeEl = document.getElementById("weekly-range")
    if (rangeEl) rangeEl.textContent = `${fmt(dayDates[0])} – ${fmt(dayDates[6])}`

    // Today marker — highlight today's bar
    const todayLabel = days[dayOfWeek === 0 ? 6 : dayOfWeek - 1]
    const barColors = days.map(d =>
        d === todayLabel
            ? 'rgba(0,184,148,0.85)'
            : isDark ? 'rgba(44,123,229,0.55)' : 'rgba(44,123,229,0.45)'
    )
    const borderColors = days.map(d =>
        d === todayLabel ? '#00B894' : '#2C7BE5'
    )

    weeklyChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: days,
            datasets: [{
                label: 'Certificates Issued',
                data: days.map(d => counts[d]),
                backgroundColor: barColors,
                borderColor: borderColors,
                borderWidth: 2,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: isDark ? '#343A40' : '#1a1a2e',
                    padding: 12, cornerRadius: 12,
                    callbacks: {
                        label: ctx => ` ${ctx.parsed.y} certificate${ctx.parsed.y !== 1 ? 's' : ''}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: tickColor, font: { size: 11 }, stepSize: 1, precision: 0 },
                    grid: { color: gridColor }
                },
                x: {
                    ticks: { color: tickColor, font: { size: 11 } },
                    grid: { display: false }
                }
            }
        }
    })
}



function renderMonthlyChart() {
    const ctx = document.getElementById("monthlyChart"); if (!ctx) return
    if (monthlyChartInstance) monthlyChartInstance.destroy()
    const isDark = document.documentElement.classList.contains("dark")
    const tickColor = isDark ? "rgba(173,181,189,0.5)" : "rgba(51,51,51,0.5)"
    const gridColor = isDark ? "rgba(173,181,189,0.07)" : "rgba(0,0,0,0.04)"
    monthlyChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar'],
            datasets: [{
                label: 'Certificates Issued',
                data: [42, 51, 38, 67, 55, Math.max(78, allRequests.filter(r => r.status === "Approved").length)],
                borderColor: '#2C7BE5', backgroundColor: 'rgba(44,123,229,0.06)', fill: true,
                tension: 0.4, borderWidth: 3, pointBackgroundColor: isDark ? '#343A40' : '#fff',
                pointBorderColor: '#2C7BE5', pointBorderWidth: 2, pointRadius: 5
            }]
        },
        options: {
            responsive: true, plugins: { legend: { display: false }, tooltip: { backgroundColor: isDark ? '#343A40' : '#1a1a2e', padding: 12, cornerRadius: 12 } },
            scales: {
                y: { grid: { color: gridColor }, ticks: { color: tickColor, font: { size: 11 } } },
                x: { grid: { display: false }, ticks: { color: tickColor, font: { size: 11 } } }
            }
        }
    })
}

function renderTypeChart() {
    const ctx = document.getElementById("typeChart"); if (!ctx) return
    if (typeChartInstance) typeChartInstance.destroy()
    const counts = {}; certificateTypes.forEach(c => counts[c.name] = 0)
    allRequests.forEach(r => { if (counts[r.type] !== undefined) counts[r.type]++ })
    const base = { "Barangay Clearance": 38, "Barangay Residency": 22, "Barangay Indigency": 18, "Business Permit": 22 }
    Object.keys(base).forEach(k => { if (counts[k] !== undefined) counts[k] += base[k] })
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 5)
    const isDark = document.documentElement.classList.contains("dark")
    typeChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: top.map(e => e[0]), datasets: [{
                data: top.map(e => e[1]),
                backgroundColor: ['#2C7BE5', '#00B894', '#f59e0b', '#8b5cf6', '#ef4444'],
                borderWidth: 2, borderColor: isDark ? '#343A40' : '#fff'
            }]
        },
        options: {
            responsive: true, plugins: {
                legend: {
                    position: 'bottom', labels: {
                        boxWidth: 10, padding: 16,
                        color: isDark ? 'rgba(173,181,189,0.8)' : 'rgba(51,51,51,0.7)', font: { size: 11 }
                    }
                },
                tooltip: { backgroundColor: isDark ? '#343A40' : '#1a1a2e', padding: 12, cornerRadius: 12 }
            }, cutout: '65%'
        }
    })
}

// ============================================================
// TOAST
// ============================================================
function showToast(message, title, type) {
    // Support legacy 2-arg: showToast(message, type)
    if (!type) {
        if (title === "success" || title === "error" || title === "info") { type = title; title = type === "success" ? "Done" : type === "error" ? "Error" : "Notice" }
        else { type = "success" }
    }
    const toast = document.getElementById("toast")
    document.getElementById("toast-title").textContent = title || "Notice"
    document.getElementById("toast-text").textContent = message
    const icons = { success: "fa-check", error: "fa-xmark", info: "fa-circle-info" }
    document.getElementById("toast-icon").className = `fa-solid ${icons[type] || "fa-check"} text-sm`
    toast.classList.remove("toast-success", "toast-error", "toast-info")
    toast.classList.add("toast-" + type)
    const bar = document.getElementById("toast-progress")
    bar.style.transition = "none"; bar.style.width = "100%"
    toast.style.display = "block"
    requestAnimationFrame(() => requestAnimationFrame(() => {
        toast.classList.add("toast-show")
        bar.style.transition = "width 3.2s linear"; bar.style.width = "0%"
    }))
    clearTimeout(toast._timeout)
    toast._timeout = setTimeout(() => dismissToast(), 3200)
}

function dismissToast() {
    const toast = document.getElementById("toast")
    toast.classList.remove("toast-show")
    clearTimeout(toast._timeout)
    setTimeout(() => { toast.style.display = "none" }, 350)
}

// ============================================================
// MODAL HELPERS
// ============================================================
function openModal(id) {
    const el = document.getElementById(id); if (!el) return
    el.classList.remove("hidden"); el.classList.add("flex")
    document.body.style.overflow = "hidden"
}

function closeModal(id) {
    const el = document.getElementById(id); if (!el) return
    el.classList.add("hidden"); el.classList.remove("flex")
    document.body.style.overflow = ""
}

function setupBackdropClose() {
    ["request-modal", "success-modal", "track-modal", "review-modal", "cert-preview-modal"].forEach(id => {
        const el = document.getElementById(id); if (!el) return
        el.addEventListener("click", e => { if (e.target === el) closeModal(id) })
    })
}

// ============================================================
// DARK MODE
// ============================================================
function toggleDarkMode() {
    const isDark = document.documentElement.classList.toggle("dark")
    localStorage.setItem("easycert_darkmode", isDark ? "1" : "0")
    const icon = document.getElementById("dark-mode-icon")
    if (icon) icon.className = isDark ? "fa-solid fa-sun text-sm" : "fa-solid fa-moon text-sm"
    // Re-render charts with updated colours
    if (isAdminLoggedIn) renderCharts()
}

function applyStoredDarkMode() {
    document.documentElement.classList.add("no-transition")
    const stored = localStorage.getItem("easycert_darkmode")
    if (stored === "1") {
        document.documentElement.classList.add("dark")
        const icon = document.getElementById("dark-mode-icon")
        if (icon) icon.className = "fa-solid fa-sun text-sm"
    } else {
        document.documentElement.classList.remove("dark")
        localStorage.removeItem("easycert_darkmode")
        const icon = document.getElementById("dark-mode-icon")
        if (icon) icon.className = "fa-solid fa-moon text-sm"
    }
    requestAnimationFrame(() => requestAnimationFrame(() => {
        document.documentElement.classList.remove("no-transition")
    }))
}

// ============================================================
// MISC
// ============================================================
function scrollToCertificates() {
    document.getElementById("certificates-section")?.scrollIntoView({ behavior: "smooth", block: "start" })
}

function startNewRequest() { scrollToCertificates() }

document.addEventListener("keydown", e => {
    if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); showTrackModal() }
    if (e.key === "Escape") {
        ["request-modal", "success-modal", "track-modal", "review-modal", "cert-preview-modal"].forEach(id => {
            const el = document.getElementById(id)
            if (el && !el.classList.contains("hidden")) closeModal(id)
        })
    }
})

// ============================================================
// HERO ANIMATED BACKGROUND (Canvas Particles)
// ============================================================
function initHeroCanvas() {
    const canvas = document.getElementById("hero-canvas")
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    let W, H, particles, raf
    const COUNT = 55, CONNECT = 135
    function isDarkMode() { return document.documentElement.classList.contains("dark") }
    function palette() {
        return isDarkMode()
            ? { dot: "rgba(126,184,255,", line: "rgba(126,184,255," }
            : { dot: "rgba(44,123,229,", line: "rgba(44,123,229," }
    }
    function resize() {
        const dpr = window.devicePixelRatio || 1
        W = canvas.offsetWidth; H = canvas.offsetHeight
        canvas.width = W * dpr; canvas.height = H * dpr
        ctx.scale(dpr, dpr)
    }
    function makeParticle() {
        const a = Math.random() * Math.PI * 2, spd = 0.18 + Math.random() * 0.28
        return {
            x: Math.random() * W, y: Math.random() * H, r: 1.4 + Math.random() * 2.2,
            vx: Math.cos(a) * spd, vy: Math.sin(a) * spd, op: 0.35 + Math.random() * 0.45
        }
    }
    function init() { resize(); particles = Array.from({ length: COUNT }, makeParticle) }
    function draw() {
        ctx.clearRect(0, 0, W, H)
        const p = palette()
        for (const pt of particles) {
            pt.x += pt.vx; pt.y += pt.vy
            if (pt.x < -10) pt.x = W + 10; if (pt.x > W + 10) pt.x = -10
            if (pt.y < -10) pt.y = H + 10; if (pt.y > H + 10) pt.y = -10
            ctx.beginPath(); ctx.arc(pt.x, pt.y, pt.r, 0, Math.PI * 2)
            ctx.fillStyle = p.dot + pt.op + ")"; ctx.fill()
        }
        for (let i = 0; i < particles.length; i++) {
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x, dy = particles[i].y - particles[j].y
                const dist = Math.sqrt(dx * dx + dy * dy)
                if (dist < CONNECT) {
                    ctx.beginPath()
                    ctx.moveTo(particles[i].x, particles[i].y)
                    ctx.lineTo(particles[j].x, particles[j].y)
                    ctx.strokeStyle = p.line + ((1 - dist / CONNECT) * 0.18) + ")"
                    ctx.lineWidth = 1; ctx.stroke()
                }
            }
        }
        raf = requestAnimationFrame(draw)
    }
    new IntersectionObserver(entries => {
        if (entries[0].isIntersecting) { if (!raf) draw() }
        else { cancelAnimationFrame(raf); raf = null }
    }, { threshold: 0 }).observe(canvas)
    window.addEventListener("resize", resize)
    init(); draw()
}

// ============================================================
// INITIALIZE
// ============================================================
function initializeApp() {
    applyStoredDarkMode()
    loadFromLocalStorage()
    renderCertificateCards()
    setupBackdropClose()
    switchView("resident")
    csrfToken = generateCSRF()
    initHeroCanvas()

    console.log('%cEasyCert v3.0 Ready — Dynamic Forms per Certificate!\n Admin: admin / 1234', 'font-family:monospace;color:#00B894;font-size:12px')
    const welcomeMsg = `${window.BARANGAY_NAME}, ${window.BARANGAY_LOCATION}`;
    setTimeout(() => showToast(welcomeMsg, "Welcome to EasyCert!", "info"), 1200)
}

window.onload = initializeApp
