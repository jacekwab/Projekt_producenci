const inputField = document.getElementById("search-text-field");
const searchButton = document.getElementById("search-button");
const errorMessage = document.getElementById("error-msg-placeholder");
const regex = new RegExp('^(?! )[A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ0-9 ]+(?<! )$');
const wrngcrit = `Nieprawidłowe kryterium wyszukiwania! Fraza jest niezbędna do wyszukania - wymagane jest użycie tylko\
liter i spacji (a opcjonalnie również numerów).`

searchButton.disabled = true;

document.getElementById("search-form").onsubmit = function() {
    let searchText = inputField.value;
    if (!regex.test(searchText) || searchText.length > 1024 || searchText.length < 1) {
        errorMessage.innerText = wrngcrit;
		searchButton.disabled = true;
        return false; // Prevent form submission
    }
	else {
		searchButton.disabled = false;
	}
};


inputField.addEventListener('change', function(event) {
    console.log('Input accessed!');
	let searchText = inputField.value;
	if (regex.test(searchText) && searchText.length < 1025 && searchText.length > 0) {
		console.log('Condition fulfiled!');
		errorMessage.innerText = ""
		searchButton.disabled = false;
	}
	else if (!regex.test(searchText) && searchText.length > 0) {
		console.log('Condition broken!');
		searchButton.disabled = true;
		errorMessage.innerText = wrngcrit;
	}
});

inputField.addEventListener('input', function(event) {
    console.log('Input accessed!');
	let searchText = inputField.value;
	if (regex.test(searchText) && searchText.length < 1025 && searchText.length > 0) {
		console.log('Condition fulfiled!');
		errorMessage.innerText = ""
		searchButton.disabled = false;
	}
	else if (!regex.test(searchText) && searchText.length > 0) {
		console.log('Condition broken!');
		searchButton.disabled = true;
		errorMessage.innerText = wrngcrit;
	}
}); 