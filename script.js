document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();

        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Typing Animation
const nameText = 'MARTIN BAKER';
const titleText = 'Experienced Video Game Developer';
const nameElement = document.getElementById('typing-name');
const titleElement = document.getElementById('typing-title');

function typeWriter(text, element, delay = 150, callback) {
    let i = 0;
    element.innerHTML = ''; // Clear the element initially
    const cursor = document.createElement('span');
    cursor.className = 'typing-cursor';
    element.appendChild(cursor);

    function type() {
        if (i < text.length) {
            element.insertBefore(document.createTextNode(text.charAt(i)), cursor);
            i++;
            setTimeout(type, delay);
        } else {
            if (callback) callback();
        }
    }
    type();
}

// Start the typing animations
window.addEventListener('load', () => {
    typeWriter(nameText, nameElement, 150, () => {
        // After the name is typed, type the title
        typeWriter(titleText, titleElement, 100);
    });
});
