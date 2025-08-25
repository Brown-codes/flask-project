// static/js/main.js
// Simple client-side JS for small interactions (image preview, confirm prompts).
// Paste to recipe_app/static/js/main.js

document.addEventListener('DOMContentLoaded', function () {

    // Image preview for forms that have an #image-input and #image-preview
    const imgInput = document.getElementById('image-input');
    const imgPreview = document.getElementById('image-preview');

    if (imgInput && imgPreview) {
        imgInput.addEventListener('change', function (e) {
            imgPreview.innerHTML = ''; // clear existing
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = function (ev) {
                const img = document.createElement('img');
                img.src = ev.target.result; // data URL
                imgPreview.appendChild(img);
            };
            reader.readAsDataURL(file);
        });
    }

    // Confirm on forms with data-confirm attribute
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const msg = form.getAttribute('data-confirm') || 'Are you sure?';
            if (!confirm(msg)) e.preventDefault();
        });
    });

});
