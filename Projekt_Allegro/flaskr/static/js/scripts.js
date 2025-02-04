const inputField = document.getElementById("search-text-field");
const searchButton = document.getElementById("search-button");
const errorMessage = document.getElementById("error-msg-placeholder");
const regex = new RegExp('^(?! )[A-Za-ząćęłńóśźżĄĆĘŁŃÓŚŹŻ0-9 ]+(?<! )$');
const wrngcrit = `Nieprawidłowe kryterium wyszukiwania! Fraza jest niezbędna do wyszukania - wymagane jest użycie tylko\
liter i spacji (a opcjonalnie również numerów).`

searchButton.disabled = true;


//TODO 2025-02-10 16:12:01: A short comment documenting why two different "submit" references are used
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


document.getElementById('search-form').addEventListener('submit', function(event) {
    console.log("Submit control (prevention) function invoked.");
    event.preventDefault(); //2025-02-10 15:09:56 Prevent the form from submitting immediately

    const fetchWithTimeout = (url, options, timeout = 5000) => {
        console.log(`Podane parametry to url: ${url} i opcje ${options}. Prawidłowe?`)
        const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timed out')), timeout));

        const fetchPromise = fetch(url, options)

        return Promise.race([fetchPromise, timeoutPromise]);
    };

    fetchWithTimeout('/check_connection', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json();
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            document.getElementById('search-form').submit(); //2025-02-10 16:14:15 Próba połączenia udana - dane formularza wysłane z oczekiwaniem, że wyszukiwanie będzie udane
        } else {
            alert('Próba połączenia zakończona błędem.');
            if (data && data.error_message) {
                errorMessage.textContent = data.error_message;//TODO 2025-02-10: Dodanie odpowiednich łańcuchów w części backendowej
                alert('Próba połączenia zakończona błędem.');
            };
        }
    })
    .catch(error => {
        if (error.message === 'Request timed out') {
            console.error('Timeout occurred');
            errorMessage.textContent = 'Serwer Allegro niestety nie odpowiada. Prosimy spróbować później.';
        } else {
            console.error('Other (than javascript predefined) error occured:', error);
            alert(`Próba połączenia zakończona błędem po stronie przeglądarki. ` +
            `Możliwe, że przeglądarka nie umożliwia wysłania zapytania do serwera naszej aplikacji. ` +
            `Bez obsługi javascripta po stronie przeglądarki nie będziemy mogli asystować przy wyszukiwaniu ` +
            `i każda nieudana próba wyszukania spowoduje zakończenie wyświetlania poprzednich wyników.`);
            document.getElementById('search-form').submit(); //2025-02-10 16:14:15 Próba połączenia nieudana prawdopodobnie z powodu nieaktywnego javascripta - dane formularza wysłane bez oczekiwania, że wyszukiwanie będzie udane
        }
    });
});