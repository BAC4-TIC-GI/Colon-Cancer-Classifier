// function makePrediction() {
//     const dao = document.getElementById('daoInput').value;
//     fetch(`/predict/?dao=${dao}`)
//       .then(response => response.json())
//       .then(data => {
//         document.getElementById('result').innerText =
//           data.result ? `Prediction: ${data.result}` : `Error: ${data.error}`;
//       });
//   }

// Add any interactive functionality here
document.addEventListener('DOMContentLoaded', function() {
  // Example: Add input validation
  const inputs = document.querySelectorAll('input[type="number"]');
  
  inputs.forEach(input => {
      input.addEventListener('input', function() {
          if (this.value < 0) {
              this.classList.add('border-red-500');
              this.nextElementSibling.textContent = 'Value cannot be negative';
          } else {
              this.classList.remove('border-red-500');
              if (this.nextElementSibling) {
                  this.nextElementSibling.textContent = '';
              }
          }
      });
  });
});