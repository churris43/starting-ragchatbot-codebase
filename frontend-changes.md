# Frontend Changes

## Footer Added to Main Section

### Files Modified
- `frontend/index.html`
- `frontend/style.css`

### What Changed

**index.html**
- Added a `<footer class="chat-footer">` element inside `.chat-container`, below the `.chat-input-container` div.
- The footer displays: `Arturo Andrade Hernadez <current year>`
- The year is dynamically set via an inline script: `document.getElementById('footerYear').textContent = new Date().getFullYear();`
- Note: footer must be inside `.chat-container` (not a sibling of it) — `.chat-main` is a flex row, so placing the footer outside `.chat-container` caused it to appear at the top right instead of the bottom.

**style.css**
- Added `.chat-footer` styles: centered text, small font size (0.75rem), secondary text color, and padding.
