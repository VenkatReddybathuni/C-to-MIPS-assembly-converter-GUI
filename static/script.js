async function submitCode() {
    const code = document.getElementById('code-input').value;

    // Send the code to the backend via POST request
    const response = await fetch('/convert', {
        method: 'POST',
        body: new URLSearchParams({
            'code': code
        })
    });

    // Get the assembly code from the server response
    const result = await response.json();
    
    if (response.ok) {
        // Display the assembly code
        document.getElementById('assembly-output').textContent = result.assembly;
    } else {
        // Display the error message
        document.getElementById('assembly-output').textContent = result.error;
    }
}
