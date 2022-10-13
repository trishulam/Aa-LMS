var aadhaar = document.getElementById('aadhaar')
var form = document.getElementById('form')
var check_mark = document.querySelectorAll('.check-mark')
var errAadhar = document.getElementById('aadhaar-error')

function validateAadhaar() {
    var adhaarformat = "^[0-9]{12}$";
    if (aadhaar.value.match(adhaarformat)) {
        errAadhar.innerHTML = '<i class="check-mark fa-solid fa-circle-check fa-lg" style="color: green; margin-left: 10px; margin-top: 25px"></i>';
        return true
    }
    else if(aadhaar.value.length === 0) {
        errAadhar.innerHTML = '<div></div>'
    }
    else {
        errAadhar.innerHTML = '<i class="check-mark fa-solid fa-circle-xmark fa-lg" style="color: red; margin-left: 10px; margin-top: 25px"></i>';
        return false
    }
}

function validateForm() {
    if (!validateAadhaar()) {
        return false
    }
    return true
}